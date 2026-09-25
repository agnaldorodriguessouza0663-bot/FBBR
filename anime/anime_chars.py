# -*- coding: utf-8 -*-
"""Personagens em estilo anime (Ana, Carlos, Bruno e policial).

Mesmas fichas de cores da animação 2D (pele, cabelo, barba, óculos, roupas),
redesenhadas com olhos grandes, sombreamento em duas cores (cel shading) e contorno.
"""
import math
import os
import random
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "animacao"))
from personagens import ANA, BRUNO, CARLOS, POLICIAL, draw_character  # noqa: E402

INK = (34, 24, 30)
IRIS = {"Ana": (92, 52, 30), "Carlos": (70, 44, 30), "Bruno": (84, 56, 36), "Policial": (70, 50, 36)}


def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def toon(img, outline=3, edge=60):
    """Contorno externo (silhueta) + linhas internas onde a cor muda bruscamente."""
    a = np.asarray(img).astype(np.int16)
    alpha = a[:, :, 3]
    mask = Image.fromarray((alpha > 40).astype(np.uint8) * 255)
    grown = np.asarray(mask.filter(ImageFilter.MaxFilter(outline * 2 + 1))) > 0
    rgb = a[:, :, :3]
    lum = rgb[:, :, 0] * 0.3 + rgb[:, :, 1] * 0.59 + rgb[:, :, 2] * 0.11
    gx = np.abs(np.diff(lum, axis=1, prepend=lum[:, :1]))
    gy = np.abs(np.diff(lum, axis=0, prepend=lum[:1, :]))
    inner = ((gx + gy) > edge) & (alpha > 200)
    out = a.copy()
    ring = grown & (alpha <= 40)
    out[ring] = INK + (255,)
    out[inner, :3] = (out[inner, :3] * 0.35 + np.array(INK) * 0.65).astype(np.int16)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- cabeça anime
