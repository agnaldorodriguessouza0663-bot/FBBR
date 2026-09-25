# -*- coding: utf-8 -*-
"""Encenação em estilo anime — "Direito Penal em Anime, Episódio 148: A Porta Trancada".

Uso: python3 episodio.py --voice pt-br-edresson-low.onnx [--out episodio148_anime.mp4] [--preview]
"""
import argparse
import math
import os
import random
import subprocess
import sys
import tempfile
import wave
from functools import lru_cache

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "animacao"))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
import cenarios as cen  # noqa: E402
from animacao import bg, camera, clamp, ease, fade_in, lerp  # noqa: E402
from anime_chars import bust, full, paste_full  # noqa: E402
from gerar_video import draw_rich, font, rich_height  # noqa: E402

W, H, FPS, SR = 1920, 1080, 30, 22050
JP = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"


def jfont(size):
    for p in (JP, "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/ipafont/ipag.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return font("sans_b", size)


def tq(t):
    """Tempo quantizado em 12 qps (animação "em dois/três", típica de anime)."""
    return round(t * 12) / 12


# ---------------------------------------------------------------- fundos anime
@lru_cache(maxsize=16)
def abg(name):
    b = bg(name)
    b = ImageEnhance.Color(b).enhance(1.35)
    b = ImageEnhance.Contrast(b).enhance(1.05)
    return b.filter(ImageFilter.GaussianBlur(2.2))


def focus_bg(c1, c2, t, lines=True, seed=0, cx=W / 2, cy=H / 2):
    g = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(c1, np.float32) * (1 - g) + np.array(c2, np.float32) * g
    img = Image.fromarray(np.repeat(arr, W, axis=1).astype(np.uint8)).convert("RGBA")
    if lines:
        speed_lines(img, t, cx, cy, color=(255, 255, 255), seed=seed, alpha=90)
    return img


def speed_lines(img, t, cx, cy, color=(255, 255, 255), n=110, seed=0, alpha=150, inner=380):
    rnd = random.Random(seed * 1000 + int(t * 12))
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(n):
        a = rnd.random() * 2 * math.pi
        r0 = inner + rnd.random() * 260
        wdt = rnd.random() * 0.012 + 0.003
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        p1 = (cx + math.cos(a - wdt) * 1500, cy + math.sin(a - wdt) * 1500)
        p2 = (cx + math.cos(a + wdt) * 1500, cy + math.sin(a + wdt) * 1500)
        d.polygon([p0, p1, p2], fill=color + (alpha,))
    img.alpha_composite(ov)


def bokeh(img, t, seed=1, color=(255, 230, 170)):
    rnd = random.Random(seed)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(26):
        x = (rnd.random() * W + t * 20 * (rnd.random() - 0.5)) % W
        y = rnd.random() * H
        r = 20 + rnd.random() * 60
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (int(40 + rnd.random() * 50),))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(6)))


def petals(img, t, seed=3, n=40, color=(250, 206, 40)):
    """Flores de ipê-amarelo caindo (o "sakura" brasileiro)."""
    rnd = random.Random(seed)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(n):
        x0, sp, ph = rnd.random() * W, 60 + rnd.random() * 80, rnd.random() * 10
        y = (rnd.random() * H + t * sp) % (H + 40) - 20
        x = x0 + 40 * math.sin(t * 1.3 + ph)
        r = 8 + rnd.random() * 6
        ang = t * 2 + ph
        d.ellipse([x - r, y - r * (0.5 + 0.4 * math.sin(ang)), x + r, y + r * (0.5 + 0.4 * math.sin(ang))], fill=color + (230,))
    img.alpha_composite(ov)


def sparkles(img, t, cx, cy, spread=500, seed=4):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(18):
        x = cx + (rnd.random() - 0.5) * spread * 2
        y = cy + (rnd.random() - 0.5) * spread
        s = 10 + 14 * abs(math.sin(t * 3 + rnd.random() * 6))
        d.polygon([(x, y - s), (x + s * 0.25, y - s * 0.25), (x + s, y), (x + s * 0.25, y + s * 0.25), (x, y + s),
                   (x - s * 0.25, y + s * 0.25), (x - s, y), (x - s * 0.25, y - s * 0.25)], fill=(255, 250, 220, 230))


def sfx(img, text, x, y, size, angle=0, alpha=1.0, color=(255, 220, 60), stroke=(30, 20, 30)):
    """Onomatopeia estilo mangá: letras grossas com contorno e leve rotação."""
    if alpha <= 0:
        return
    pop = 1 + 0.5 * (1 - ease(alpha * 1.5))
    f = font("sans_b", int(size * pop))
    tw = int(f.getlength(text)) + 60
    th = int(size * pop * 1.5)
    lay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((30, 10), text, font=f, fill=color + (int(255 * min(1, alpha * 2)),),
                             stroke_width=max(4, size // 12), stroke_fill=stroke + (int(255 * min(1, alpha * 2)),))
    lay = lay.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int(x - lay.size[0] / 2), int(y - lay.size[1] / 2)))


def status_window(img, title, lines, shown, x, y, w, alpha=1.0, color=(90, 220, 255)):
    """Janela de "status" estilo game/anime com o texto legal."""
    if alpha <= 0:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    size = 32
    hs = [max(46, rich_height(li, size, w - 90)) for li in lines]
    h = 90 + sum(hs) + 14 * len(lines) + 20
    a = int(235 * alpha)
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(10, 24, 48, int(a * 0.88)), outline=color + (a,), width=4)
    d.rectangle([x + 4, y + 4, x + w - 4, y + 66], fill=color + (int(a * 0.25),))
    d.text((x + 30, y + 12), title, font=font("sans_b", 36), fill=(255, 255, 255, a))
    yy = y + 86
    for k, li in enumerate(lines):
        if k < shown:
            d.polygon([(x + 30, yy + 10), (x + 46, yy + 20), (x + 30, yy + 30)], fill=color + (a,))
            draw_rich(d, (x + 60, yy), li, size, w - 90, color=(236, 240, 250), hlcolor=(255, 214, 90))
        yy += hs[k] + 14
    img.alpha_composite(ov)


