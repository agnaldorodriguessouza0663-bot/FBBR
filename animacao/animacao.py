# -*- coding: utf-8 -*-
"""Animação educativa: Art. 148 do CP — estudo de caso com Ana, Carlos e Bruno.

Uso: python3 animacao.py --voice pt-br-edresson-low.onnx [--out art148_estudo_de_caso.mp4] [--preview]
"""
import argparse
import math
import os
import subprocess
import sys
import tempfile
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gerar_video import C, draw_lock, draw_rich, draw_scale, font, rich_height  # noqa: E402

import cenarios as cen  # noqa: E402
from personagens import ANA, BRUNO, CARLOS, POLICIAL, draw_character, paste_character  # noqa: E402

W, H, FPS = 1920, 1080, 30
BAR = 120  # faixas de cinema (letterbox) nas cenas da história
SR = 22050


# ---------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


def fade_in(t, t0, d=0.6):
    return ease((t - t0) / d)


class Ctx:
    def __init__(self, t, T, starts):
        self.t, self.T, self.s = t, T, starts

    def seg(self):
        k = 0
        for i, s in enumerate(self.s):
            if self.t >= s:
                k = i
        return k


BG = {}


def bg(name):
    if name not in BG:
        BG[name] = {
            "rua": lambda: cen.city_street(False),
            "rua_noite": lambda: cen.city_street(True),
            "sala": cen.interior_sala,
            "quarto": cen.quarto,
            "sitio": cen.sitio,
            "bruno": cen.casa_bruno_noite,
            "estudo": cen.estudo_ana,
            "fachada": cen.casa_fachada,
        }[name]()
    return BG[name]


def camera(world, cx, cy, w):
    """Recorta o mundo (2208x1242) com centro (cx, cy) e largura w; devolve 1920x1080."""
    h = w * 9 / 16
    x0 = clamp(cx - w / 2, 0, cen.BW - w)
    y0 = clamp(cy - h / 2, 0, cen.BH - h)
    return world.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def char(spec, h, x, y, canvas, **kw):
    paste_character(canvas, draw_character(spec, h, **kw), x, y)


_VIG = None


def cinematic(img):
    """Vinheta suave + faixas de cinema."""
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        _VIG = np.clip(1.08 - 0.32 * r ** 2, 0.55, 1.0)[..., None]
    a = np.asarray(img.convert("RGB")).astype(np.float32) * _VIG
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, W, BAR], fill=(0, 0, 0))
    d.rectangle([0, H - BAR, W, H], fill=(0, 0, 0))
    return out


def overlay_text(img, text, y, size, alpha, color=(236, 196, 90), serif=True, shadow=True):
    if alpha <= 0:
        return
    f = font("serif_b" if serif else "sans_b", size)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    tw = f.getlength(text)
    x = (W - tw) / 2
    a = int(255 * alpha)
    if shadow:
        d.text((x + 3, y + 4), text, font=f, fill=(0, 0, 0, int(a * 0.7)))
    d.text((x, y), text, font=f, fill=color + (a,))
    img.alpha_composite(ov)


def stamp(img, text, alpha, color=(200, 50, 60), y=180):
    """Selo de destaque (ex.: PRIVAÇÃO DA LIBERDADE)."""
    if alpha <= 0:
        return
    f = font("sans_b", 64)
    tw = f.getlength(text)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    s = 1 + 0.25 * (1 - alpha)
    x0, x1 = W / 2 - (tw / 2 + 50) * s, W / 2 + (tw / 2 + 50) * s
    a = int(235 * alpha)
    d.rounded_rectangle([x0, y, x1, y + 110], radius=14, fill=(20, 16, 20, int(a * 0.75)), outline=color + (a,), width=6)
    d.text((W / 2 - tw / 2, y + 18), text, font=f, fill=color + (a,))
    img.alpha_composite(ov)


def bubble(img, text, x, y, alpha=1.0):
    if alpha <= 0:
        return
    f = font("sans_b", 36)
    tw = f.getlength(text)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(240 * alpha)
    d.rounded_rectangle([x - tw / 2 - 30, y - 90, x + tw / 2 + 30, y - 10], radius=30, fill=(255, 255, 255, a))
    d.polygon([(x - 18, y - 12), (x + 18, y - 12), (x, y + 18)], fill=(255, 255, 255, a))
    d.text((x - tw / 2, y - 74), text, font=f, fill=(30, 30, 40, a))
    img.alpha_composite(ov)


# ---------------------------------------------------------------- telas jurídicas
def legal_base(title, kicker="ART. 148 · CÓDIGO PENAL"):
    img = Image.new("RGB", (W, H))
    arr = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H)[:, None]
    for i in range(3):
        arr[:, :, i] = C["bg1"][i] * (1 - t) + C["bg2"][i] * t
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((140, 60), kicker, font=font("sans_b", 26), fill=C["gold"])
    d.line([140, 104, W - 140, 104], fill=(60, 76, 100), width=2)
    d.text((140, 130), title, font=font("serif_b", 64), fill=C["text"])
    d.rectangle([140, 222, 260, 228], fill=C["gold"])
    return img


def card(img, x, y, w, h, head, body, color, alpha=1.0, size=32):
    if alpha <= 0:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    c = C[color] if isinstance(color, str) else color
    dy = int(20 * (1 - alpha))
    d.rounded_rectangle([x, y + dy, x + w, y + h + dy], radius=16, fill=C["panel"])
    d.rounded_rectangle([x, y + dy, x + 10, y + h + dy], radius=4, fill=c)
    hh = draw_rich(d, (x + 36, y + 26 + dy), head, size + 2, w - 60, color=c, hlcolor=c, base="sans_b", hl="sans_b")
    draw_rich(d, (x + 36, y + 40 + hh + dy), body, size, w - 60)
    if alpha < 1:
        a = np.asarray(ov).copy()
        a[:, :, 3] = (a[:, :, 3] * alpha).astype(np.uint8)
        ov = Image.fromarray(a)
    img.alpha_composite(ov)


def banner(img, x, y, w, text, color, alpha=1.0, size=36):
    if alpha <= 0:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    c = C[color]
    h = rich_height(text, size, w - 100) + 50
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=C["bg1"], outline=c, width=4)
    draw_rich(d, (x + 50, y + 25), text, size, w - 100, hlcolor=color)
    if alpha < 1:
        a = np.asarray(ov).copy()
        a[:, :, 3] = (a[:, :, 3] * alpha).astype(np.uint8)
        ov = Image.fromarray(a)
    img.alpha_composite(ov)