def draw_head(d, spec, ox, oy, s, expr="neutral", t=0.0, talk=False, look=0.0, fx=(), neck=380):
    """Desenha a cabeça com centro do crânio em (ox, oy); s = pixels por unidade."""
    name = spec["name"]
    skin, skd = spec["skin"], _shade(spec["skin"], 0.8)

    def P(x, y):
        return (ox + x * s, oy + y * s)

    def B(x0, y0, x1, y1):
        return [ox + x0 * s, oy + y0 * s, ox + x1 * s, oy + y1 * s]

    def W(v):
        return max(1, int(v * s))

    rnd = random.Random(5)
    hc = spec["hair_color"]
    hl = _shade(hc, 2.6) if sum(hc) < 120 else _shade(hc, 1.3)

    # cabelo de trás (Ana: black power volumoso)
    if spec["hair"] == "afro":
        for _ in range(70):
            a = rnd.random() * 2 * math.pi
            r = rnd.random() ** 0.6
            x, y = 285 * r * math.cos(a), 40 + 270 * r * math.sin(a)
            rr = 70 + rnd.random() * 30
            d.ellipse(B(x - rr, y - rr, x + rr, y + rr), fill=hc)
        for k in range(40):
            a = 2 * math.pi * k / 40
            x, y = 300 * math.cos(a), 40 + 285 * math.sin(a)
            rr = 55 + rnd.random() * 20
            d.ellipse(B(x - rr, y - rr, x + rr, y + rr), fill=hc)
    # pescoço
    d.rectangle(B(-58, 180, 58, neck), fill=skd)
    # orelhas
    for sg in (-1, 1):
        d.ellipse(B(sg * 158 - 26, 20, sg * 158 + 26, 110), fill=skin)
    # rosto (crânio + queixo anime)
    pts = [P(160 * math.cos(math.radians(a)), 170 * math.sin(math.radians(a))) for a in range(180, 361, 10)]
    pts += [P(152, 100), P(105, 200), P(35, 262), P(0, 270), P(-35, 262), P(-105, 200), P(-152, 100)]
    d.polygon(pts, fill=skin)
    # sombra lateral (luz vinda da esquerda)
    d.polygon([P(120, -60), P(160, 0), P(152, 100), P(105, 200), P(35, 262), P(60, 200), P(118, 110), P(132, 20)], fill=skd)
    if spec.get("earrings"):
        for sg in (-1, 1):
            d.ellipse(B(sg * 160 - 12, 110, sg * 160 + 12, 134), fill=spec["earrings"])

    if "shade" in fx:  # sombra dramática na parte de cima do rosto
        pts = [P(160 * math.cos(math.radians(a)), 170 * math.sin(math.radians(a))) for a in range(180, 361, 10)]
        d.polygon(pts + [P(156, 90), P(-156, 90)], fill=_shade(skin, 0.45))
    # barba
    beard = spec.get("beard")
    if beard == "full":
        bc = spec["beard_color"]
        pts = [P(-160, 10), P(-150, 120), P(-118, 220)]
        for k in range(9):
            x = -118 + k * 29.5
            y = 300 + (12 if k % 2 else 0) - abs(x) * 0.35
            pts.append(P(x, y))
        pts += [P(118, 220), P(150, 120), P(160, 10), P(128, 30), P(110, 120), P(60, 150), P(0, 158), P(-60, 150),
                P(-110, 120), P(-128, 30)]
        d.polygon(pts, fill=bc)
        d.polygon([P(-70, 165), P(0, 150), P(70, 165), P(60, 185), P(0, 172), P(-60, 185)], fill=bc)
        for _ in range(40):
            x, y = rnd.uniform(-110, 110), rnd.uniform(190, 280)
            d.line([P(x, y), P(x + 6, y + 10)], fill=spec["beard_grey"], width=W(3))
    elif beard == "trim":
        bc = spec["beard_color"]
        pts = [P(-158, 30), P(-146, 120), P(-100, 215), P(-35, 275), P(0, 285), P(35, 275), P(100, 215), P(146, 120),
               P(158, 30), P(140, 40), P(125, 130), P(80, 200), P(30, 232), P(0, 236), P(-30, 232), P(-80, 200),
               P(-125, 130), P(-140, 40)]
        d.polygon(pts, fill=bc)
        d.polygon([P(-55, 170), P(0, 160), P(55, 170), P(48, 182), P(0, 174), P(-48, 182)], fill=bc)

    # olhos (grandes, com brilho)
    blink = (t % 4.1) < 0.12 and expr not in ("happy",)
    lx = look * 12
    narrow = name == "Carlos"
    E = 1.22
    iris_c = IRIS.get(name, (80, 50, 30))
    for sg in (-1, 1):
        cx, cy = sg * 66, 62

        def EB(x0, y0, x1, y1):
            return B(cx + x0 * E, cy + y0 * E, cx + x1 * E, cy + y1 * E)

        def EP(x, y):
            return P(cx + x * E, cy + y * E)

        if expr == "happy":
            d.arc(EB(-40, -20, 40, 40), 200, 340, fill=INK, width=W(12))
            continue
        if blink:
            d.arc(EB(-42, -30, 42, 20), 20, 160, fill=INK, width=W(9))
            continue
        top = -(24 if narrow else 40)
        d.ellipse(EB(-42, top, 42, 44), fill=(252, 250, 246))
        ir = 0.5 if expr == "shock" else 1.0
        iw, ih = 28 * ir, 40 * ir
        ix = lx / E
        d.ellipse(EB(ix - iw, 4 - ih, ix + iw, 4 + ih), fill=iris_c)
        d.chord(EB(ix - iw, 4 - ih, ix + iw, 4 + ih), 180, 360, fill=_shade(iris_c, 0.5))
        d.ellipse(EB(ix - iw * 0.55, 10, ix + iw * 0.55, 4 + ih * 0.9), fill=_shade(iris_c, 1.5))
        d.ellipse(EB(ix - 12 * ir, -14 * ir, ix + 12 * ir, 20 * ir), fill=(14, 8, 8))
        if expr != "shock":
            d.ellipse(EB(ix - 22, -28, ix - 4, -10), fill=(255, 255, 255))
            d.ellipse(EB(ix + 8, 18, ix + 16, 27), fill=(255, 255, 255))
        # pálpebra superior grossa (cílios); Carlos com olhar mais fechado
        y_in = top + (14 if narrow else 4)
        y_out = top
        ya, yb = (y_out, y_in) if sg < 0 else (y_in, y_out)
        d.polygon([EP(-48, ya + 4), EP(0, top - 8), EP(48, yb + 4), EP(48, yb + 16), EP(0, top + 6), EP(-48, ya + 16)], fill=INK)
        if name == "Ana":
            xo = 48 * sg
            yo = (yb if sg > 0 else ya)
            d.polygon([EP(xo, yo + 4), EP(xo + sg * 20, yo - 12), EP(xo - sg * 4, yo + 16)], fill=INK)
            d.polygon([EP(xo - sg * 8, yo + 6), EP(xo + sg * 12, yo - 2), EP(xo - sg * 10, yo + 16)], fill=INK)
        d.arc(EB(-32, 12, 32, 50), 35, 145, fill=_shade(skin, 0.55), width=W(4))

    # sobrancelhas
    tilt = {"worried": -22, "shock": -18, "serious": 20, "determined": 16, "sad": -20, "sigh": -10}.get(expr, 0)
    bw = 20 if narrow else (14 if name == "Bruno" else 10)
    for sg in (-1, 1):
        cx = sg * 65
        inner_x, outer_x = cx - sg * 42, cx + sg * 44
        d.line([P(outer_x, -14), P(inner_x, -12 + tilt)], fill=spec["brows"], width=W(bw))

    # nariz
    d.line([P(6, 120), P(-2, 146)], fill=_shade(skin, 0.62), width=W(5))

    # boca
    my = 196 if spec.get("beard") else 190
    open_m = talk and int(t * 10) % 3 != 0
    lips = spec["lips"]
    if expr in ("shock",) or open_m:
        h = 26 if expr != "shock" else 34
        d.ellipse(B(-24, my - 6, 24, my + h), fill=(110, 36, 42))
        d.chord(B(-18, my + h * 0.45, 18, my + h), 0, 180, fill=(220, 110, 120))
    elif expr in ("happy", "smile", "relief"):
        d.chord(B(-34, my - 18, 34, my + 22), 0, 180, fill=(120, 40, 46) if expr == "happy" else (250, 248, 244))
        d.arc(B(-34, my - 18, 34, my + 22), 0, 180, fill=_shade(lips, 0.7), width=W(5))
    elif expr in ("worried", "sad", "sigh"):
        pts = [P(-24 + k * 8, my + 6 + (4 if k % 2 else -2)) for k in range(7)]
        d.line(pts, fill=_shade(lips, 0.6), width=W(5))
    else:
        d.line([P(-20, my + 4), P(20, my + 2)], fill=_shade(lips, 0.6), width=W(5))

    # rubor
    if "blush" in fx or expr in ("happy", "relief"):
        for sg in (-1, 1):
            for k in range(3):
                x = sg * 90 + k * 14 - 14
                d.line([P(x, 150), P(x - 10, 168)], fill=(236, 110, 120), width=W(5))

    # cabelo da frente
    if spec["hair"] == "afro":
        for k in range(11):
            x = -190 + k * 38
            y = -120 + abs(x) * 0.25 - 20 * math.cos(k)
            rr = 52 + (k % 3) * 8
            d.ellipse(B(x - rr, y - rr, x + rr, y + rr), fill=hc)
        for _ in range(60):
            a = rnd.random() * 2 * math.pi
            r = 0.3 + 0.7 * rnd.random()
            x, y = 290 * r * math.cos(a), 40 + 280 * r * math.sin(a)
            if abs(x) < 150 and -60 < y < 280:
                continue
            rr = 10 + rnd.random() * 12
            d.arc(B(x - rr, y - rr, x + rr, y + rr), 180, 330, fill=hl, width=W(4))
        d.arc(B(-240, -250, 200, 60), 205, 260, fill=hl, width=W(14))  # brilho anime
    elif spec["hair"] == "short_receding":
        pts = [P(168 * math.cos(math.radians(a)), -8 + 178 * math.sin(math.radians(a))) for a in range(185, 356, 10)]
        edge = []
        for k in range(12, -1, -1):
            x = -150 + k * 25
            edge.append(P(x, -70 + (10 if k % 2 else 0) + abs(x) * 0.12))
        d.polygon(pts + edge, fill=hc)
        for sg in (-1, 1):
            d.polygon([P(sg * 168, -10), P(sg * 150, -60), P(sg * 146, 40), P(sg * 164, 50)], fill=hc)
        d.arc(B(-150, -175, 90, -60), 200, 250, fill=hl, width=W(10))
    elif spec["hair"] == "short_fade":
        pts = [P(170 * math.cos(math.radians(a)), -12 + 185 * math.sin(math.radians(a))) for a in range(185, 356, 10)]
        pts += [P(150, -60), P(110, -80), P(60, -46), P(40, -84), P(-10, -40), P(-30, -86), P(-90, -50), P(-110, -90),
                P(-150, -50)]
        d.polygon(pts, fill=hc)
        for sg in (-1, 1):
            d.polygon([P(sg * 170, -20), P(sg * 152, -50), P(sg * 148, 30), P(sg * 166, 40)], fill=_shade(hc, 1.8))
        d.arc(B(-150, -190, 110, -70), 200, 250, fill=hl, width=W(10))
    elif spec["hair"] == "cap":
        d.chord(B(-176, -200, 176, 20), 180, 360, fill=spec["hair_color"])
        d.rectangle(B(-176, -100, 176, -60), fill=spec["hair_color"])
        d.chord(B(-200, -80, 200, -20), 0, 180, fill=(14, 18, 32))
        d.ellipse(B(-24, -170, 24, -122), fill=(212, 176, 80))

    # óculos (com reflexo)
    if spec.get("glasses"):
        gc = spec["glasses"]
        for sg in (-1, 1):
            cx = sg * 65
            d.rounded_rectangle(B(cx - 60, 18, cx + 60, 108), radius=W(18), outline=gc, width=W(7))
            d.line([P(cx - 30, 96), P(cx + 10, 30)], fill=(236, 244, 255), width=W(5))
            d.line([P(sg * 125, 50), P(sg * 160, 40)], fill=gc, width=W(7))
        d.line([P(-5, 52), P(5, 52)], fill=gc, width=W(7))

    # efeitos anime
    if "sweat" in fx:
        x, y = 200, -40 + 20 * math.sin(t * 3)
        d.polygon([P(x, y - 50), P(x - 26, y + 10), P(x + 26, y + 10)], fill=(150, 200, 250))
        d.ellipse(B(x - 27, y - 16, x + 27, y + 38), fill=(150, 200, 250))
        d.ellipse(B(x - 12, y, x - 2, y + 14), fill=(255, 255, 255))
    if "tear" in fx:
        for sg in (-1, 1):
            d.polygon([P(sg * 80, 108), P(sg * 70, 150), P(sg * 90, 150)], fill=(170, 220, 255))