def stamp(img, text, alpha, color=(235, 60, 70), y=150):
    if alpha <= 0:
        return
    sfx(img, text, W / 2, y + 60, 84, angle=4, alpha=alpha, color=color, stroke=(255, 255, 255))


# ---------------------------------------------------------------- legendas estilo fansub
SPEAKER = {"A": ("ANA", (255, 190, 90)), "AI": ("ANA (pensando)", (255, 190, 90)), "C": ("CARLOS", (200, 200, 210)),
           "B": ("BRUNO", (140, 200, 255)), "P": ("POLICIAL", (120, 170, 255)), "N": ("NARRADOR", (255, 230, 150))}


def subtitle(img, spk, text):
    name, col = SPEAKER[spk]
    d = ImageDraw.Draw(img)
    f = font("sans_b", 38)
    fn = font("sans_b", 28)
    lines, cur = [], ""
    for w in text.split():
        if f.getlength(cur + " " + w) > 1500 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    lines = lines[-2:] if len(lines) > 2 else lines
    y = H - 60 - 52 * len(lines)
    d.text((W / 2 - fn.getlength(name) / 2, y - 40), name, font=fn, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    for li in lines:
        txt = f"({li})" if spk == "AI" else li
        d.text((W / 2 - f.getlength(txt) / 2, y), txt, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
        y += 52


def chunk_line(text, maxc=110):
    """Divide falas longas em blocos de legenda."""
    parts, cur = [], ""
    for w in text.split():
        cur = (cur + " " + w).strip()
        if len(cur) > maxc * 0.6 and cur.endswith((".", "?", "!", ":", ";", ",")) or len(cur) > maxc:
            parts.append(cur)
            cur = ""
    if cur:
        parts.append(cur)
    return parts


# ---------------------------------------------------------------- utilidades de cena
class Ctx:
    def __init__(self, t, T, lines):
        self.t, self.T, self.lines = t, T, lines  # lines: [(spk, t0, t1)]

    def talking(self, spk):
        return any(s == spk and a <= self.t <= b for s, a, b in self.lines)

    def st(self, i):
        return self.lines[i][1] if i < len(self.lines) else self.T


def put_bust(img, name, size, x, y, c, expr="neutral", look=0.0, fx=(), spk=None, prop=None):
    b = bust(name, size, expr, tq(c.t), c.talking(spk) if spk else False, look, tuple(fx), prop)
    img.alpha_composite(b, (int(x - b.size[0] / 2), int(y)))


def put_full(world, name, h, x, y, c, walk=None, arms=("down", "down"), expr="neutral", look=0.0, fx=(), spk=None):
    t = tq(c.t)
    f = full(name, h, t, None if walk is None else round(walk * 4) / 4, arms, expr,
             c.talking(spk) if spk else False, look, tuple(fx))
    paste_full(world, f, x, y)


def phone_ui(img, x, y, t, mode):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = 400, 720
    d.rounded_rectangle([x, y, x + w, y + h], radius=50, fill=(18, 18, 22, 255), outline=(34, 24, 30, 255), width=6)
    d.rounded_rectangle([x + 16, y + 16, x + w - 16, y + h - 16], radius=38, fill=(236, 240, 244, 255))
    f, fb, fs = font("sans", 28), font("sans_b", 32), font("sans", 22)
    if mode == "chat":
        d.rectangle([x + 16, y + 60, x + w - 16, y + 140], fill=(255, 150, 60, 255))
        d.text((x + 40, y + 80), "Ana", font=fb, fill=(255, 255, 255, 255))
        for k, (m, hr) in enumerate([("Chegou bem?", "19:40"), ("Ana?", "21:05"), ("Me responde!", "22:00")]):
            a = fade_in(t, 0.3 + k * 0.8, 0.3)
            if a <= 0:
                continue
            yy = y + 180 + k * 120
            d.rounded_rectangle([x + 110, yy, x + w - 36, yy + 92], radius=20, fill=(210, 236, 255, int(255 * a)))
            d.text((x + 130, yy + 12), m, font=f, fill=(30, 30, 30, int(255 * a)))
            d.text((x + w - 110, yy + 58), hr, font=fs, fill=(120, 120, 120, int(255 * a)))
        if t > 3:
            d.text((x + 60, y + 580), "sem resposta...", font=fb, fill=(200, 60, 70, 255))
    else:
        big = font("sans_b", 130)
        d.text((x + w / 2 - fb.getlength("Ligando...") / 2, y + 140), "Ligando...", font=fb, fill=(60, 60, 70, 255))
        d.text((x + w / 2 - big.getlength("190") / 2, y + 220), "190", font=big, fill=(30, 60, 160, 255))
        r = 60 + 8 * math.sin(t * 6)
        d.ellipse([x + w / 2 - r, y + 560 - r, x + w / 2 + r, y + 560 + r], fill=(40, 170, 90, 255))
    img.alpha_composite(ov)


def world_shot(name):
    return abg(name).copy().convert("RGBA")


# ================================================================ CENAS
def s_cold(c):
    t = c.t
    img = focus_bg((60, 10, 20), (10, 6, 12), t, seed=1)
    b = bust("Ana", 1500, "shock", tq(t), c.talking("A"), 0.0, ("sweat",), None)
    oy = int(1500 * 0.34 + 62 * 1.5 * 1.0)
    band = b.crop((0, oy - 170, b.size[0], oy + 150))
    band = band.resize((W, int(band.size[1] * W / b.size[0])))
    shake = 6 * math.sin(t * 40) if t < 1.2 else 0
    y = H / 2 - band.size[1] / 2 + shake
    ImageDraw.Draw(img).rectangle([0, y - 8, W, y + band.size[1] + 8], fill=(20, 12, 16, 255))
    img.alpha_composite(band, (0, int(y)))
    sfx(img, "CLIC!", 1540, 240, 110, angle=-12, alpha=fade_in(t, 0.2, 0.25))
    return img


def s_title(c):
    t = c.t
    img = Image.new("RGBA", (W, H), (250, 248, 242, 255))
    d = ImageDraw.Draw(img)
    r = 330 * ease(t / 0.8)
    d.ellipse([W / 2 - r, H / 2 - r - 40, W / 2 + r, H / 2 + r - 40], fill=(214, 40, 56))
    d.rectangle([0, H - 170, W, H - 150], fill=(214, 40, 56))
    a = fade_in(t, 0.6)
    if a > 0:
        jf = jfont(64)
        d.text((150, 120), "第148話", font=jf, fill=(30, 20, 30))
        f1, f2, f3 = font("sans_b", 46), font("serif_b", 118), font("sans_b", 40)
        for txt, f, yy, col in (("DIREITO PENAL EM ANIME · EPISÓDIO 148", f1, 250, (255, 255, 255)),
                                ("A PORTA TRANCADA", f2, 430, (255, 255, 255)),
                                ("Art. 148 do Código Penal — Sequestro e Cárcere Privado", f3, 610, (255, 255, 255))):
            d.text((W / 2 - f.getlength(txt) / 2, yy), txt, font=f, fill=col, stroke_width=6, stroke_fill=(30, 20, 30))
        fs = font("sans", 28)
        txt = "História fictícia · finalidade educativa"
        d.text((W / 2 - fs.getlength(txt) / 2, H - 120), txt, font=fs, fill=(80, 70, 80))
    return img


def s_morning(c):
    t = c.t
    world = world_shot("rua")
    xa = lerp(300, 900, ease(t / 2.5))
    put_full(world, "Ana", 600, xa, cen.GROUND, c, walk=t * 5.5 if t < 2.4 else None, expr="happy" if t < 2.5 else "smile",
             look=0.8, spk="A")
    put_full(world, "Bruno", 620, 1350, cen.GROUND, c, expr="smile", look=-0.8, spk="B")
    img = camera(world, lerp(950, 1120, ease(t / c.T)), 700, 1900).convert("RGBA")
    petals(img, t)
    return img


def s_bust_street(name, expr, spk, look, fx=(), tint=(255, 220, 160)):
    def f(c):
        t = c.t
        img = camera(world_shot("rua"), 1300, 600, 1400).convert("RGBA").filter(ImageFilter.GaussianBlur(8))
        bokeh(img, t, color=tint)
        put_bust(img, name, 1000, W / 2 + (240 if name == "Carlos" else -240), 180, c, expr, look, fx, spk)
        petals(img, t, n=20)
        return img
    return f


def s_sala_close(c):
    t = c.t
    world = world_shot("sala")
    d = ImageDraw.Draw(world)
    close = ease((t - 1.6) / 1.0)
    cen.draw_door(d, 1 - close)
    xc = lerp(1150, 1520, ease(t / 1.6))
    put_full(world, "Carlos", 620, xc, cen.GROUND, c, walk=t * 5 if t < 1.5 else None,
             arms=("down", "reach") if t > 1.6 else ("down", "down"), expr="serious", look=0.8)
    put_full(world, "Ana", 590, 760, cen.GROUND, c, expr="neutral" if t < 2.2 else "worried", look=0.9)
    img = camera(world, 1200, 720, 2100).convert("RGBA")
    return img


def s_key(c):
    t = c.t
    img = focus_bg((40, 30, 50), (12, 10, 20), t, seed=7)
    d = ImageDraw.Draw(img)
    # fechadura grande e chave girando
    d.rounded_rectangle([760, 300, 1160, 800], radius=40, fill=(212, 176, 80), outline=(34, 24, 30), width=10)
    d.ellipse([900, 440, 1020, 560], fill=(30, 22, 18))
    d.polygon([(930, 530), (990, 530), (1010, 680), (910, 680)], fill=(30, 22, 18))
    ang = -90 * ease((t - 0.3) / 0.5)
    key = Image.new("RGBA", (700, 200), (0, 0, 0, 0))
    kd = ImageDraw.Draw(key)
    kd.ellipse([0, 20, 160, 180], fill=(230, 196, 100), outline=(34, 24, 30), width=8)
    kd.ellipse([50, 70, 110, 130], fill=(0, 0, 0, 0))
    kd.rectangle([150, 80, 620, 120], fill=(230, 196, 100), outline=(34, 24, 30), width=6)
    kd.rectangle([520, 120, 560, 170], fill=(230, 196, 100), outline=(34, 24, 30), width=6)
    key = key.rotate(ang, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(key, (int(960 - key.size[0] / 2 - 280 * math.cos(math.radians(ang)) * 0), int(500 - key.size[1] / 2)))
    sfx(img, "TRANC!", 1450, 260, 130, angle=-10, alpha=fade_in(t, 0.75, 0.2), color=(255, 90, 80))
    return img


def s_bust_room(name, expr, spk, look=0.0, fx=(), c1=(70, 60, 90), c2=(30, 26, 44), lines=True, seed=2):
    def f(c):
        img = focus_bg(c1, c2, c.t, lines=lines, seed=seed)
        put_bust(img, name, 1000, W / 2, 170, c, expr, look, fx, spk)
        return img
    return f


def s_door_try(c):
    t = c.t
    world = world_shot("sala")
    d = ImageDraw.Draw(world)
    jig = 10 * math.sin(t * 34) if 0.8 < t < 2.6 else 0
    cen.draw_door(d, 0, jiggle=jig)
    put_full(world, "Carlos", 620, 900, cen.GROUND, c, expr="serious", arms=("cross", "cross"), look=0.8)
    put_full(world, "Ana", 600, 1460, cen.GROUND, c, arms=("chest", "reach"), expr="worried", look=0.9, fx=("sweat",), spk="A")
    img = camera(world, 1300, 700, 1700).convert("RGBA")
    if 0.8 < t < 2.8:
        sfx(img, "TREC! TREC!", 1500, 230, 90, angle=8, alpha=fade_in(t, 0.8, 0.2), color=(255, 240, 120))
    return img


def s_shock_stamp(c):
    t = c.t
    img = focus_bg((20, 30, 60), (6, 8, 20), t, seed=9)
    speed_lines(img, t, W / 2, 560, color=(255, 255, 255), n=160, seed=9, alpha=140, inner=420)
    put_bust(img, "Ana", 1000, W / 2, 200, c, "shock", 0.0, ("sweat",))
    stamp(img, "PRIVAÇÃO DA LIBERDADE", fade_in(t, 0.8, 0.4))
    return img


def s_think_caput(c):
    t = c.t
    img = focus_bg((24, 60, 110), (10, 20, 50), t, lines=False)
    rnd = random.Random(2)
    d = ImageDraw.Draw(img)
    for _ in range(18):
        x = rnd.random() * W
        y = (rnd.random() * H - t * 30 * (0.5 + rnd.random())) % H
        d.text((x, y), rnd.choice(["§", "Art.", "CP", "148"]), font=font("serif_b", 40 + rnd.randint(0, 30)),
               fill=(120, 170, 230, 90))
    put_bust(img, "Ana", 900, 470, 230, c, "determined", 0.6, (), "AI")
    lines = ["**Privar** alguém de sua liberdade,", "mediante **sequestro** ou **cárcere privado**:",
             "Pena — **reclusão, de 1 a 3 anos**."]
    shown = 1 + int(clamp((t - 1.0) / max(1, c.T - 3) * 3, 0, 2.99))
    status_window(img, "ART. 148 — CÓDIGO PENAL (caput)", lines, shown, 900, 280, 900, fade_in(t, 0.5))
    return img


def s_split(c):
    t = c.t
    img = focus_bg((28, 40, 70), (12, 16, 30), t, lines=False)
    pw = 860
    for i, (bgn, label, col, cam) in enumerate([("sitio", "SEQUESTRO", (80, 150, 230), (1200, 760, 2000)),
                                                ("quarto", "CÁRCERE PRIVADO", (230, 80, 100), (1104, 640, 2208))]):
        world = world_shot(bgn)
        if i == 0:
            put_full(world, "Ana", 520, 1100 + 450 * math.sin(t * 0.4), 1120, c, walk=t * 5, expr="worried",
                     look=math.cos(t * 0.4))
        else:
            put_full(world, "Ana", 580, 1000, 1060, c, arms=("chest", "down"), expr="sad", look=0.6)
        view = camera(world, *cam).resize((pw, int(pw * 9 / 16))).convert("RGBA")
        x0, y0 = 70 + i * (pw + 60), 180
        a = fade_in(t, 0.3 + i * (c.T * 0.3), 0.5)
        if a <= 0:
            continue
        d = ImageDraw.Draw(img)
        d.rectangle([x0 - 8, y0 - 8, x0 + pw + 8, y0 + view.size[1] + 8], fill=(34, 24, 30))
        img.alpha_composite(view, (x0, y0))
        sfx(img, label, x0 + pw / 2, y0 - 10, 56, angle=-3 if i == 0 else 3, color=col, stroke=(255, 255, 255))
    if t > c.T * 0.62:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        d.rounded_rectangle([200, 760, W - 200, 880], radius=24, fill=(10, 24, 48, 230), outline=(255, 214, 90, 255), width=4)
        txt = "Mesmo art. 148 · mesma pena (reclusão de 1 a 3 anos)"
        f = font("sans_b", 44)
        d.text((W / 2 - f.getlength(txt) / 2, 792), txt, font=f, fill=(255, 214, 90))
        img.alpha_composite(ov)
    return img


def s_eyecatch(c):
    t = c.t
    img = Image.new("RGBA", (W, H), (255, 236, 200, 255))
    d = ImageDraw.Draw(img)
    for k in range(12):
        a0 = k * 30 + t * 20
        d.pieslice([W / 2 - 1400, H / 2 - 1400, W / 2 + 1400, H / 2 + 1400], a0, a0 + 15, fill=(255, 214, 150))
    sc = 1 + 0.06 * math.sin(t * 4)
    sfx(img, "ART. 148", W / 2, H / 2 - 40, int(200 * sc), angle=-6, color=(214, 40, 56), stroke=(255, 255, 255))
    f = font("sans_b", 44)
    txt = "Direito Penal em Anime"
    d.text((W / 2 - f.getlength(txt) / 2, H / 2 + 120), txt, font=f, fill=(60, 40, 50))
    sparkles(img, t, W / 2, H / 2, 700)
    return img


def s_bruno_chat(c):
    t = c.t
    world = world_shot("bruno")
    img = camera(world, 900, 640, 1500).convert("RGBA").filter(ImageFilter.GaussianBlur(4))
    fx = ("sweat",) if t > c.st(1) - 0.5 else ()
    put_bust(img, "Bruno", 980, 640, 200, c, "worried" if t > c.st(1) - 0.5 else "neutral", 0.5, fx, "B")
    phone_ui(img, 1300, 170, t, "chat")
    if c.st(1) - 0.6 < t < c.st(1) + 1.2:
        sfx(img, "!?", 1020, 220, 150, angle=-8, alpha=fade_in(t, c.st(1) - 0.6, 0.2), color=(255, 90, 80))
    return img


def s_bruno_call(c):
    t = c.t
    world = world_shot("bruno")
    img = camera(world, 900, 640, 1500).convert("RGBA").filter(ImageFilter.GaussianBlur(4))
    put_bust(img, "Bruno", 980, 640, 200, c, "determined", 0.5, (), "B", prop="phone")
    phone_ui(img, 1300, 170, t, "call")
    if c.talking("P"):
        sfx(img, "♪ 190", 1500, 960, 50, alpha=1.0, color=(140, 200, 255))
    return img


def s_twoshot(c):
    t = c.t
    world = world_shot("sala")
    d = ImageDraw.Draw(world)
    cen.draw_door(d, 0)
    fxc = ("sweat",) if c.talking("C") else ()
    put_full(world, "Ana", 600, 980, cen.GROUND, c, arms=("down", "wave") if c.talking("A") else ("down", "down"),
             expr="determined", look=0.8, spk="A")
    put_full(world, "Carlos", 620, 1420, cen.GROUND, c, arms=("cross", "cross"), expr="sigh" if c.talking("C") else "serious",
             look=-0.8, fx=fxc, spk="C")
    img = camera(world, 1200, 720, 1750).convert("RGBA")
    if c.talking("A") and t > c.st(0) + 3:
        sfx(img, "§ 1º!", 700, 250, 90, angle=-8, alpha=fade_in(t, c.st(0) + 3, 0.2), color=(255, 214, 90))
    return img


def s_status_qualif(c):
    t = c.t
    img = focus_bg((24, 60, 110), (10, 20, 50), t, lines=False)
    put_bust(img, "Ana", 820, 380, 300, c, "determined", 0.6, (), "AI")
    l1 = ["§ 1º (**2 a 5 anos**): vítima **ascendente, descendente, cônjuge ou companheiro(a)** do agente, ou **maior de 60**",
          "internação em **casa de saúde ou hospital** · privação por **mais de 15 dias**",
          "vítima **menor de 18 anos** · **fins libidinosos**",
          "§ 2º (**2 a 8 anos**): **grave sofrimento físico ou moral** por maus-tratos ou pela natureza da detenção"]
    shown = 1 + int(clamp(t / max(1, c.T - 2) * 4, 0, 3.99))
    status_window(img, "FORMAS QUALIFICADAS — ART. 148", l1, shown, 760, 150, 1100, fade_in(t, 0.3))
    return img


def s_rescue(c):
    t = c.t
    world = world_shot("fachada")
    d = ImageDraw.Draw(world)
    cen.draw_police_car(d, 520, cen.GROUND + 20, t)
    put_full(world, "Policial", 600, 1180, cen.GROUND, c, arms=("down", "reach") if t < 2.5 else ("down", "down"),
             look=0.8, spk="P")
    put_full(world, "Bruno", 610, 880, cen.GROUND, c, expr="worried", look=0.8)
    img = camera(world, 1100, 700, 2000).convert("RGBA")
    # luzes da viatura sobre a cena
    ov = Image.new("RGBA", img.size, (230, 40, 50, 36) if int(t * 3) % 2 else (40, 90, 230, 36))
    img.alpha_composite(ov)
    if t < 2.0:
        sfx(img, "TOC TOC!", 1500, 360, 100, angle=-6, alpha=fade_in(t, 0.3, 0.2), color=(255, 240, 150))
    return img


def s_reunion(c):
    t = c.t
    world = world_shot("fachada")
    d = ImageDraw.Draw(world)
    cen.draw_police_car(d, 420, cen.GROUND + 20, t)
    fx0, fy0, fx1, fy1 = cen.FACHADA_DOOR
    d.rectangle([fx0, fy0, fx1, fy1], fill=(40, 28, 20))
    xa = lerp(1410, 1180, ease(t / 1.4))
    put_full(world, "Bruno", 610, 900, cen.GROUND, c, expr="relief", arms=("down", "open"), look=0.8, spk="B")
    put_full(world, "Ana", 590, xa, cen.GROUND, c, walk=t * 5 if t < 1.3 else None, expr="happy", look=-0.8,
             fx=("tear",) if t > 2 else (), spk="A")
    img = camera(world, 1050, 700, 1600).convert("RGBA")
    sparkles(img, t, 1000, 500, 500)
    return img


def s_police_carlos(c):
    t = c.t
    world = world_shot("fachada")
    d = ImageDraw.Draw(world)
    cen.draw_police_car(d, 520, cen.GROUND + 20, t)
    put_full(world, "Carlos", 620, 1160, cen.GROUND, c, expr="sigh", look=-0.6, spk="C")
    put_full(world, "Policial", 600, 1480, cen.GROUND, c, look=-0.8, spk="P")
    img = camera(world, 1200, 700, 1800).convert("RGBA")
    return img


BOARD = [
    "Art. 148: **privar alguém da liberdade** — reclusão de 1 a 3 anos",
    "Sequestro x cárcere privado: **mesmo artigo**, mesma pena",
    "§ 1º: **2 a 5 anos** · § 2º: **2 a 8 anos** (qualificadoras)",
    "Sem **causa de aumento** nem **de diminuição** própria",
    "Hediondo: **só § 1º, IV** (menor de 18) — Lei 14.811/2024",
    "Resgate → **art. 159** · Constrangimento ilegal → **art. 146**",
]


def s_class(c):
    t = c.t
    img = Image.new("RGBA", (W, H), (236, 226, 200, 255))
    d = ImageDraw.Draw(img)
    # janelas da sala de aula
    for k in range(3):
        x = 80 + k * 200
        d.rectangle([x, 80, x + 160, 520], fill=(170, 210, 240), outline=(120, 100, 80), width=10)
    d.rectangle([0, 860, W, H], fill=(170, 130, 90))
    # quadro-negro
    bx0, by0, bx1, by1 = 700, 70, 1860, 700
    d.rectangle([bx0 - 20, by0 - 20, bx1 + 20, by1 + 20], fill=(120, 84, 50))
    d.rectangle([bx0, by0, bx1, by1], fill=(36, 70, 56))
    d.text((bx0 + 40, by0 + 24), "AULA DO EPISÓDIO — ART. 148", font=font("sans_b", 42), fill=(250, 246, 220))
    # itens aparecem conforme as falas de Ana (0, 2, 2, 4, 6, 6)
    reveal = [0, 0, 2, 2, 4, 6]
    for k, it in enumerate(BOARD):
        li = reveal[k]
        if t >= c.st(li) + (1.5 if k % 2 else 0.3):
            draw_rich(d, (bx0 + 50, by0 + 100 + k * 92), "• " + it, 32, bx1 - bx0 - 90,
                      color=(240, 240, 226), hlcolor=(255, 226, 120), base="sans", hl="sans_b")
    put_full(img, "Ana", 640, 420, 1040, c, arms=("down", "wave") if c.talking("A") else ("down", "down"),
             expr="smile", look=0.8, spk="A")
    put_bust(img, "Bruno", 560, 1500, 560, c, "neutral" if not c.talking("B") else "smile", -0.6, (), "B")
    d = ImageDraw.Draw(img)
    d.rectangle([1150, 1000, 1850, 1080], fill=(150, 110, 70))
    return img


def s_next(c):
    t = c.t
    img = Image.new("RGBA", (W, H), (20, 16, 30, 255))
    speed_lines(img, t, W / 2, H / 2, color=(214, 40, 56), n=90, seed=5, alpha=120, inner=300)
    d = ImageDraw.Draw(img)
    f1, f2 = font("sans_b", 48), font("serif_b", 104)
    for txt, f, yy in (("PRÓXIMO EPISÓDIO", f1, 280), ("ART. 159", f2, 380), ("Extorsão mediante sequestro", f1, 540)):
        d.text((W / 2 - f.getlength(txt) / 2, yy), txt, font=f, fill=(255, 255, 255), stroke_width=6,
               stroke_fill=(214, 40, 56))
    fs = font("sans", 28)
    txt = "História e personagens fictícios · finalidade exclusivamente educativa"
    d.text((W / 2 - fs.getlength(txt) / 2, 800), txt, font=fs, fill=(190, 180, 200))
    end = fade_in(t, c.T - 1.2, 1.0)
    if end > 0:
        img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * end))))
    return img