# ================================================================= CENAS
# Cada cena: segs (narração), min (duração mínima, s) e draw(ctx) -> Image RGB 1920x1080.

def cena1(c):
    t, s = c.t, c.s
    if t < s[1] + 0.2:
        world = bg("rua").copy().convert("RGBA")
        x = lerp(300, 1500, t / (s[1] + 0.2))
        char(ANA, 560, x, cen.GROUND, world, t=t, walk=t * 5.5, expr="smile", look=0.6)
        img = camera(world, lerp(900, 1250, t / s[1]), 700, 2000).convert("RGBA")
        overlay_text(img, "ARTIGO 148 DO CÓDIGO PENAL", 180, 76, fade_in(t, 0.8) * (1 - fade_in(t, s[1] - 0.6, 0.5)))
    else:
        tb = t - s[1]
        img = Image.new("RGBA", (W, H), (14, 16, 24, 255))
        d = ImageDraw.Draw(img)
        # Código Penal
        bx, by = 330, 330
        d.rectangle([bx + 24, by + 20, bx + 444, by + 600], fill=(60, 16, 20))
        d.rectangle([bx, by, bx + 420, by + 580], fill=(110, 26, 34))
        d.rectangle([bx + 24, by + 24, bx + 396, by + 556], outline=(212, 176, 80), width=4)
        for txt, yy, sz in (("CÓDIGO", 140, 56), ("PENAL", 210, 56), ("Decreto-Lei nº 2.848/1940", 330, 24)):
            f = font("serif_b", sz)
            d.text((bx + 210 - f.getlength(txt) / 2, by + yy), txt, font=f, fill=(226, 190, 96))
        draw_scale(d, bx + 210, by + 470, 60, (226, 190, 96))
        # liberdade interrompida: porta iluminada que se fecha
        x0, y0, x1, y1 = 1180, 300, 1560, 900
        d.rectangle([x0 - 20, y0 - 20, x1 + 20, y1], fill=(60, 60, 70))
        d.rectangle([x0, y0, x1, y1], fill=(255, 226, 160))
        closing = ease((tb - 1.2) / 2.2)
        for k in range(5):
            bxk = x0 + 60 + k * 70 + tb * 120 * (1 - closing)
            byk = y0 + 150 + 40 * math.sin(k * 1.7 + tb * 2)
            if bxk < x1 - 20:
                d.arc([bxk - 20, byk - 10, bxk, byk + 10], 200, 340, fill=(40, 40, 50), width=5)
                d.arc([bxk, byk - 10, bxk + 20, byk + 10], 200, 340, fill=(40, 40, 50), width=5)
        wdoor = (x1 - x0) * closing
        d.rectangle([x0, y0, x0 + wdoor, y1], fill=(80, 56, 38))
        if closing > 0.98:
            draw_lock(d, x1 + 70, (y0 + y1) / 2, 70, "gold")
        overlay_text(img, "SEQUESTRO E CÁRCERE PRIVADO", 150, 76, fade_in(tb, 0.3))
    return cinematic(img)