# ---------------------------------------------------------------- busto e corpo inteiro
@lru_cache(maxsize=256)
def bust(name, size, expr="neutral", tq=0.0, talk=False, look=0.0, fx=(), prop=None):
    """Busto (cabeça + ombros), size = altura em px. Cacheado (animação em 12 qps)."""
    spec = SPECS[name]
    S = 2
    Wd, Hd = int(size * 1.1 * S), int(size * S)
    img = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = Hd / 1000 * 1.0
    ox, oy = Wd / 2, Hd * 0.34 + 3 * S * math.sin(tq * 1.6)
    sh = spec["shirt"]
    shd = _shade(sh, 0.78)
    top = oy + 330 * s
    d.ellipse([ox - 470 * s, top, ox - 250 * s, top + 260 * s], fill=sh)
    d.ellipse([ox + 250 * s, top, ox + 470 * s, top + 260 * s], fill=shd)
    d.polygon([(ox - 480 * s, Hd), (ox - 470 * s, top + 130 * s), (ox - 360 * s, top), (ox + 360 * s, top),
               (ox + 470 * s, top + 130 * s), (ox + 480 * s, Hd)], fill=sh)
    d.polygon([(ox + 150 * s, top), (ox + 360 * s, top), (ox + 470 * s, top + 130 * s), (ox + 480 * s, Hd), (ox + 290 * s, Hd)],
              fill=shd)
    if spec["neck"] == "v":
        d.polygon([(ox - 90 * s, top), (ox + 90 * s, top), (ox, top + 170 * s)], fill=_shade(spec["skin"], 0.8))
    else:
        d.chord([ox - 100 * s, top - 60 * s, ox + 100 * s, top + 50 * s], 0, 180, fill=_shade(spec["skin"], 0.8))
    if spec.get("necklace"):
        d.arc([ox - 90 * s, top - 90 * s, ox + 90 * s, top + 190 * s], 20, 160, fill=(150, 130, 100), width=max(2, int(5 * s)))
    if spec.get("badge"):
        d.polygon([(ox + 250 * s, top + 180 * s), (ox + 300 * s, top + 150 * s), (ox + 350 * s, top + 180 * s),
                   (ox + 330 * s, top + 250 * s), (ox + 270 * s, top + 250 * s)], fill=spec["badge"])
    draw_head(d, spec, ox, oy, s, expr=expr, t=tq, talk=talk, look=look, fx=fx, neck=340)
    if prop == "phone":
        hx, hy = ox + 230 * s, oy + 90 * s
        d.rounded_rectangle([hx - 50 * s, hy - 150 * s, hx + 40 * s, hy + 60 * s], radius=int(20 * s), fill=(24, 24, 30))
        d.ellipse([hx - 70 * s, hy + 20 * s, hx + 70 * s, hy + 150 * s], fill=spec["skin"])
        if spec.get("watch"):
            d.rectangle([hx - 70 * s, hy + 130 * s, hx + 70 * s, hy + 170 * s], fill=spec["watch"])
    img = img.resize((Wd // S, Hd // S), Image.LANCZOS)
    return toon(img)


@lru_cache(maxsize=512)
def full(name, h, tq=0.0, walk=None, arms=("down", "down"), expr="neutral", talk=False, look=0.0, fx=(), prop=None):
    """Corpo inteiro: corpo da animação 2D + cabeça anime por cima + contorno."""
    spec = SPECS[name]
    body = draw_character(spec, h, t=tq, walk=walk, arms=arms, expr="neutral", look=look, prop=prop, breathe=False)
    extra = int(h * 0.25)
    canvas = Image.new("RGBA", (body.size[0], body.size[1] + extra), (0, 0, 0, 0))
    canvas.alpha_composite(body, (0, extra))
    S = 2
    layer = Image.new("RGBA", (canvas.size[0] * S, canvas.size[1] * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = 0.56 * h / 1000 * S
    ox = canvas.size[0] / 2 * S
    oy = (extra + (62 + 60) * h / 1000) * S
    draw_head(d, spec, ox, oy, s, expr=expr, t=tq, talk=talk, look=look, fx=fx, neck=262)
    head = layer.resize(canvas.size, Image.LANCZOS)
    canvas.alpha_composite(head)
    return toon(canvas, outline=2)


def paste_full(canvas, img, x, y_feet, shadow=True):
    """Cola um personagem de corpo inteiro com os pés em (x, y_feet)."""
    w, h = img.size
    hh = h / 1.32  # altura do personagem (corpo 1,07h + margem da cabeça 0,25h)
    feet = 0.25 * hh + 1.06 * hh
    if shadow:
        sh = Image.new("RGBA", (int(w * 0.7), int(hh * 0.06)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([0, 0, sh.size[0], sh.size[1]], fill=(0, 0, 0, 80))
        canvas.alpha_composite(sh, (int(x - sh.size[0] / 2), int(y_feet - sh.size[1] / 2)))
    canvas.alpha_composite(img, (int(x - w / 2), int(y_feet - feet)))


SPECS = {"Ana": ANA, "Carlos": CARLOS, "Bruno": BRUNO, "Policial": POLICIAL}
