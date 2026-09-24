# -*- coding: utf-8 -*-
"""Gera o vídeo educativo sobre o art. 148 do CP a partir de roteiro.py.

Requisitos: pillow, numpy, piper-tts (voz pt-BR), imageio-ffmpeg.
Uso: python3 gerar_video.py --voice /caminho/pt-br-edresson-low.onnx --out art148.mp4
"""
import argparse
import math
import os
import subprocess
import tempfile
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from roteiro import SCENES

W, H, FPS = 1920, 1080, 30
MARGIN = 140
C = dict(
    bg1=(12, 22, 37), bg2=(22, 38, 60), text=(237, 232, 220), muted=(150, 162, 182),
    gold=(201, 162, 39), blue=(86, 132, 186), wine=(170, 66, 78), green=(94, 156, 118),
    grey=(128, 138, 154), panel=(28, 44, 68), panel2=(34, 52, 80),
)
FONTDIR = "/usr/share/fonts/truetype"
F = {
    "serif_b": f"{FONTDIR}/liberation/LiberationSerif-Bold.ttf",
    "serif_i": f"{FONTDIR}/liberation/LiberationSerif-Italic.ttf",
    "sans": f"{FONTDIR}/liberation/LiberationSans-Regular.ttf",
    "sans_b": f"{FONTDIR}/liberation/LiberationSans-Bold.ttf",
}
_fcache = {}


def font(name, size):
    key = (name, size)
    if key not in _fcache:
        _fcache[key] = ImageFont.truetype(F[name], size)
    return _fcache[key]


def col(name):
    return C[name] if isinstance(name, str) else name


# ---------------------------------------------------------------- texto rico
def tokens(text):
    """Divide texto com **destaques** em palavras (palavra, destacado, quebra_de_linha)."""
    out, bold, prev_part = [], False, ""
    for i, part in enumerate(text.split("**")):
        if i > 0:
            bold = not bold
        joined = i > 0 and prev_part and not prev_part[-1].isspace()
        prev_part = part
        for li, line in enumerate(part.split("\n")):
            if li > 0:
                out.append(("\n", bold, False))
            for wi, w in enumerate(line.split(" ")):
                if w:
                    # pontuação colada ao destaque anterior não recebe espaço
                    glue = bool(joined) and li == 0 and wi == 0 and bool(out) and out[-1][0] != "\n"
                    out.append((w, bold, glue))
    return out


def layout_rich(text, size, maxw, base="sans", hl="sans_b"):
    """Retorna linhas: lista de [(x, palavra, destacado)] e altura de linha."""
    fn, fb = font(base, size), font(hl, size)
    space = fn.getlength(" ")
    lines, cur, x = [], [], 0
    for w, b, glue in tokens(text):
        if w == "\n":
            lines.append(cur)
            cur, x = [], 0
            continue
        wl = (fb if b else fn).getlength(w)
        if glue and cur:
            x -= space
        elif cur and x + wl > maxw:
            lines.append(cur)
            cur, x = [], 0
        cur.append((x, w, b))
        x += wl + space
    if cur:
        lines.append(cur)
    return lines, int(size * 1.32)


def draw_rich(d, xy, text, size, maxw, color="text", hlcolor="gold", base="sans", hl="sans_b"):
    lines, lh = layout_rich(text, size, maxw, base, hl)
    x0, y = xy
    for line in lines:
        for x, w, b in line:
            d.text((x0 + x, y), w, font=font(hl if b else base, size), fill=col(hlcolor if b else color))
        y += lh
    return len(lines) * lh


def rich_height(text, size, maxw, base="sans", hl="sans_b"):
    lines, lh = layout_rich(text, size, maxw, base, hl)
    return len(lines) * lh


# ---------------------------------------------------------------- fundo
def make_background():
    img = Image.new("RGB", (W, H))
    arr = np.zeros((H, W, 3), dtype=np.float32)
    t = np.linspace(0, 1, H)[:, None]
    for i in range(3):
        arr[:, :, i] = C["bg1"][i] * (1 - t) + C["bg2"][i] * t
    img = Image.fromarray(arr.astype(np.uint8))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # colunas clássicas discretas (tribunal) à direita
    for k, cx in enumerate((1640, 1760, 1880)):
        a = 14
        d.rectangle([cx - 30, 260, cx + 30, 1000], fill=(255, 255, 255, a))
        d.rectangle([cx - 44, 236, cx + 44, 260], fill=(255, 255, 255, a))
        d.rectangle([cx - 44, 1000, cx + 44, 1024], fill=(255, 255, 255, a))
        for fx in range(-18, 19, 12):
            d.line([cx + fx, 270, cx + fx, 990], fill=(0, 0, 0, 18), width=3)
    d.polygon([(1560, 236), (1760, 150), (1960, 236)], fill=(255, 255, 255, 12))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img