def cena2(c):
    t = c.t
    img = Image.new("RGBA", (W, H), (10, 12, 18, 255))
    panels = [("estudo", ANA, "ANA", "a vítima", "smile", (1100, 700)),
              ("rua", CARLOS, "CARLOS", "o autor da privação da liberdade", "neutral", (1500, 700)),
              ("bruno", BRUNO, "BRUNO", "o amigo que procura ajuda", "neutral", (1500, 700))]
    pw = W // 3
    for i, (bgn, spec, name, role, expr, (cx, cy)) in enumerate(panels):
        a = fade_in(t, 0.4 + i * 1.6, 0.8)
        if a <= 0:
            continue
        world = bg(bgn).copy().convert("RGBA")
        char(spec, 640, cx, 1150, world, t=t, expr=expr, seed=i,
             arms=("down", "phone") if spec is BRUNO else ("down", "down"))
        view = camera(world, cx, cy - 20 + 20 * math.sin(t * 0.3), 1000)
        view = view.resize((int(W * 1.0), H)).crop((W // 2 - pw // 2, 0, W // 2 + pw // 2, H))
        panel = view.convert("RGBA")
        d = ImageDraw.Draw(panel)
        d.rectangle([0, H - 330, pw, H - 120], fill=(10, 12, 18, 200))
        f = font("serif_b", 70)
        d.text((pw / 2 - f.getlength(name) / 2, H - 310), name, font=f, fill=C["gold"])
        f2 = font("sans", 30)
        d.text((pw / 2 - f2.getlength(role) / 2, H - 215), role, font=f2, fill=C["text"])
        if a < 1:
            pa = np.asarray(panel).copy()
            pa[:, :, 3] = (255 * a)
            panel = Image.fromarray(pa)
        img.alpha_composite(panel, (i * pw + int(40 * (1 - a)), 0))
        ImageDraw.Draw(img).line([(i * pw, 0), (i * pw, H)], fill=(0, 0, 0), width=6)
    overlay_text(img, "Personagens fictícios · finalidade educativa", 42, 30, fade_in(t, 1.0), color=(200, 200, 210), serif=False)
    return cinematic(img)


def cena3(c):
    t, s = c.t, c.s
    if t < s[1]:
        world = bg("rua").copy().convert("RGBA")
        k = s[1] / 7.0  # tempos proporcionais à duração da fala
        xa = lerp(500, 980, ease(t / (3.0 * k)))
        walking = t < 3.0 * k
        char(CARLOS, 580, 1380, cen.GROUND, world, t=t, expr="smile", talk=(3.2 * k < t < 5.0 * k), look=-0.8, seed=2)
        char(ANA, 560, xa, cen.GROUND, world, t=t, walk=t * 5.5 if walking else None, expr="smile",
             talk=(5.2 * k < t < 6.8 * k), look=0.8)
        img = camera(world, 1180, 720, 1700).convert("RGBA")
        bubble(img, "Oi, Ana! Tudo bem?", 1330, 330, fade_in(t, 3.2 * k, 0.3) * (1 - fade_in(t, 5.0 * k, 0.3)))
        bubble(img, "Oi, Carlos!", 760, 330, fade_in(t, 5.2 * k, 0.3) * (1 - fade_in(t, 6.9 * k, 0.3)))
        return cinematic(img)
    tb = t - s[1]
    world = bg("sala").copy().convert("RGBA")
    d = ImageDraw.Draw(world)
    door_close = ease((tb - 2.2) / 1.2)
    t_try = s[2] - s[1] + 1.0  # Ana tenta abrir a porta
    jig = 8 * math.sin(tb * 30) if t_try + 1.2 < tb < t_try + 3.0 else 0
    cen.draw_door(d, 1 - door_close, jiggle=jig)
    # Carlos: vai até a porta, fecha, tranca e guarda a chave; depois se afasta
    if tb < 2.2:
        xc = lerp(1150, 1520, ease(tb / 2.2))
        char(CARLOS, 600, xc, cen.GROUND, world, t=t, walk=tb * 5 if tb < 2.1 else None, expr="neutral", seed=2)
    elif tb < 5.2:
        pose = ("down", "reach") if tb < 3.6 else ("down", "key")
        char(CARLOS, 600, 1520, cen.GROUND, world, t=t, arms=pose, expr="serious", prop="key", seed=2)
    else:
        xc = lerp(1520, 1080, ease((tb - 5.2) / 2.0))
        moving = tb < 7.1
        char(CARLOS, 600, xc, cen.GROUND, world, t=t, walk=tb * 5 if moving else None,
             arms=("down", "pocket"), expr="serious", look=0.8, seed=2)
    # Ana: fica preocupada e tenta sair
    if tb < t_try:
        char(ANA, 570, 760, cen.GROUND, world, t=t, expr="neutral" if tb < 3.6 else "worried", look=0.9)
    else:
        xa = lerp(760, 1480, ease((tb - t_try) / 1.2))
        arms = ("chest", "reach") if tb > t_try + 1.1 else ("down", "down")
        char(ANA, 570, xa, cen.GROUND, world, t=t, walk=(tb * 5.5) if tb < t_try + 1.2 else None,
             arms=arms, expr="worried", look=0.9)
    zoom = lerp(2100, 1650, ease((tb - t_try) / 6))
    img = camera(world, lerp(1100, 1380, ease((tb - t_try) / 4)), 720, zoom).convert("RGBA")
    if 3.6 < tb < 5.2:
        overlay_text(img, "a chave fica com Carlos", 170, 34, fade_in(tb, 3.6, 0.3) * (1 - fade_in(tb, 4.9, 0.3)),
                     color=(230, 230, 236), serif=False)
    stamp(img, "PRIVAÇÃO DA LIBERDADE", fade_in(tb, t_try + 2.4, 0.5))
    return cinematic(img)


def cena4(c):
    t, s = c.t, c.s
    img = legal_base("ART. 148 — CÓDIGO PENAL")
    d = ImageDraw.Draw(img)
    a = fade_in(t, 0.3)
    if a > 0:
        d.rounded_rectangle([140, 270, 1780, 450], radius=16, fill=C["panel2"])
        d.rectangle([140, 270, 150, 450], fill=C["gold"])
        d.text((190, 290), "CAPUT", font=font("sans_b", 26), fill=C["gold"])
        draw_rich(d, (190, 330), "“Privar alguém de sua liberdade, mediante sequestro ou cárcere privado:”", 46, 1560,
                  base="serif_i", hl="serif_b")
        d.rounded_rectangle([190, 385 + 10, 190 + 760, 385 + 50], radius=20, fill=C["blue"])
        d.text((210, 399), "Pena — reclusão, de 1 (um) a 3 (três) anos.", font=font("sans_b", 30), fill=(255, 255, 255))
    card(img, 140, 490, 780, 170, "Núcleo do tipo", "**Privar** alguém de sua liberdade", "gold", fade_in(t, s[1]))
    card(img, 140, 690, 780, 200, "Bem jurídico", "**Liberdade individual**, especialmente a **liberdade de locomoção**",
         "gold", fade_in(t, s[1] + 2.5))
    # mini-animação: caminha livre e é impedida
    a2 = fade_in(t, s[1] + 0.5)
    if a2 > 0:
        px0, py0, px1, py1 = 980, 490, 1780, 890
        panel = Image.new("RGBA", (px1 - px0, py1 - py0), C["panel"] + (255,))
        pd = ImageDraw.Draw(panel)
        pd.rectangle([0, 330, px1 - px0, py1 - py0], fill=(40, 58, 86))
        tt = t - (s[1] + 0.5)
        gate_x = 520
        gate = ease((tt - 3.0) / 0.8)
        x = min(lerp(60, 700, tt / 7.0), gate_x - 70) if gate > 0.2 else lerp(60, 700, tt / 7.0)
        walking = not (gate > 0.2 and x >= gate_x - 71)
        ci = draw_character(ANA, 280, t=t, walk=tt * 6 if walking else None, expr="smile" if gate < 0.2 else "worried",
                            look=0.7)
        paste_character(panel, ci, x, 350)
        gh = 300 * gate
        for k in range(6):
            pd.rectangle([gate_x + k * 22, 350 - gh, gate_x + k * 22 + 8, 350], fill=(180, 180, 190))
        if gate > 0.9:
            draw_lock(pd, gate_x + 160, 190, 50, "gold")
        f = font("sans_b", 28)
        lab = "livre para ir e vir" if gate < 0.2 else "liberdade interrompida"
        pd.text((30, 20), lab, font=f, fill=C["green"] if gate < 0.2 else C["wine"])
        pa = np.asarray(panel).copy()
        pa[:, :, 3] = (255 * a2)
        img.alpha_composite(Image.fromarray(pa), (px0, py0))
    return img.convert("RGB")


def cena5(c):
    t, s = c.t, c.s
    img = legal_base("SEQUESTRO ≠ CÁRCERE PRIVADO", "ART. 148 · MODALIDADES")
    pw, ph = 800, 470
    for i, (name, color, cap, when) in enumerate([
        ("SEQUESTRO", "blue", "Privação em sentido **mais amplo** — ex.: impedida de deixar uma propriedade", s[1]),
        ("CÁRCERE PRIVADO", "wine", "Restrição em espaço **mais delimitado** — ex.: quarto ou cômodo", s[2]),
    ]):
        x0 = 140 + i * (pw + 40)
        y0 = 270
        world = bg("sitio" if i == 0 else "quarto").copy().convert("RGBA")
        if i == 0:
            tt = t * 0.35
            xa = 1100 + 500 * math.sin(tt)
            walking = True
            char(ANA, 520, xa, 1120, world, t=t, walk=t * 5, expr="worried", look=math.cos(tt))
            if abs(math.cos(tt)) < 0.15:
                walking = False
            view = camera(world, 1200, 760, 2000)
        else:
            char(ANA, 560, 1000 + 60 * math.sin(t * 0.5), 1060, world, t=t, arms=("chest", "down"), expr="worried", seed=3)
            view = camera(world, 1104, 640, 2208)
        view = view.resize((pw, int(pw * 9 / 16))).convert("RGBA")
        img.alpha_composite(view, (x0, y0))
        d = ImageDraw.Draw(img)
        on = t >= when
        d.rectangle([x0, y0, x0 + pw, y0 + int(pw * 9 / 16)], outline=C[color] if on else (60, 76, 100), width=6 if on else 3)
        f = font("serif_b", 40)
        d.rounded_rectangle([x0 + pw / 2 - f.getlength(name) / 2 - 24, y0 - 28, x0 + pw / 2 + f.getlength(name) / 2 + 24, y0 + 32],
                            radius=12, fill=C[color])
        d.text((x0 + pw / 2 - f.getlength(name) / 2, y0 - 24), name, font=f, fill=(255, 255, 255))
        if on:
            card(img, x0, y0 + 470, pw, 150, "", cap, color, fade_in(t, when), size=32)
    banner(img, 140, 900, 1640, "Distinção doutrinária — **ambos estão no art. 148**, com a **mesma pena** (reclusão de 1 a 3 anos)",
           "gold", fade_in(t, s[3]), size=34)
    return img.convert("RGB")


def phone_ui(img, x, y, t, mode):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = 420, 760
    d.rounded_rectangle([x, y, x + w, y + h], radius=50, fill=(18, 18, 22, 255))
    d.rounded_rectangle([x + 16, y + 16, x + w - 16, y + h - 16], radius=38, fill=(236, 240, 244, 255))
    f, fb, fs = font("sans", 28), font("sans_b", 32), font("sans", 22)
    if mode == "chat":
        d.rectangle([x + 16, y + 60, x + w - 16, y + 140], fill=(40, 120, 100, 255))
        d.text((x + 40, y + 80), "Ana", font=fb, fill=(255, 255, 255, 255))
        msgs = [("Ana, chegou bem?", "19:40"), ("Me responde?", "20:55"), ("Tô preocupado!", "22:10")]
        for k, (m, hr) in enumerate(msgs):
            a = fade_in(t, 0.5 + k * 1.2, 0.4)
            if a <= 0:
                continue
            yy = y + 180 + k * 130
            d.rounded_rectangle([x + 70, yy, x + w - 36, yy + 100], radius=20, fill=(210, 246, 200, int(255 * a)))
            d.text((x + 90, yy + 14), m, font=f, fill=(30, 30, 30, int(255 * a)))
            d.text((x + w - 120, yy + 62), hr, font=fs, fill=(120, 120, 120, int(255 * a)))
        a = fade_in(t, 4.2, 0.4)
        if a > 0:
            d.text((x + 50, y + 600), "Sem resposta há horas", font=fb, fill=(190, 50, 60, int(255 * a)))
    else:
        d.text((x + w / 2 - fb.getlength("Ligando...") / 2, y + 150), "Ligando...", font=fb, fill=(60, 60, 70, 255))
        big = font("sans_b", 130)
        d.text((x + w / 2 - big.getlength("190") / 2, y + 240), "190", font=big, fill=(30, 60, 140, 255))
        d.text((x + w / 2 - f.getlength("Polícia Militar") / 2, y + 420), "Polícia Militar", font=f, fill=(60, 60, 70, 255))
        r = 60 + 8 * math.sin(t * 6)
        d.ellipse([x + w / 2 - r, y + 600 - r, x + w / 2 + r, y + 600 + r], fill=(40, 170, 90, 255))
    img.alpha_composite(ov)


def cena6(c):
    t, s = c.t, c.s
    world = bg("bruno").copy().convert("RGBA")
    calling = t >= s[1]
    char(BRUNO, 640, 820, 1110, world, t=t, arms=("down", "phone") if calling else ("chest", "down"),
         expr="worried", talk=calling and (t - s[1]) > 1.5, look=0.3 if not calling else -0.3, seed=5)
    img = camera(world, lerp(1000, 900, t / c.T), 700, lerp(2100, 1700, ease(t / c.T))).convert("RGBA")
    phone_ui(img, 1300, 170, t if not calling else t - s[1], "call" if calling else "chat")
    return cinematic(img)


def cena7(c):
    t, s = c.t, c.s
    if t < s[1]:
        world = bg("quarto").copy().convert("RGBA")
        char(ANA, 600, 900, 1080, world, t=t, arms=("chest", "down"), expr="worried", look=0.8, seed=4)
        img = camera(world, 1000, 680, lerp(2208, 1800, ease(t / s[1]))).convert("RGBA")
        overlay_text(img, "FORMAS QUALIFICADAS — ART. 148, § 1º E § 2º", 160, 56, fade_in(t, 0.8))
        return cinematic(img)
    img = legal_base("Formas qualificadas — art. 148, §§ 1º e 2º")
    incisos = [
        ("I", "vítima **ascendente, descendente, cônjuge ou companheiro** do agente, ou **maior de 60 anos**"),
        ("II", "**internação** da vítima em **casa de saúde ou hospital**"),
        ("III", "privação da liberdade por **mais de 15 dias**"),
        ("IV", "vítima **menor de 18 anos**"),
        ("V", "crime praticado com **fins libidinosos**"),
    ]
    d = ImageDraw.Draw(img)
    a = fade_in(t, s[1])
    if a > 0:
        d.rounded_rectangle([140, 262, 1030, 330], radius=14, fill=C["gold"])
        d.text((170, 274), "§ 1º — reclusão de 2 a 5 anos", font=font("sans_b", 38), fill=C["bg1"])
    seg = s[2] - s[1]
    for k, (n, txt) in enumerate(incisos):
        ak = fade_in(t, s[1] + 0.8 + k * seg / 6, 0.5)
        if ak <= 0:
            continue
        y = 350 + k * 118
        d.rounded_rectangle([140, y, 1030, y + 104], radius=12, fill=C["panel"])
        d.rounded_rectangle([140, y, 220, y + 104], radius=12, fill=C["gold"])
        fr = font("serif_b", 36)
        d.text((180 - fr.getlength(n) / 2, y + 30), n, font=fr, fill=C["bg1"])
        draw_rich(d, (245, y + 14 if rich_height(txt, 30, 760) > 50 else y + 32), txt, 30, 760)
    card(img, 1080, 262, 700, 330, "§ 2º — reclusão de 2 a 8 anos",
         "Se resulta à vítima, em razão de **maus-tratos** ou da **natureza da detenção**, **grave sofrimento físico ou moral**.",
         "wine", fade_in(t, s[2]), size=32)
    card(img, 1080, 620, 700, 330, "Atenção",
         "Finalidade de obter **vantagem**, como condição ou preço do resgate, **não está no art. 148**: é extorsão mediante sequestro (**art. 159**).",
         "blue", fade_in(t, s[3]), size=30)
    return img.convert("RGB")


def cena8(c):
    t, s = c.t, c.s
    img = legal_base("ATENÇÃO PARA A PROVA!", "QUALIFICADORA ≠ CAUSA DE AUMENTO ≠ CAUSA DE DIMINUIÇÃO")
    d = ImageDraw.Draw(img)
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    d.ellipse([1640, 120, 1760, 240], fill=(int(200 + 40 * pulse), 60, 60))
    d.text((1688, 132), "!", font=font("serif_b", 90), fill=(255, 255, 255))
    boxes = [
        ("QUALIFICADORA", "Fixa **novas penas mínima e máxima**.\n\nArt. 148: **§ 1º** (2 a 5 anos) e **§ 2º** (2 a 8 anos).", "gold", s[1]),
        ("CAUSA DE AUMENTO", "Aplica **fração** que aumenta a pena, na 3ª fase da dosimetria.\n\nO art. 148 **não prevê** causa de aumento própria.", "blue", s[1] + 3.0),
        ("CAUSA DE DIMINUIÇÃO", "Aplica **fração** que reduz a pena, na 3ª fase.\n\n**Sem minorante própria** no art. 148; causas gerais (ex.: tentativa, art. 14) vêm de outros dispositivos.", "green", s[2]),
    ]
    for k, (h, b, col, when) in enumerate(boxes):
        card(img, 140 + k * 560, 300, 520, 560, h, b, col, fade_in(t, when), size=32)
    return img.convert("RGB")


def cena9(c):
    t, s = c.t, c.s
    img = legal_base("CRIME HEDIONDO?", "LEI Nº 8.072/1990 · LEI DOS CRIMES HEDIONDOS")
    d = ImageDraw.Draw(img)
    # balança oscilando
    ang = 0.08 * math.sin(t * 0.9)
    cx, cy, sc = 420, 640, 170
    col = C["gold"]
    d.line([cx, cy - 1.1 * sc, cx, cy + 0.9 * sc], fill=col, width=10)
    d.polygon([(cx - 0.5 * sc, cy + 1.05 * sc), (cx + 0.5 * sc, cy + 1.05 * sc), (cx, cy + 0.8 * sc)], fill=col)
    for sgn in (-1, 1):
        bx = cx + sgn * sc * math.cos(ang)
        by = cy - 0.8 * sc + sgn * sc * math.sin(ang)
        d.line([cx, cy - 0.8 * sc, bx, by], fill=col, width=10)
        d.line([bx, by, bx - 0.35 * sc, by + 0.75 * sc], fill=col, width=4)
        d.line([bx, by, bx + 0.35 * sc, by + 0.75 * sc], fill=col, width=4)
        d.chord([bx - 0.45 * sc, by + 0.5 * sc, bx + 0.45 * sc, by + 1.0 * sc], 0, 180, fill=col)
    # documento da lei
    x0, y0 = 760, 270
    d.rounded_rectangle([x0, y0, 1780, 860], radius=10, fill=(244, 240, 228))
    d.text((x0 + 40, y0 + 30), "LEI Nº 8.072, DE 25 DE JULHO DE 1990", font=font("serif_b", 36), fill=(40, 40, 50))
    d.text((x0 + 40, y0 + 80), "Art. 1º São considerados hediondos os seguintes crimes (...):", font=font("serif_i", 28), fill=(60, 60, 70))
    for k in range(6):
        yy = y0 + 140 + k * 44
        d.rounded_rectangle([x0 + 40, yy, x0 + 40 + (820 if k % 2 else 900), yy + 20], radius=8, fill=(208, 204, 196))
    hl = fade_in(t, s[2], 0.6)
    yy = y0 + 400
    if hl > 0:
        d.rounded_rectangle([x0 + 24, yy - 12, 1760, yy + 150], radius=10, fill=(252, 226, 150))
    draw_rich(d, (x0 + 40, yy), "**XI** – sequestro e cárcere privado cometido contra **menor de 18 (dezoito) anos** "
                                "(art. 148, § 1º, inciso IV);", 32, 940, color=(40, 40, 50), hlcolor=(150, 40, 50),
              base="serif_i", hl="serif_b")
    d.text((x0 + 40, yy + 110), "Incluído pela Lei nº 14.811, de 2024", font=font("sans", 24), fill=(90, 90, 100))
    banner(img, 140, 880, 1640, "**Nem todo** sequestro ou cárcere privado é hediondo: depende da **hipótese prevista na Lei 8.072/1990**.",
           "gold", fade_in(t, s[0] + 3.0), size=32)
    return img.convert("RGB")


def cena10(c):
    t, s = c.t, c.s
    img = legal_base("Não confunda: arts. 146, 148 e 159", "DISTINÇÃO DE OUTROS CRIMES")
    d = ImageDraw.Draw(img)
    doors = [
        ("ART. 146", "Constrangimento ilegal", "Obrigar alguém, com violência ou grave ameaça, a **não fazer** o que a lei permite ou a **fazer** o que ela não manda\n**Detenção de 3 meses a 1 ano, ou multa**", "grey", s[0] + 3.0),
        ("ART. 148", "Sequestro e cárcere privado", "**Privar** alguém de sua **liberdade**\n**Reclusão de 1 a 3 anos** (caput)", "gold", s[1]),
        ("ART. 159", "Extorsão mediante sequestro", "Sequestrar com o **fim de obter vantagem**, como condição ou preço do resgate\n**Reclusão de 8 a 15 anos** · hediondo", "wine", s[2]),
    ]
    for k, (art, name, body, col, when) in enumerate(doors):
        x0 = 150 + k * 560
        y0, x1, y1 = 280, x0 + 500, 940
        c_ = C[col]
        d.rectangle([x0 - 14, y0 - 14, x1 + 14, y1], fill=(60, 70, 90))
        d.rectangle([x0, y0, x1, y1], fill=(250, 240, 214))
        op = ease((t - when) / 1.0)
        if op > 0:
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            tx = x0 + (x1 - x0) * 0.12 + 20
            nh = draw_rich(od, (tx, y0 + 120), name, 32, x1 - tx - 20, color=(40, 40, 50, int(255 * op)),
                           base="sans_b", hl="sans_b")
            draw_rich(od, (tx, y0 + 140 + nh), body, 29, x1 - tx - 20, color=(40, 40, 50, int(255 * op)), hlcolor=tuple(c_) + (int(255 * op),))
            img.alpha_composite(ov)
            d = ImageDraw.Draw(img)
        wdoor = (x1 - x0) * (1 - op * 0.88)
        d.rectangle([x0, y0, x0 + wdoor, y1], fill=(100, 70, 46))
        if wdoor > 60:
            d.ellipse([x0 + wdoor - 50, (y0 + y1) / 2 - 12, x0 + wdoor - 26, (y0 + y1) / 2 + 12], fill=C["gold"])
        # placa
        f = font("serif_b", 46)
        d.rounded_rectangle([x0 + 90, y0 + 24, x1 - 90, y0 + 96], radius=10, fill=c_)
        d.text((x0 + 250 - f.getlength(art) / 2, y0 + 32), art, font=f, fill=(255, 255, 255))
    return img.convert("RGB")


def cena11(c):
    t, s = c.t, c.s
    world = bg("fachada").copy().convert("RGBA")
    d = ImageDraw.Draw(world)
    cen.draw_police_car(d, 520, cen.GROUND + 20, t)
    fx0, fy0, fx1, fy1 = cen.FACHADA_DOOR
    open_door = ease((t - s[1]) / 1.0)
    d.rectangle([fx0, fy0, fx1, fy1], fill=(40, 28, 20))
    d.rectangle([fx0, fy0, fx0 + (fx1 - fx0) * (1 - open_door * 0.85), fy1], fill=(126, 84, 52))
    # Bruno e policial chegam
    xb = lerp(-100, 1040, ease(t / max(1.0, s[1])))
    xp = lerp(-300, 860, ease(t / max(1.0, s[1])))
    arriving = t < s[1] - 0.2
    char(POLICIAL, 590, xp, cen.GROUND, world, t=t, walk=t * 5 if arriving else None, seed=7)
    ana_out = t >= s[1] + 0.8
    char(BRUNO, 600, xb, cen.GROUND, world, t=t, walk=t * 5.2 if arriving else None,
         expr="relief" if ana_out else "worried", arms=("down", "open") if ana_out else ("down", "down"), seed=5)
    if ana_out:
        xa = lerp(1410, 1240, ease((t - s[1] - 0.8) / 1.6))
        char(ANA, 570, xa, cen.GROUND, world, t=t, walk=(t * 5) if t < s[1] + 2.4 else None, expr="relief",
             arms=("down", "down"), look=-0.8)
    if t >= s[2]:
        # Carlos é abordado de forma calma, ao lado de outro policial; sem confronto
        a = ease((t - s[2]) / 1.0)
        char(CARLOS, 600, lerp(1410, 1620, a), cen.GROUND, world, t=t, expr="serious", arms=("down", "down"), look=0.5, seed=2)
        char(POLICIAL, 590, 1830, cen.GROUND, world, t=t, arms=("down", "down"), look=-0.8, seed=9)
    img = camera(world, lerp(900, 1250, ease(t / c.T)), 720, lerp(2000, 2208, ease((t - s[2]) / 4))).convert("RGBA")
    return cinematic(img)


def cena12(c):
    t, s = c.t, c.s
    img = legal_base("ART. 148 — PONTOS IMPORTANTES", "RESUMO")
    for k, (spec, x) in enumerate(((BRUNO, 270), (ANA, 470), (CARLOS, 670))):
        ci = draw_character(spec, 560, t=t, expr="smile" if spec is not CARLOS else "neutral", seed=k,
                            arms=("down", "down"))
        paste_character(img, ci, x, 960)
    items = [
        "Protege a **liberdade individual**",
        "Consiste em **privar alguém de sua liberdade**",
        "Abrange **sequestro e cárcere privado**",
        "Possui hipóteses com **penas mais graves** (§§ 1º e 2º)",
        "Diferencia-se do **constrangimento ilegal** (art. 146)",
        "Diferencia-se da **extorsão mediante sequestro** (art. 159)",
        "Hediondez depende da **hipótese prevista na Lei 8.072/1990**",
    ]
    d = ImageDraw.Draw(img)
    span = max(1.0, (s[1] + 1.5) / len(items))
    for k, it in enumerate(items):
        a = fade_in(t, 0.5 + k * span, 0.4)
        if a <= 0:
            continue
        y = 270 + k * 96
        d.line([(900, y + 26), (914, y + 42), (940, y + 12)], fill=C["green"], width=7)
        draw_rich(d, (965, y + 4), it, 32, 860)
    return img.convert("RGB")


def cena13(c):
    t, T = c.t, c.T
    world = bg("rua_noite").copy().convert("RGBA")
    for k, (spec, x) in enumerate(((BRUNO, 850), (ANA, 1110), (CARLOS, 1370))):
        char(spec, 580, x, cen.GROUND, world, t=t, expr="neutral" if spec is CARLOS else "smile", seed=k)
    img = camera(world, 1104, 700, lerp(1700, 2208, ease(t / (T * 0.8)))).convert("RGBA")
    overlay_text(img, "ART. 148 DO CÓDIGO PENAL", 140, 64, fade_in(t, 0.5) * (1 - fade_in(t, T - 4.5)))
    overlay_text(img, "SEQUESTRO E CÁRCERE PRIVADO", 220, 46, fade_in(t, 1.3) * (1 - fade_in(t, T - 4.5)), color=(240, 236, 226))
    overlay_text(img, "Direito Penal — Estudo de caso", 880, 44, fade_in(t, 4.5) * (1 - fade_in(t, T - 4.5)),
                 color=(240, 236, 226), serif=False)
    end = fade_in(t, T - 4.0, 1.2)
    if end > 0:
        ov = Image.new("RGBA", img.size, (8, 10, 16, int(255 * end)))
        img.alpha_composite(ov)
        d = ImageDraw.Draw(img)
        g = tuple(int(v * end) for v in C["gold"])
        draw_scale(d, W // 2, H // 2 - 40, 90, g)
        f = font("sans", 26)
        txt = "História fictícia · finalidade exclusivamente educativa"
        d.text((W / 2 - f.getlength(txt) / 2, H // 2 + 120), txt, font=f, fill=tuple(int(v * end) for v in C["muted"]))
    return cinematic(img)


SCENES = [
    dict(fn=cena1, min=14, segs=[
        "Você sabe o que acontece quando alguém impede outra pessoa de exercer livremente o seu direito de ir e vir?",
        "O artigo cento e quarenta e oito do Código Penal trata justamente do crime de sequestro e cárcere privado."]),
    dict(fn=cena2, min=10, segs=[
        "Para entender melhor o artigo cento e quarenta e oito, vamos acompanhar uma situação fictícia envolvendo Ana, Carlos e Bruno."]),
    dict(fn=cena3, min=25, segs=[
        "Certo dia, Ana encontra Carlos, um conhecido, e os dois conversam normalmente.",
        "Carlos leva Ana até uma casa. Lá dentro, fecha a porta e guarda a chave.",
        "Em determinado momento, Carlos impede Ana de deixar o local contra a sua vontade. Ana não pode sair livremente, "
        "e percebe que sua liberdade de locomoção foi restringida.",
        "Essa conduta pode caracterizar o crime previsto no artigo cento e quarenta e oito do Código Penal."]),
    dict(fn=cena4, min=20, segs=[
        "Diz o artigo: privar alguém de sua liberdade, mediante sequestro ou cárcere privado. A pena é de reclusão, de um a três anos.",
        "O núcleo do crime é simples: privar alguém de sua liberdade. O bem jurídico protegido é principalmente a liberdade "
        "individual, especialmente a liberdade de locomoção."]),
    dict(fn=cena5, min=25, segs=[
        "Mas qual é a diferença entre sequestro e cárcere privado? Tradicionalmente, a doutrina diferencia as duas modalidades "
        "pela forma da privação da liberdade.",
        "Sequestro representa uma privação da liberdade em sentido mais amplo, como impedir alguém de deixar uma propriedade.",
        "Já o cárcere privado normalmente envolve uma restrição em espaço mais delimitado, como um quarto ou cômodo.",
        "Apesar da distinção doutrinária, ambos estão previstos no artigo cento e quarenta e oito, com a mesma pena."]),
    dict(fn=cena6, min=15, segs=[
        "Enquanto isso, Bruno percebe que Ana não responde às mensagens nem às ligações, algo incomum para ela.",
        "Bruno percebe que existe algo errado e procura ajuda. Ele liga para a polícia e relata o que sabe."]),
    dict(fn=cena7, min=32, segs=[
        "O artigo cento e quarenta e oito prevê situações em que a conduta recebe tratamento penal mais grave. "
        "Por isso, é fundamental analisar as circunstâncias concretas do caso.",
        "Pelo parágrafo primeiro, a pena é de dois a cinco anos quando a vítima é ascendente, descendente, cônjuge ou "
        "companheiro do agente, ou maior de sessenta anos; quando há internação em casa de saúde ou hospital; quando a "
        "privação dura mais de quinze dias; quando a vítima é menor de dezoito anos; ou quando há fins libidinosos.",
        "Pelo parágrafo segundo, a pena é de dois a oito anos se resulta à vítima, por maus-tratos ou pela natureza da "
        "detenção, grave sofrimento físico ou moral.",
        "Atenção: a finalidade de obter vantagem como condição ou preço do resgate não está no artigo cento e quarenta e oito. "
        "Ela caracteriza a extorsão mediante sequestro, do artigo cento e cinquenta e nove."]),
    dict(fn=cena8, min=18, segs=[
        "Atenção para a prova! Não devemos confundir qualificadoras com causas de aumento ou diminuição de pena.",
        "Nas hipóteses do próprio artigo cento e quarenta e oito, a lei estabelece novas penas mínima e máxima: são "
        "qualificadoras. Causas de aumento e de diminuição aplicam frações sobre a pena.",
        "O artigo cento e quarenta e oito não prevê causa de aumento nem de diminuição própria. As causas gerais devem ser "
        "analisadas conforme outros dispositivos eventualmente aplicáveis."]),
    dict(fn=cena9, min=22, segs=[
        "Outro ponto importante é a hediondez. Não devemos afirmar que todo e qualquer sequestro ou cárcere privado "
        "possui automaticamente natureza hedionda.",
        "É necessário verificar a modalidade concreta e a hipótese prevista na Lei dos Crimes Hediondos, considerando a "
        "redação vigente da legislação.",
        "Hoje, desde a Lei catorze mil, oitocentos e onze, de dois mil e vinte e quatro, é hediondo o sequestro e cárcere "
        "privado cometido contra menor de dezoito anos, previsto no parágrafo primeiro, inciso quarto."]),
    dict(fn=cena10, min=18, segs=[
        "Também é importante não confundir o artigo cento e quarenta e oito com outros crimes. O constrangimento ilegal "
        "está previsto no artigo cento e quarenta e seis.",
        "O artigo cento e quarenta e oito trata da privação da liberdade.",
        "Já a extorsão mediante sequestro, prevista no artigo cento e cinquenta e nove, possui elementos próprios: o agente "
        "sequestra com o fim de obter vantagem, como condição ou preço do resgate."]),
    dict(fn=cena11, min=18, segs=[
        "Bruno consegue acionar as autoridades, que localizam a casa.",
        "No caso fictício que acompanhamos, Ana recupera sua liberdade, e os fatos passam a ser analisados pelas "
        "autoridades competentes.",
        "Para definir corretamente o crime, é necessário observar todas as circunstâncias da situação concreta."]),
    dict(fn=cena12, min=20, segs=[
        "Em resumo: o artigo cento e quarenta e oito protege a liberdade individual e pune a privação da liberdade de outra pessoa.",
        "Para compreender corretamente o crime, é necessário analisar a conduta, as circunstâncias, a duração da privação "
        "e as características da vítima."]),
    dict(fn=cena13, min=11, segs=[
        "Conhecer o artigo é importante. Saber aplicá-lo ao caso concreto é essencial."]),
]


# ---------------------------------------------------------------- áudio
def synth(text, voice, path, length_scale):
    subprocess.run(["piper", "-m", voice, "-f", path, "--length-scale", str(length_scale), "--sentence-silence", "0.2"],
                   input=text.encode("utf-8"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = int(len(data) * SR / sr)
    return np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data).astype(np.float32)


def music(n):
    """Trilha discreta: pad em lá menor (Am–F–C–G), sons senoidais suaves."""
    t = np.arange(n) / SR
    chords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (130.81, 164.81, 196.0), (98.0, 123.47, 146.83)]
    out = np.zeros(n, np.float32)
    dur = 8.0
    for k in range(int(n / SR / dur) + 2):
        t0 = k * dur
        i0, i1 = int(max(0, (t0 - 1.5) * SR)), int(min(n, (t0 + dur + 1.5) * SR))
        if i0 >= i1:
            continue
        tt = t[i0:i1] - t0
        env = np.clip((tt + 1.5) / 2.5, 0, 1) * np.clip((dur + 1.5 - tt) / 2.5, 0, 1)
        for f in chords[k % 4]:
            for mul, amp in ((1, 1.0), (2, 0.25), (0.5, 0.5)):
                out[i0:i1] += amp * env * np.sin(2 * np.pi * f * mul * t[i0:i1] + mul) * 0.5
                out[i0:i1] += amp * env * np.sin(2 * np.pi * f * mul * 1.003 * t[i0:i1]) * 0.5
    out /= np.max(np.abs(out)) + 1e-6
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * t / 11)
    return out * lfo * 0.09


# ---------------------------------------------------------------- legendas
def chunk_text(text, maxc=62):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > maxc and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
        if cur.endswith((".", "?", "!", ":", ";")) and len(cur) > 28:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def subtitles_display(text):
    """Legenda com números como na lei (a narração usa números por extenso)."""
    rep = [("artigo cento e quarenta e oito", "artigo 148"), ("artigo cento e quarenta e seis", "artigo 146"),
           ("artigo cento e cinquenta e nove", "artigo 159"), ("Lei catorze mil, oitocentos e onze, de dois mil e vinte e quatro", "Lei 14.811/2024"),
           ("parágrafo primeiro, inciso quarto", "§ 1º, inciso IV"), ("parágrafo primeiro", "§ 1º"), ("parágrafo segundo", "§ 2º"),
           ("dois a cinco anos", "2 a 5 anos"), ("dois a oito anos", "2 a 8 anos"), ("um a três anos", "1 a 3 anos"),
           ("sessenta anos", "60 anos"), ("quinze dias", "15 dias"), ("dezoito anos", "18 anos")]
    for a, b in rep:
        text = text.replace(a, b).replace(a[0].upper() + a[1:], b[0].upper() + b[1:])
    return text


def draw_subtitle(img, text):
    f = font("sans", 36)
    tw = f.getlength(text)
    d = ImageDraw.Draw(img)
    y = H - BAR + 38
    d.rounded_rectangle([W / 2 - tw / 2 - 20, y - 8, W / 2 + tw / 2 + 20, y + 50], radius=10, fill=(0, 0, 0))
    d.text((W / 2 - tw / 2, y), text, font=f, fill=(250, 250, 250))


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="art148_estudo_de_caso.mp4")
    ap.add_argument("--length-scale", type=float, default=0.84)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", type=int, default=None, help="renderiza só a cena N (1..13)")
    args = ap.parse_args()
    tmp = tempfile.mkdtemp()

    # 1) narração e linha do tempo
    lead, gap = 0.5, 0.35
    timeline, voice_parts, subs = [], [], []
    tcur = 0.0
    for si, sc in enumerate(SCENES):
        if args.only and si + 1 != args.only:
            continue
        starts, t_local = [], lead
        clips = []
        for gi, text in enumerate(sc["segs"]):
            a = synth(text, args.voice, os.path.join(tmp, f"{si}_{gi}.wav"), args.length_scale)
            starts.append(t_local - 0.2 if gi else 0.0)
            clips.append((t_local, a, text))
            t_local += len(a) / SR + gap
        T = max(sc["min"], t_local + 0.8)
        T = round(T * FPS) / FPS
        timeline.append(dict(si=si, T=T, starts=starts, t0=tcur))
        for (ts, a, text) in clips:
            voice_parts.append((tcur + ts, a))
            pieces = chunk_text(subtitles_display(text))
            total = sum(len(p) for p in pieces)
            acc = 0.0
            dur = len(a) / SR
            for p in pieces:
                st = tcur + ts + dur * acc / total
                acc += len(p)
                subs.append((st, tcur + ts + dur * acc / total, p))
        tcur += T
    total = tcur
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for (ts, a) in voice_parts:
        i = int(ts * SR)
        voice[i:i + len(a)] += a
    env = np.convolve((np.abs(voice) > 0.02).astype(np.float32), np.ones(int(0.4 * SR)) / (0.4 * SR), mode="same")
    mix = voice * 0.95 + music(n) * (1 - 0.55 * np.clip(env * 3, 0, 1))
    fade = np.clip(np.minimum(np.arange(n), n - np.arange(n)) / (2.0 * SR), 0, 1)
    mix = np.clip(mix * fade, -1, 1)
    wav_path = os.path.join(tmp, "mix.wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print(f"Duração total: {total / 60:.2f} min")

    base = os.path.splitext(args.out)[0]
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for i, (a, b, p) in enumerate(subs, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{p}\n\n")

    if args.preview:
        os.makedirs("preview", exist_ok=True)
        for tl in timeline:
            sc = SCENES[tl["si"]]
            for k, frac in enumerate((0.15, 0.5, 0.9)):
                t = tl["T"] * frac
                sc["fn"](Ctx(t, tl["T"], tl["starts"])).save(f"preview/c{tl['si'] + 1:02d}_{k}.png")
        return

    # 2) vídeo
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium",
                             "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                             "-movflags", "+faststart", "-shortest", args.out], stdin=subprocess.PIPE)
    prev = None
    si_sub = 0
    for tl in timeline:
        sc = SCENES[tl["si"]]
        nf = int(round(tl["T"] * FPS))
        print(f"cena {tl['si'] + 1}: {tl['T']:.1f}s", flush=True)
        for k in range(nf):
            t = k / FPS
            img = sc["fn"](Ctx(t, tl["T"], tl["starts"]))
            gt = tl["t0"] + t
            while si_sub < len(subs) and subs[si_sub][1] < gt:
                si_sub += 1
            if si_sub < len(subs) and subs[si_sub][0] <= gt <= subs[si_sub][1]:
                draw_subtitle(img, subs[si_sub][2])
            arr = np.asarray(img)
            if prev is not None and k < 18:
                a = (k + 1) / 19
                arr = (prev.astype(np.float32) * (1 - a) + arr.astype(np.float32) * a).astype(np.uint8)
            proc.stdin.write(arr.tobytes())
            if k == nf - 1:
                prev = arr
    proc.stdin.close()
    proc.wait()
    print("OK:", args.out)


if __name__ == "__main__":
    main()
