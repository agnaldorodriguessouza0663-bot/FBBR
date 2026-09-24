# -*- coding: utf-8 -*-
"""Personagens ilustrados (Ana, Carlos, Bruno e policiais genéricos).

Os traços seguem as fotos de referência: cabelo, barba, óculos, tom de pele
e roupas. São personagens estilizados, não retratos. Cada um é desenhado
sempre com as mesmas cores e formas, para manter a identidade entre as cenas.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- fichas
ANA = dict(
    name="Ana",
    skin=(112, 70, 46), skin_dark=(88, 54, 36), lips=(122, 62, 50),
    hair="afro", hair_color=(28, 22, 20), hair_hi=(58, 46, 40),
    brows=(30, 22, 18), brow_w=7,
    shirt=(214, 148, 64), shirt_dark=(180, 118, 44), neck="v",
    pants=(46, 58, 86), shoes=(120, 78, 52),
    earrings=(214, 176, 80),
)
CARLOS = dict(
    name="Carlos",
    skin=(196, 146, 112), skin_dark=(168, 118, 88), lips=(150, 92, 80),
    hair="short_receding", hair_color=(24, 20, 18),
    beard="full", beard_color=(26, 20, 17), beard_grey=(92, 86, 80),
    brows=(26, 20, 18), brow_w=11,
    shirt=(34, 36, 40), shirt_dark=(22, 24, 27), neck="crew", necklace=(70, 60, 50),
    pants=(52, 62, 82), shoes=(28, 28, 30),
)
BRUNO = dict(
    name="Bruno",
    skin=(178, 128, 98), skin_dark=(150, 104, 78), lips=(140, 84, 74),
    hair="short_fade", hair_color=(22, 18, 16),
    beard="trim", beard_color=(34, 24, 20), beard_grey=None,
    brows=(24, 18, 16), brow_w=8,
    glasses=(40, 40, 46),
    shirt=(232, 230, 222), shirt_dark=(196, 194, 186), neck="crew",
    pants=(112, 146, 184), shoes=(236, 236, 236),
    watch=(212, 172, 70),
)
POLICIAL = dict(
    name="Policial",
    skin=(150, 106, 80), skin_dark=(126, 88, 66), lips=(120, 76, 64),
    hair="cap", hair_color=(20, 26, 44),
    brows=(30, 24, 20), brow_w=7,
    shirt=(34, 48, 78), shirt_dark=(24, 34, 58), neck="crew", badge=(212, 176, 80),
    pants=(30, 40, 64), shoes=(18, 18, 20),
)

ARM_UP, ARM_LO = 190, 185


def _limb(d, p1, p2, w, color):
    x1, y1 = p1
    x2, y2 = p2
    ang = math.atan2(y2 - y1, x2 - x1)
    dx, dy = math.sin(ang) * w / 2, -math.cos(ang) * w / 2
    d.polygon([(x1 + dx, y1 + dy), (x2 + dx, y2 + dy), (x2 - dx, y2 - dy), (x1 - dx, y1 - dy)], fill=color)
    d.ellipse([x1 - w / 2, y1 - w / 2, x1 + w / 2, y1 + w / 2], fill=color)
    d.ellipse([x2 - w / 2, y2 - w / 2, x2 + w / 2, y2 + w / 2], fill=color)


def _ik(sx, sy, tx, ty, outward):
    """Cotovelo por cinemática inversa de 2 segmentos (dobra para fora)."""
    dx, dy = tx - sx, ty - sy
    dist = max(1e-3, min(math.hypot(dx, dy), ARM_UP + ARM_LO - 1))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1, min(1, (ARM_UP ** 2 + dist ** 2 - ARM_LO ** 2) / (2 * ARM_UP * dist))))
    best = None
    for sgn in (1, -1):
        ex, ey = sx + ARM_UP * math.cos(a + sgn * b), sy + ARM_UP * math.sin(a + sgn * b)
        score = 0.5 * (ex - sx) * outward + (ey - sy)
        if best is None or score > best[0]:
            best = (score, ex, ey)
    hx, hy = sx + dist * math.cos(a), sy + dist * math.sin(a)
    return (best[1], best[2]), (hx, hy)


# alvos da mão, relativos ao ombro, com x positivo = para fora do corpo
ARM_TARGETS = {
    "down": (22, 360),
    "phone": (-52, -100),
    "reach": (330, 60),
    "key": (-30, 215),
    "pocket": (12, 300),
    "wave": (150, -190),
    "chest": (-95, 120),
    "open": (150, 250),
    "cross": (-150, 170),
}


def draw_character(spec, h, t=0.0, walk=None, arms=("down", "down"), expr="neutral", talk=False,
                   look=0.0, breathe=True, prop=None, seed=0):
    """Desenha o personagem e devolve (imagem RGBA, deslocamento_x_dos_pés).

    h: altura em pixels; walk: fase da caminhada (rad) ou None;
    arms: pose do braço esquerdo e do direito da imagem; expr: smile/neutral/worried/serious/relief.
    """
    S = 2
    TOP = 60  # margem acima da cabeça (cabelo volumoso)
    Hh = int(h * S)
    Ww = int(h * 1.05 * S)
    u = Hh / 1000.0
    img = Image.new("RGBA", (Ww, int(Hh + (TOP + 10) * u)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = Ww / 2

    def P(x, y):
        return (cx + x * u, (y + TOP) * u)

    def box(x0, y0, x1, y1):
        return [cx + x0 * u, (y0 + TOP) * u, cx + x1 * u, (y1 + TOP) * u]

    bob = 0.0
    if walk is not None:
        bob = -7 * abs(math.sin(walk))
    elif breathe:
        bob = 2.2 * math.sin(t * 1.7 + seed)

    # --- cabelo volumoso atrás da cabeça (Ana)
    if spec["hair"] == "afro":
        rnd = random.Random(7)
        hc, hh = spec["hair_color"], spec["hair_hi"]
        d.ellipse(box(-150, -12 + bob, 150, 238 + bob), fill=hc)
        for k in range(46):
            a = 2 * math.pi * k / 46
            rx, ry = 150 * math.cos(a), 125 * math.sin(a) + 113 + bob
            r = 26 + rnd.random() * 10
            d.ellipse(box(rx - r, ry - r, rx + r, ry + r), fill=hc)
        for _ in range(120):
            a = rnd.random() * 2 * math.pi
            rr = rnd.random() ** 0.5
            x, y = 145 * rr * math.cos(a), 118 * rr * math.sin(a) + 113 + bob
            r = 5 + rnd.random() * 6
            d.arc(box(x - r, y - r, x + r, y + r), rnd.randint(0, 180), rnd.randint(200, 360), fill=hh, width=max(1, int(2 * u)))

    # --- pernas
    swing = 24 * math.sin(walk) if walk is not None else 0.0
    for side, sgn in ((-1, 1), (1, -1)):
        hip = (side * 44, 525 + bob)
        ang = math.radians(swing * sgn)
        knee_bend = max(0.0, math.sin(walk + (0 if sgn > 0 else math.pi))) * 10 if walk is not None else 0
        foot = (hip[0] + math.sin(ang) * 435, hip[1] + math.cos(ang) * 435 - knee_bend)
        _limb(d, P(*hip), P(*foot), 78 * u, spec["pants"])
        fx, fy = foot
        d.ellipse(box(fx - 46, fy - 6, fx + 50, fy + 34), fill=spec["shoes"])
    d.rounded_rectangle(box(-92, 505 + bob, 92, 600 + bob), radius=int(20 * u), fill=spec["pants"])

    # --- tronco
    sh, shd = spec["shirt"], spec["shirt_dark"]
    y0 = 212 + bob
    d.polygon([P(-112, y0 + 18), P(112, y0 + 18), P(92, 560 + bob), P(-92, 560 + bob)], fill=sh)
    d.ellipse(box(-128, y0, -70, y0 + 70), fill=sh)
    d.ellipse(box(70, y0, 128, y0 + 70), fill=sh)
    d.rectangle(box(-112, y0 + 10, 112, y0 + 60), fill=sh)
    d.line([P(-92, 555 + bob), P(92, 555 + bob)], fill=shd, width=max(2, int(6 * u)))
    if spec.get("badge"):
        d.polygon([P(52, 290 + bob), P(72, 280 + bob), P(92, 290 + bob), P(88, 318 + bob), P(72, 328 + bob), P(56, 318 + bob)],
                  fill=spec["badge"])
        d.rectangle(box(-88, 300 + bob, -40, 312 + bob), fill=(200, 200, 210))

    # --- pescoço e gola
    d.rectangle(box(-27, 168 + bob, 27, 232 + bob), fill=spec["skin_dark"])
    if spec["neck"] == "v":
        d.polygon([P(-40, y0 + 4), P(40, y0 + 4), P(0, y0 + 70)], fill=spec["skin_dark"])
        d.line([P(-40, y0 + 4), P(0, y0 + 70), P(40, y0 + 4)], fill=shd, width=max(2, int(6 * u)))
    else:
        d.arc(box(-40, y0 - 22, 40, y0 + 26), 0, 180, fill=shd, width=max(2, int(8 * u)))
    if spec.get("necklace"):
        d.arc(box(-30, y0 - 30, 30, y0 + 110), 20, 160, fill=spec["necklace"], width=max(1, int(3 * u)))

    # --- cabeça
    hy0 = bob
    d.ellipse(box(-76, 102 + hy0, -54, 150 + hy0), fill=spec["skin_dark"])
    d.ellipse(box(54, 102 + hy0, 76, 150 + hy0), fill=spec["skin_dark"])
    d.ellipse(box(-64, 40 + hy0, 64, 198 + hy0), fill=spec["skin"])
    if spec.get("earrings"):
        for s in (-1, 1):
            d.ellipse(box(s * 66 - 7, 148 + hy0, s * 66 + 7, 162 + hy0), fill=spec["earrings"])

    # cabelo
    hc = spec["hair_color"]
    if spec["hair"] == "afro":
        rnd = random.Random(11)
        for k in range(9):
            x = -70 + k * 17.5
            r = 24 + rnd.random() * 6
            yy = 46 + 10 * abs(k - 4) / 4 + hy0
            d.ellipse(box(x - r, yy - r, x + r, yy + r), fill=hc)
    elif spec["hair"] == "short_receding":
        d.chord(box(-67, 30 + hy0, 67, 112 + hy0), 180, 360, fill=hc)
        for s in (-1, 1):
            d.rectangle(box(min(s * 58, s * 66), 72 + hy0, max(s * 58, s * 66), 108 + hy0), fill=hc)
    elif spec["hair"] == "short_fade":
        d.chord(box(-67, 22 + hy0, 67, 120 + hy0), 180, 360, fill=hc)
        d.rectangle(box(-66, 70 + hy0, -58, 104 + hy0), fill=hc)
        d.rectangle(box(58, 70 + hy0, 66, 104 + hy0), fill=hc)
    elif spec["hair"] == "cap":
        d.chord(box(-70, 22 + hy0, 70, 120 + hy0), 180, 360, fill=hc)
        d.rectangle(box(-70, 64 + hy0, 70, 80 + hy0), fill=hc)
        d.chord(box(-80, 70 + hy0, 80, 96 + hy0), 0, 180, fill=(14, 18, 32))
        d.ellipse(box(-10, 36 + hy0, 10, 56 + hy0), fill=(212, 176, 80))

    # barba
    beard = spec.get("beard")
    if beard == "full":
        bc = spec["beard_color"]
        d.chord(box(-66, 62 + hy0, 66, 236 + hy0), 0, 180, fill=bc)
        for s in (-1, 1):
            d.rectangle(box(min(s * 56, s * 65), 100 + hy0, max(s * 56, s * 65), 152 + hy0), fill=bc)
        d.ellipse(box(-34, 146 + hy0, 34, 168 + hy0), fill=bc)
        rnd = random.Random(3)
        for _ in range(60):
            x = rnd.uniform(-52, 52)
            y = rnd.uniform(160, 225)
            if (x / 60) ** 2 + ((y - 150) / 82) ** 2 < 1:
                d.point(P(x, y + hy0), fill=spec["beard_grey"])
    elif beard == "trim":
        bc = spec["beard_color"]
        d.chord(box(-64, 84 + hy0, 64, 216 + hy0), 0, 180, fill=bc)
        for s in (-1, 1):
            d.rectangle(box(min(s * 58, s * 64), 110 + hy0, max(s * 58, s * 64), 152 + hy0), fill=bc)
        d.ellipse(box(-28, 148 + hy0, 28, 164 + hy0), fill=bc)

    # olhos (com piscar)
    blink = (t + seed * 0.9) % 3.9 < 0.13
    lx = look * 5
    for s in (-1, 1):
        ex, ey = s * 25, 116 + hy0
        if blink:
            d.line([P(ex - 11, ey), P(ex + 11, ey)], fill=(30, 20, 16), width=max(2, int(4 * u)))
        else:
            d.ellipse(box(ex - 13, ey - 8, ex + 13, ey + 8), fill=(246, 242, 236))
            d.ellipse(box(ex - 7 + lx, ey - 7, ex + 7 + lx, ey + 7), fill=(58, 36, 24))
            d.ellipse(box(ex - 3 + lx, ey - 3, ex + 3 + lx, ey + 3), fill=(10, 8, 8))
            d.ellipse(box(ex - 2 + lx - 2, ey - 5, ex + lx, ey - 3), fill=(255, 255, 255))
    # sobrancelhas
    inner = {"worried": -8, "serious": 7, "relief": -3}.get(expr, 0)
    for s in (-1, 1):
        d.line([P(s * 40, 98 + hy0), P(s * 12, 96 + inner + hy0)], fill=spec["brows"],
               width=max(2, int(spec["brow_w"] * u)))
    # nariz
    d.arc(box(-10, 126 + hy0, 10, 146 + hy0), 20, 160, fill=spec["skin_dark"], width=max(2, int(4 * u)))
    # boca
    my = 170 + hy0
    lips = spec["lips"]
    if talk and int(t * 9) % 2 == 0:
        d.ellipse(box(-14, my - 8, 14, my + 10), fill=(70, 30, 30))
    elif expr == "smile":
        d.chord(box(-24, my - 16, 24, my + 12), 0, 180, fill=(246, 244, 240))
        d.arc(box(-24, my - 16, 24, my + 12), 0, 180, fill=lips, width=max(2, int(5 * u)))
    elif expr == "relief":
        d.arc(box(-18, my - 10, 18, my + 6), 10, 170, fill=lips, width=max(2, int(5 * u)))
    elif expr == "worried":
        d.arc(box(-16, my, 16, my + 16), 200, 340, fill=lips, width=max(2, int(5 * u)))
    else:
        d.line([P(-15, my), P(15, my)], fill=lips, width=max(2, int(5 * u)))

    # óculos
    if spec.get("glasses"):
        gc = spec["glasses"]
        gw = max(2, int(3.5 * u))
        for s in (-1, 1):
            d.rounded_rectangle(box(min(s * 8, s * 44), 102 + hy0, max(s * 8, s * 44), 130 + hy0), radius=int(7 * u),
                                outline=gc, width=gw)
            d.line([P(s * 44, 110 + hy0), P(s * 62, 106 + hy0)], fill=gc, width=gw)
        d.line([P(-8, 110 + hy0), P(8, 110 + hy0)], fill=gc, width=gw)

    # --- braços
    for i, side in enumerate((-1, 1)):
        pose = arms[i]
        sx, sy = side * 108, 232 + bob
        tx, ty = ARM_TARGETS.get(pose, ARM_TARGETS["down"])
        if walk is not None and pose == "down":
            sw = 22 * math.sin(walk) * (1 if side < 0 else -1)
            tx, ty = 22 + sw * 1.5, 355
        tx, ty = sx + side * tx, sy + ty
        (ex, ey), (hx, hy) = _ik(sx, sy, tx, ty, side)
        _limb(d, P(sx, sy), P(ex, ey), 60 * u, spec["skin"])
        _limb(d, P(ex, ey), P(hx, hy), 54 * u, spec["skin"])
        mx, my = sx + (ex - sx) * 0.55, sy + (ey - sy) * 0.55
        _limb(d, P(sx, sy), P(mx, my), 76 * u, sh)
        d.ellipse(box(hx - 30, hy - 30, hx + 30, hy + 30), fill=spec["skin"])
        if spec.get("watch") and side == -1:
            wx, wy = ex + (hx - ex) * 0.8, ey + (hy - ey) * 0.8
            d.ellipse(box(wx - 20, wy - 20, wx + 20, wy + 20), fill=spec["watch"])
        if pose == "phone" and side == 1:
            d.rounded_rectangle(box(hx - 22, hy - 58, hx + 16, hy + 20), radius=int(8 * u), fill=(20, 20, 24))
        if pose == "key" and prop == "key":
            kx, ky = hx, hy
            d.ellipse(box(kx - 16, ky - 34, kx + 16, ky - 4), outline=(214, 176, 80), width=max(2, int(6 * u)))
            d.line([P(kx, ky - 4), P(kx, ky + 40)], fill=(214, 176, 80), width=max(2, int(7 * u)))
            d.line([P(kx, ky + 30), P(kx + 14, ky + 30)], fill=(214, 176, 80), width=max(2, int(6 * u)))

    img = img.resize((Ww // S, img.size[1] // S), Image.LANCZOS)
    # iluminação lateral suave (luz vinda da esquerda)
    a = np.asarray(img).astype(np.float32)
    grad = np.linspace(1.08, 0.80, a.shape[1])[None, :, None]
    vgrad = np.linspace(1.04, 0.92, a.shape[0])[:, None, None]
    a[:, :, :3] = np.clip(a[:, :, :3] * grad * vgrad, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def paste_character(canvas, char_img, x, y_feet, shadow=True):
    """Cola o personagem com os pés em (x, y_feet) e sombra no chão."""
    w, h = char_img.size
    if shadow:
        sh = Image.new("RGBA", (int(w * 0.9), int(h * 0.07)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([0, 0, sh.size[0], sh.size[1]], fill=(0, 0, 0, 70))
        canvas.alpha_composite(sh, (int(x - sh.size[0] / 2), int(y_feet - sh.size[1] / 2)))
    feet = h * 1000 / 1070.0  # pés em y=1000 de um total de 1070 unidades (TOP=60 + 10)
    canvas.alpha_composite(char_img, (int(x - w / 2), int(y_feet - feet)))