# (função, falas [(falante, texto)], duração mínima, efeitos sonoros [(t, tipo)])
SHOTS = [
    (s_cold, [("A", "Carlos... por que você trancou a porta?!")], 4.0, [(0.2, "click"), (0.0, "sting")]),
    (s_title, [("N", "Direito Penal em anime. Episódio cento e quarenta e oito: A porta trancada.")], 6.5, [(0.0, "jingle")]),
    (s_morning, [("A", "Bruno! Hoje eu vou estudar o dia inteiro pra prova de Penal!"),
                 ("B", "Boa sorte, Ana! Me manda mensagem quando chegar em casa, tá?"),
                 ("A", "Pode deixar!")], 9.0, []),
    (s_bust_street("Carlos", "smile", "C", 0.6), [("C", "Ana! Quanto tempo! Vem comigo, quero te mostrar uma coisa lá em casa.")], 4.5, []),
    (s_bust_street("Ana", "neutral", "A", -0.6), [("A", "Tá bom... mas é rapidinho. Eu preciso estudar.")], 3.5, []),
    (s_sala_close, [("N", "Mas, dentro da casa de Carlos...")], 3.2, [(2.3, "thump")]),
    (s_key, [], 2.4, [(0.75, "click"), (0.75, "sting")]),
    (s_bust_room("Ana", "worried", "A", 0.4, ("sweat",)), [("A", "Carlos, abre a porta. Eu quero ir embora.")], 3.5, []),
    (s_bust_room("Carlos", "serious", "C", -0.2, ("shade",), (90, 20, 30), (20, 6, 10), seed=4),
     [("C", "Você só sai daqui quando eu deixar.")], 3.5, [(0.0, "drone")]),
    (s_door_try, [("A", "Está trancada...!")], 3.4, [(0.8, "rattle")]),
    (s_shock_stamp, [("N", "Neste momento, Ana foi privada de sua liberdade de locomoção, contra a sua vontade.")], 5.0,
     [(0.8, "sting")]),
    (s_think_caput, [("AI", "Calma, Ana. Pensa. Artigo cento e quarenta e oito do Código Penal: privar alguém de sua "
                            "liberdade, mediante sequestro ou cárcere privado. Pena: reclusão, de um a três anos.")], 9.0, []),
    (s_split, [("AI", "Se ele me prendesse num quarto, seria cárcere privado. Se me impedisse de sair de um sítio, "
                      "sequestro. Os dois estão no mesmo artigo, com a mesma pena.")], 8.0, []),
    (s_eyecatch, [], 3.0, [(0.0, "jingle")]),
    (s_bruno_chat, [("B", "Já são dez da noite... A Ana sempre responde."), ("B", "Tem alguma coisa errada.")], 6.0,
     [(0.0, "drone")]),
    (s_bruno_call, [("B", "Alô, polícia? Minha amiga não responde desde a tarde. Ela disse que ia encontrar um tal de Carlos."),
                    ("P", "Entendido, senhor. Vamos verificar o endereço agora.")], 8.0, []),
    (s_twoshot, [("A", "Sabia que, se você me mantiver aqui por mais de quinze dias, a pena sobe para dois a cinco anos? "
                       "Parágrafo primeiro!"), ("C", "Você e esse seu Direito...")], 8.0, []),
    (s_status_qualif, [("AI", "E também seria mais grave se eu fosse ascendente, descendente, cônjuge ou companheira dele, "
                              "maior de sessenta ou menor de dezoito anos; se houvesse internação em casa de saúde ou "
                              "hospital; ou fins libidinosos. E, com grave sofrimento físico ou moral, seriam dois a oito "
                              "anos: parágrafo segundo.")], 12.0, []),
    (s_rescue, [("P", "Polícia! Abra a porta, por favor.")], 4.0, [(0.3, "knock"), (0.0, "siren")]),
    (s_bust_room("Carlos", "sigh", "C", 0.0, ("sweat",), (60, 60, 80), (24, 24, 36), lines=False),
     [("C", "... Tudo bem.")], 3.0, []),
    (s_reunion, [("B", "Ana! Você está bem?"), ("A", "Agora estou. Obrigada, Bruno!")], 5.5, [(0.5, "sparkle")]),
    (s_police_carlos, [("P", "O senhor vai nos acompanhar até a delegacia para prestar esclarecimentos."),
                       ("N", "E os fatos passam a ser analisados pelas autoridades competentes.")], 7.0, []),
    (s_class, [("A", "Aula do episódio! O artigo cento e quarenta e oito protege a liberdade de locomoção. Sequestro e "
                     "cárcere privado estão no mesmo artigo."),
               ("B", "E as formas mais graves?"),
               ("A", "São qualificadoras: parágrafo primeiro, dois a cinco anos; parágrafo segundo, dois a oito. E o artigo "
                     "não tem causa de aumento nem de diminuição própria."),
               ("B", "É crime hediondo?"),
               ("A", "Só quando a vítima é menor de dezoito anos, desde a Lei catorze mil, oitocentos e onze, de dois mil e "
                     "vinte e quatro."),
               ("B", "E se o Carlos pedisse resgate?"),
               ("A", "Aí seria extorsão mediante sequestro, artigo cento e cinquenta e nove! E não confunda com o "
                     "constrangimento ilegal, do artigo cento e quarenta e seis.")], 20.0, [(0.0, "jingle")]),
    (s_next, [("N", "No próximo episódio: artigo cento e cinquenta e nove, extorsão mediante sequestro! Não percam!")], 7.0,
     [(0.0, "sting")]),
]