def draw_scale(d, cx, cy, s, color):
    """Balança da Justiça estilizada."""
    c = col(color)
    lw = max(3, int(s * 0.04))
    d.line([cx, cy - s * 0.9, cx, cy + s * 0.75], fill=c, width=lw)
    d.polygon([(cx - s * 0.35, cy + s * 0.9), (cx + s * 0.35, cy + s * 0.9), (cx, cy + s * 0.7)], fill=c)
    d.ellipse([cx - s * 0.08, cy - s * 1.0, cx + s * 0.08, cy - s * 0.84], fill=c)
    d.line([cx - s, cy - s * 0.7, cx + s, cy - s * 0.7], fill=c, width=lw)
    for sx in (-1, 1):
        px = cx + sx * s
        d.line([px, cy - s * 0.7, px - s * 0.3, cy], fill=c, width=max(2, lw // 2))
        d.line([px, cy - s * 0.7, px + s * 0.3, cy], fill=c, width=max(2, lw // 2))
        d.chord([px - s * 0.36, cy - s * 0.2, px + s * 0.36, cy + s * 0.2], 0, 180, fill=c)


def draw_person(d, cx, cy, s, color):
    """Figura humana neutra (cabeça + tronco)."""
    c = col(color)
    d.ellipse([cx - s * 0.22, cy - s * 1.0, cx + s * 0.22, cy - s * 0.56], fill=c)
    d.rounded_rectangle([cx - s * 0.32, cy - s * 0.5, cx + s * 0.32, cy + s * 0.3], radius=int(s * 0.18), fill=c)


def draw_lock(d, cx, cy, s, color):
    c = col(color)
    d.arc([cx - s * 0.32, cy - s * 0.75, cx + s * 0.32, cy - s * 0.05], 180, 360, fill=c, width=max(3, int(s * 0.12)))
    d.line([cx - s * 0.32 + s * 0.05, cy - s * 0.4, cx - s * 0.32 + s * 0.05, cy - s * 0.1], fill=c, width=max(3, int(s * 0.12)))
    d.line([cx + s * 0.32 - s * 0.05, cy - s * 0.4, cx + s * 0.32 - s * 0.05, cy - s * 0.1], fill=c, width=max(3, int(s * 0.12)))
    d.rounded_rectangle([cx - s * 0.48, cy - s * 0.15, cx + s * 0.48, cy + s * 0.55], radius=int(s * 0.1), fill=c)
    d.ellipse([cx - s * 0.08, cy + s * 0.08, cx + s * 0.08, cy + s * 0.24], fill=C["bg1"])


# ---------------------------------------------------------------- moldura comum
def chrome(img, scene, progress):
    d = ImageDraw.Draw(img)
    d.text((MARGIN, 44), "ART. 148  ·  CÓDIGO PENAL BRASILEIRO", font=font("sans_b", 24), fill=C["gold"])
    label = f"{scene['sec']} / 11   ·   {scene['secname'].upper()}"
    fl = font("sans", 24)
    d.text((W - MARGIN - fl.getlength(label), 44), label, font=fl, fill=C["muted"])
    d.line([MARGIN, 86, W - MARGIN, 86], fill=(60, 76, 100), width=2)
    d.text((MARGIN, H - 58), "Decreto-Lei nº 2.848/1940 (Código Penal) · Lei nº 8.072/1990 · exemplos fictícios",
           font=font("sans", 22), fill=C["muted"])
    d.rectangle([0, H - 8, W, H], fill=(40, 56, 80))
    d.rectangle([0, H - 8, int(W * progress), H], fill=C["gold"])


def title_block(d, text):
    f = font("serif_b", 62)
    d.text((MARGIN, 118), text, font=f, fill=C["text"])
    d.rectangle([MARGIN, 208, MARGIN + 120, 214], fill=C["gold"])


# ---------------------------------------------------------------- itens
CONTENT_W = W - 2 * MARGIN


def card_size(card, w):
    pad = 30
    hh = rich_height(card["head"], 34, w - 2 * pad - 12, "sans_b", "sans_b")
    bh = rich_height(card["body"], 32, w - 2 * pad - 12)
    return hh + 14 + bh + 2 * pad


def draw_card(img, d, x, y, w, h, card, visible):
    if not visible:
        return
    pad = 30
    c = col(card.get("color", "gold"))
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=C["panel"])
    d.rounded_rectangle([x, y, x + 10, y + h], radius=4, fill=c)
    hh = draw_rich(d, (x + pad + 12, y + pad), card["head"], 34, w - 2 * pad - 12, color=c, hlcolor=c,
                   base="sans_b", hl="sans_b")
    draw_rich(d, (x + pad + 12, y + pad + hh + 14), card["body"], 32, w - 2 * pad - 12)


def item_height(it):
    t = it["t"]
    if t == "bullet" or t == "check":
        return rich_height(it["text"], 38, CONTENT_W - 70) + 8
    if t == "inciso":
        return max(76, rich_height(it["text"], 36, CONTENT_W - 150) + 20)
    if t == "quote":
        return rich_height(it["text"], 44, CONTENT_W - 110, "serif_i", "serif_b") + 100
    if t == "penalty":
        return 84
    if t == "card":
        return card_size(it, CONTENT_W)
    if t == "row":
        n = len(it["cards"])
        cw = (CONTENT_W - 30 * (n - 1)) // n
        return max(card_size(c, cw) for c in it["cards"])
    if t == "banner":
        size = 42 if it.get("big") else 34
        return rich_height(it["text"], size, CONTENT_W - 100) + 56
    if t == "table":
        return 70 * len(it["rows"])
    raise ValueError(t)


def draw_item(img, d, it, y, step):
    t = it["t"]
    vis = it["step"] <= step
    x = MARGIN
    if t in ("bullet", "check"):
        if not vis:
            return
        c = col(it.get("color", "gold"))
        if t == "bullet":
            d.rectangle([x + 4, y + 18, x + 20, y + 34], fill=c)
        else:
            d.line([(x, y + 26), (x + 12, y + 40), (x + 34, y + 12)], fill=C["green"], width=6)
        draw_rich(d, (x + 60, y), it["text"], 38, CONTENT_W - 70)
    elif t == "inciso":
        if not vis:
            return
        h = item_height(it)
        d.rounded_rectangle([x, y, x + CONTENT_W, y + h - 12], radius=12, fill=C["panel"])
        d.rounded_rectangle([x, y, x + 110, y + h - 12], radius=12, fill=C["gold"])
        fr = font("serif_b", 40)
        d.text((x + 55 - fr.getlength(it["num"]) / 2, y + (h - 12) / 2 - 24), it["num"], font=fr, fill=C["bg1"])
        th = rich_height(it["text"], 36, CONTENT_W - 150)
        draw_rich(d, (x + 140, y + (h - 12 - th) / 2 + 2), it["text"], 36, CONTENT_W - 150)
    elif t == "quote":
        if not vis:
            return
        h = item_height(it)
        c = col(it.get("color", "gold"))
        d.rounded_rectangle([x, y, x + CONTENT_W, y + h - 16], radius=14, fill=C["panel2"])
        d.rectangle([x, y, x + 8, y + h - 16], fill=c)
        d.text((x + 50, y + 20), it["label"].upper(), font=font("sans_b", 24), fill=c)
        draw_rich(d, (x + 50, y + 60), "“" + it["text"] + "”", 44, CONTENT_W - 110, base="serif_i", hl="serif_b")
    elif t == "penalty":
        if not vis:
            return
        c = col(it["color"])
        f = font("sans_b", 40)
        tw = f.getlength(it["text"])
        d.rounded_rectangle([x, y, x + tw + 60, y + 70], radius=35, fill=c)
        d.text((x + 30, y + 13), it["text"], font=f, fill=(255, 255, 255))
    elif t == "card":
        draw_card(img, d, x, y, CONTENT_W, item_height(it), it, vis)
    elif t == "row":
        n = len(it["cards"])
        cw = (CONTENT_W - 30 * (n - 1)) // n
        h = item_height(it)
        for i, c in enumerate(it["cards"]):
            draw_card(img, d, x + i * (cw + 30), y, cw, h, c, c.get("step", it["step"]) <= step)
    elif t == "banner":
        if not vis:
            return
        h = item_height(it)
        c = col(it["color"])
        d.rounded_rectangle([x, y, x + CONTENT_W, y + h], radius=16, outline=c, width=4, fill=C["bg1"])
        size = 42 if it.get("big") else 34
        draw_rich(d, (x + 50, y + 28), it["text"], size, CONTENT_W - 100, hlcolor=it["color"])
    elif t == "table":
        if not vis:
            return
        rh = 70
        kw = 520
        for i, (k, v) in enumerate(it["rows"]):
            yy = y + i * rh
            d.rectangle([x, yy, x + CONTENT_W, yy + rh - 4], fill=C["panel"] if i % 2 == 0 else C["panel2"])
            d.rectangle([x, yy, x + kw, yy + rh - 4], fill=(44, 62, 92))
            d.text((x + 30, yy + 16), k, font=font("sans_b", 32), fill=C["gold"])
            d.text((x + kw + 30, yy + 16), v, font=font("sans", 32), fill=C["text"])


def render_standard(bg, scene, step, progress):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    chrome(img, scene, progress)
    title_block(d, scene["title"])
    items = scene["items"]
    heights = [item_height(it) for it in items]
    gap = 26
    total = sum(heights) + gap * (len(items) - 1)
    top, bottom = 250, H - 90
    y = top + max(0, (bottom - top - total) // 2) if total < (bottom - top) else top
    if total > bottom - top:
        raise ValueError(f"Conteúdo excede a tela em '{scene['title']}': {total}px")
    for it, h in zip(items, heights):
        draw_item(img, d, it, y, step)
        y += h + gap
    return img


def render_title(bg, scene, step, progress):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 8, int(W * progress), H], fill=C["gold"])
    draw_scale(d, W // 2, 230, 110, "gold")
    f1 = font("serif_b", 150)
    t1 = "Art. 148"
    d.text(((W - f1.getlength(t1)) / 2, 350), t1, font=f1, fill=C["gold"])
    f2 = font("sans", 40)
    t2 = "CÓDIGO PENAL BRASILEIRO  ·  DECRETO-LEI Nº 2.848/1940"
    d.text(((W - f2.getlength(t2)) / 2, 530), t2, font=f2, fill=C["muted"])
    f3 = font("serif_b", 84)
    t3 = "Sequestro e Cárcere Privado"
    d.text(((W - f3.getlength(t3)) / 2, 600), t3, font=f3, fill=C["text"])
    if step >= 2:
        topics = ["Conceito", "Sequestro x Cárcere", "Qualificadoras", "Hediondez", "Distinções"]
        fs = font("sans_b", 32)
        widths = [fs.getlength(t) + 60 for t in topics]
        x = (W - (sum(widths) + 24 * (len(topics) - 1))) / 2
        for t, w in zip(topics, widths):
            d.rounded_rectangle([x, 780, x + w, 846], radius=33, outline=C["gold"], width=3)
            d.text((x + 30, 794), t, font=fs, fill=C["text"])
            x += w + 24
    return img


def render_end(bg, scene, step, progress):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 8, int(W * progress), H], fill=C["gold"])
    draw_scale(d, W // 2, 200, 80, "gold")
    f = font("serif_b", 96)
    t = "Bons estudos!"
    d.text(((W - f.getlength(t)) / 2, 300), t, font=f, fill=C["text"])
    refs = [
        "Referências",
        "Código Penal (Decreto-Lei nº 2.848/1940): arts. 14, 65, 68, 83, 146, 148 e 159",
        "Lei nº 8.072/1990 (Crimes Hediondos): art. 1º, XI, e art. 2º — inciso XI incluído pela Lei nº 14.811/2024",
        "Lei nº 7.210/1984 (Execução Penal): art. 112",
        "Conteúdo educativo · exemplos fictícios · confira sempre a redação vigente no Planalto",
    ]
    y = 470
    for i, r in enumerate(refs):
        fr = font("sans_b" if i == 0 else "sans", 36 if i == 0 else 30)
        d.text(((W - fr.getlength(r)) / 2, y), r, font=fr, fill=C["gold"] if i == 0 else (C["muted"] if i == 4 else C["text"]))
        y += 70 if i == 0 else 56
    return img


# ------------------------------------------------ animação sequestro x cárcere
def render_compare_base(bg, scene, step, progress):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    chrome(img, scene, progress)
    title_block(d, scene["title"])
    pw = (CONTENT_W - 40) // 2
    for i, (head, color, cap) in enumerate([
        ("SEQUESTRO", "blue", "Privação em sentido **mais amplo**: a vítima circula por uma casa, sítio ou "
                              "propriedade, mas **não pode sair**."),
        ("CÁRCERE PRIVADO", "wine", "Privação **mais restrita**: a vítima fica confinada em espaço "
                                    "delimitado — quarto, cela ou cômodo."),
    ]):
        x = MARGIN + i * (pw + 40)
        d.rounded_rectangle([x, 250, x + pw, 820], radius=18, fill=C["panel"])
        fh = font("serif_b", 44)
        d.text((x + (pw - fh.getlength(head)) / 2, 268), head, font=fh, fill=col(color))
        if step >= i + 2:
            d.rounded_rectangle([x, 250, x + pw, 820], radius=18, outline=col(color), width=4)
            draw_rich(d, (x + 30, 690), cap, 30, pw - 60)
    if step >= 4:
        d.rounded_rectangle([MARGIN, 845, MARGIN + CONTENT_W, 975], radius=16, outline=C["gold"], width=4, fill=C["bg1"])
        draw_rich(d, (MARGIN + 50, 868), "Mesmo núcleo: **privar alguém de sua liberdade** · mesmo art. 148 · "
                                         "**mesma pena** (reclusão de 1 a 3 anos, no caput)", 34, CONTENT_W - 100)
    return img


def render_compare_anim(base, t, step):
    img = base.copy()
    d = ImageDraw.Draw(img)
    pw = (CONTENT_W - 40) // 2
    # --- painel esquerdo: propriedade cercada (sequestro)
    x0 = MARGIN
    fx0, fy0, fx1, fy1 = x0 + 60, 340, x0 + pw - 60, 670
    d.rectangle([fx0 + 4, fy0 + 4, fx1 - 4, fy1 - 4], fill=(36, 58, 52))
    for fx in range(int(fx0), int(fx1) + 1, 28):
        d.line([fx, fy0 - 10, fx, fy0 + 10], fill=C["muted"], width=3)
        d.line([fx, fy1 - 10, fx, fy1 + 10], fill=C["muted"], width=3)
    for fy in range(fy0, fy1 + 1, 28):
        d.line([fx0 - 10, fy, fx0 + 10, fy], fill=C["muted"], width=3)
        d.line([fx1 - 10, fy, fx1 + 10, fy], fill=C["muted"], width=3)
    d.rectangle([fx0, fy0, fx1, fy1], outline=C["muted"], width=3)
    # casa e árvores
    hx, hy = fx0 + 120, fy0 + 150
    d.polygon([(hx - 80, hy), (hx, hy - 70), (hx + 80, hy)], fill=(150, 90, 70))
    d.rectangle([hx - 64, hy, hx + 64, hy + 90], fill=(210, 196, 170))
    d.rectangle([hx - 16, hy + 40, hx + 16, hy + 90], fill=(110, 80, 60))
    for tx, ty in ((fx1 - 90, fy0 + 80), (fx1 - 150, fy1 - 70), (fx0 + 260, fy1 - 60)):
        d.rectangle([tx - 5, ty, tx + 5, ty + 30], fill=(110, 80, 60))
        d.ellipse([tx - 32, ty - 50, tx + 32, ty + 10], fill=(70, 130, 90))
    # portão trancado
    gx, gy = fx1, (fy0 + fy1) // 2
    d.rectangle([gx - 6, gy - 50, gx + 6, gy + 50], fill=C["bg1"])
    d.line([gx, gy - 50, gx, gy + 50], fill=C["gold"], width=6)
    draw_lock(d, gx + 34, gy - 10, 40, "gold")
    # pessoa circulando dentro da propriedade
    cx = (fx0 + fx1) / 2 + (fx1 - fx0 - 160) / 2 * math.sin(t * 0.55)
    cy = (fy0 + fy1) / 2 + 40 + (fy1 - fy0 - 170) / 2 * math.sin(t * 0.9 + 1.0)
    draw_person(d, cx, cy, 70, "text")
    # --- painel direito: cômodo trancado (cárcere privado)
    x1 = MARGIN + pw + 40
    rx0, ry0 = x1 + pw / 2 - 170, 360
    rx1, ry1 = x1 + pw / 2 + 170, 650
    d.rectangle([rx0, ry0, rx1, ry1], fill=(48, 44, 56), outline=(190, 184, 170), width=14)
    dx = rx1 - 7
    d.rectangle([dx - 7, ry0 + 90, dx + 7, ry0 + 220], fill=(120, 86, 60))
    draw_lock(d, rx1 + 44, ry0 + 150, 44, "gold")
    # janela com grade
    d.rectangle([rx0 + 40, ry0 + 40, rx0 + 130, ry0 + 110], fill=(24, 36, 56), outline=(190, 184, 170), width=4)
    for gxw in range(int(rx0 + 58), int(rx0 + 130), 18):
        d.line([gxw, ry0 + 40, gxw, ry0 + 110], fill=(190, 184, 170), width=3)
    px = (rx0 + rx1) / 2 + 40 * math.sin(t * 0.8)
    draw_person(d, px, ry1 - 60 + 3 * math.sin(t * 2.0), 70, "text")
    return img


# ---------------------------------------------------------------- áudio
def synth(text, voice, path, length_scale):
    subprocess.run(["piper", "-m", voice, "-f", path, "--length-scale", str(length_scale),
                    "--sentence-silence", "0.18"], input=text.encode("utf-8"), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return sr, data


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="art148_sequestro_carcere_privado.mp4")
    ap.add_argument("--length-scale", type=float, default=0.88)
    ap.add_argument("--preview", action="store_true", help="só exporta PNGs de cada passo")
    args = ap.parse_args()

    bg = make_background()
    tmp = tempfile.mkdtemp()

    if args.preview:
        os.makedirs("preview", exist_ok=True)
        for si, sc in enumerate(SCENES):
            steps = sorted({s for _, s in sc["segs"]})
            img = frame_for(bg, sc, steps[-1], 0.5, 0.0, {})
            img.save(f"preview/cena{si + 1:02d}.png")
        return

    # 1) narração e tempos
    timeline, audio, sr = [], [], None
    gap, lead = 0.3, 0.35
    frame_total = 0
    for si, sc in enumerate(SCENES):
        for gi, (text, step) in enumerate(sc["segs"]):
            sr, data = synth(text, args.voice, os.path.join(tmp, f"s{si}_{gi}.wav"), args.length_scale)
            pre = lead if gi == 0 else 0.0
            post = gap + (0.7 if gi == len(sc["segs"]) - 1 else 0.0)
            if sc.get("title") == "Quadro-resumo":
                post += 7.0  # tempo para leitura da tabela
            elif sc.get("kind") == "end":
                post += 3.0
            dur = pre + len(data) / sr + post
            nframes = int(round(dur * FPS))
            timeline.append(dict(scene=si, step=step, text=text, start=frame_total, frames=nframes,
                                 speech_start=frame_total / FPS + pre, speech_len=len(data) / sr))
            seg = np.zeros(int(round(nframes * sr / FPS)), dtype=np.int16)
            off = int(pre * sr)
            seg[off:off + len(data)] = data[: len(seg) - off]
            audio.append(seg)
            frame_total += nframes
    audio = np.concatenate(audio)
    wav_path = os.path.join(tmp, "narracao.wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio.tobytes())
    print(f"Duração: {frame_total / FPS / 60:.2f} min")

    # 2) legendas
    base = os.path.splitext(args.out)[0]
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for i, seg in enumerate(timeline, 1):
            f.write(f"{i}\n{srt_time(seg['speech_start'])} --> {srt_time(seg['speech_start'] + seg['speech_len'])}\n"
                    f"{seg['text']}\n\n")

    # 3) vídeo
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
                             "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart",
                             "-shortest", args.out], stdin=subprocess.PIPE)
    cache = {}
    prev, prev_scene = None, None
    for seg in timeline:
        sc = SCENES[seg["scene"]]
        fade = 16 if seg["scene"] != prev_scene else 9
        prev_scene = seg["scene"]
        for k in range(seg["frames"]):
            fi = seg["start"] + k
            img = frame_for(bg, sc, seg["step"], fi / frame_total, fi / FPS, cache)
            arr = np.asarray(img)
            if prev is not None and k < fade:
                a = (k + 1) / (fade + 1)
                arr = (prev.astype(np.float32) * (1 - a) + arr.astype(np.float32) * a).astype(np.uint8)
            proc.stdin.write(arr.tobytes())
        prev = arr
    proc.stdin.close()
    proc.wait()
    print("OK:", args.out)


def frame_for(bg, sc, step, progress, t, cache):
    kind = sc.get("kind")
    pbucket = round(progress * 400)  # barra de progresso muda em passos pequenos
    if kind == "compare":
        key = (id(sc), step, pbucket)
        if key not in cache:
            cache.clear()
            cache[key] = render_compare_base(bg, sc, step, pbucket / 400)
        return render_compare_anim(cache[key], t, step)
    key = (id(sc), step, pbucket)
    if key not in cache:
        cache.clear()
        fn = {"title": render_title, "end": render_end}.get(kind, render_standard)
        cache[key] = fn(bg, sc, step, pbucket / 400)
    return cache[key]


if __name__ == "__main__":
    main()