VOICE = {"N": (1.0, None), "A": (1.3, None), "AI": (1.3, "echo"), "B": (1.12, None), "C": (0.84, None), "P": (0.94, None)}


# ---------------------------------------------------------------- áudio
def synth(text, spk, voice, tmp, idx, length_scale):
    raw = os.path.join(tmp, f"r{idx}.wav")
    out = os.path.join(tmp, f"v{idx}.wav")
    subprocess.run(["piper", "-m", voice, "-f", raw, "--length-scale", str(length_scale), "--sentence-silence", "0.15"],
                   input=text.encode("utf-8"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    f, eff = VOICE[spk]
    af = f"asetrate=16000*{f},aresample=16000,atempo={1 / f:.4f}"
    if eff == "echo":
        af += ",aecho=0.8:0.6:60:0.3"
    af += f",aresample={SR}"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ac", "1", out],
                   check=True)
    with wave.open(out) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def sfx_audio(kind):
    n = int(SR * 2.5)
    t = np.arange(n) / SR
    rnd = np.random.default_rng(1)
    if kind == "click":
        x = rnd.normal(0, 1, int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / 150)
        return x * 0.5
    if kind == "thump":
        x = np.sin(2 * np.pi * 70 * t[:SR // 2]) * np.exp(-t[:SR // 2] * 12)
        return x * 0.8
    if kind == "knock":
        k = np.sin(2 * np.pi * 110 * t[:SR // 5]) * np.exp(-t[:SR // 5] * 30)
        out = np.zeros(int(SR * 0.8))
        for st in (0, int(0.28 * SR)):
            out[st:st + len(k)] += k
        return out * 0.9
    if kind == "rattle":
        out = np.zeros(int(SR * 1.8))
        for st in np.arange(0, 1.7, 0.12):
            i = int(st * SR)
            b = rnd.normal(0, 1, int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / 300)
            out[i:i + len(b)] += b * 0.35
        return out
    if kind == "sting":
        env = np.exp(-t * 1.6)
        x = sum(np.sin(2 * np.pi * f * t) for f in (55, 110, 164.8, 233.1)) * env
        return x * 0.18
    if kind == "drone":
        return np.sin(2 * np.pi * 55 * t) * np.minimum(1, t) * np.exp(-t * 0.5) * 0.15
    if kind == "siren":
        f = 750 + 250 * np.sign(np.sin(2 * np.pi * 1.2 * t))
        ph = np.cumsum(2 * np.pi * f / SR)
        return np.sin(ph) * 0.05 * np.minimum(1, t * 2)
    if kind == "sparkle":
        out = np.zeros(n)
        for k, f in enumerate((1568, 2093, 2637, 3136)):
            i = int(k * 0.09 * SR)
            m = n - i
            out[i:] += np.sin(2 * np.pi * f * t[:m]) * np.exp(-t[:m] * 8) * 0.12
        return out
    if kind == "jingle":
        out = np.zeros(n)
        notes = (523.25, 659.25, 783.99, 1046.5, 783.99, 1046.5)
        for k, f in enumerate(notes):
            i = int(k * 0.14 * SR)
            m = n - i
            out[i:] += (np.sin(2 * np.pi * f * t[:m]) + 0.3 * np.sin(4 * np.pi * f * t[:m])) * np.exp(-t[:m] * 5) * 0.12
        return out
    return np.zeros(1)


def music(n):
    """Trilha de fundo: pad suave em lá menor com arpejo leve."""
    t = np.arange(n) / SR
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
    out = np.zeros(n, np.float32)
    dur = 4.0
    for k in range(int(n / SR / dur) + 1):
        i0, i1 = int(k * dur * SR), int(min(n, (k + 1) * dur * SR + SR))
        tt = t[i0:i1] - k * dur
        env = np.clip(tt / 0.8, 0, 1) * np.clip((dur + 1 - tt) / 1.0, 0, 1)
        ch = chords[k % 4]
        for f in ch:
            out[i0:i1] += 0.5 * env * np.sin(2 * np.pi * f / 2 * t[i0:i1])
        for j in range(8):  # arpejo
            s0 = i0 + int(j * dur / 8 * SR)
            m = min(n - s0, int(0.5 * SR))
            if m <= 0:
                continue
            f = ch[j % 3] * (2 if j % 4 == 3 else 1)
            out[s0:s0 + m] += 0.18 * np.sin(2 * np.pi * f * t[:m]) * np.exp(-t[:m] * 6)
    out /= np.max(np.abs(out)) + 1e-6
    return out * 0.07


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="episodio148_anime.mp4")
    ap.add_argument("--length-scale", type=float, default=0.9)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    tmp = tempfile.mkdtemp()

    lead, gap = 0.35, 0.35
    timeline, voice_parts, sfx_parts, subs = [], [], [], []
    tcur, idx = 0.0, 0
    for si, (fn, lines, mn, fxs) in enumerate(SHOTS):
        tl, spans = lead, []
        for spk, text in lines:
            a = synth(text, spk, args.voice, tmp, idx, args.length_scale)
            idx += 1
            dur = len(a) / SR
            spans.append((spk, tl, tl + dur))
            voice_parts.append((tcur + tl, a))
            parts = chunk_line(text)
            tot = sum(len(p) for p in parts)
            acc = 0
            for p in parts:
                s0 = tcur + tl + dur * acc / tot
                acc += len(p)
                subs.append((s0, tcur + tl + dur * acc / tot + 0.15, spk, p))
            tl += dur + gap
        T = round(max(mn, tl + 0.4) * FPS) / FPS
        for (ts, kind) in fxs:
            sfx_parts.append((tcur + ts, sfx_audio(kind)))
        timeline.append((si, T, spans, tcur))
        tcur += T
    total = tcur
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for ts, a in voice_parts:
        i = int(ts * SR)
        voice[i:i + len(a)] += a[: n - i]
    fxmix = np.zeros(n, np.float32)
    for ts, a in sfx_parts:
        i = int(ts * SR)
        fxmix[i:i + len(a)] += a[: n - i].astype(np.float32)
    env = np.convolve((np.abs(voice) > 0.02).astype(np.float32), np.ones(int(0.4 * SR)) / (0.4 * SR), mode="same")
    mix = voice + fxmix + music(n) * (1 - 0.5 * np.clip(env * 3, 0, 1))
    fade = np.clip(np.minimum(np.arange(n), n - np.arange(n)) / (1.0 * SR), 0, 1)
    mix = np.clip(mix * fade, -1, 1)
    wav_path = os.path.join(tmp, "mix.wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print(f"Duração total: {total / 60:.2f} min")

    base = os.path.splitext(args.out)[0]

    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for i, (a, b, spk, p) in enumerate(subs, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{SPEAKER[spk][0]}: {p}\n\n")

    if args.preview:
        os.makedirs("preview", exist_ok=True)
        for si, T, spans, t0 in timeline:
            for k, frac in enumerate((0.3, 0.8)):
                t = T * frac
                SHOTS[si][0](Ctx(t, T, spans)).convert("RGB").save(f"preview/s{si + 1:02d}_{k}.png")
        return

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium",
                             "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                             "-movflags", "+faststart", "-shortest", args.out], stdin=subprocess.PIPE)
    prev = None
    k_sub = 0
    for si, T, spans, t0 in timeline:
        nf = int(round(T * FPS))
        print(f"cena {si + 1}/{len(SHOTS)}: {T:.1f}s", flush=True)
        for k in range(nf):
            t = k / FPS
            img = SHOTS[si][0](Ctx(t, T, spans))
            gt = t0 + t
            while k_sub < len(subs) and subs[k_sub][1] < gt:
                k_sub += 1
            if k_sub < len(subs) and subs[k_sub][0] <= gt <= subs[k_sub][1]:
                subtitle(img, subs[k_sub][2], subs[k_sub][3])
            arr = np.asarray(img.convert("RGB"))
            if prev is not None and k < 8:  # cortes rápidos, com fusão curta
                a = (k + 1) / 9
                arr = (prev.astype(np.float32) * (1 - a) + arr.astype(np.float32) * a).astype(np.uint8)
            proc.stdin.write(arr.tobytes())
            if k == nf - 1:
                prev = arr
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg falhou")
    print("OK:", args.out)


if __name__ == "__main__":
    main()
