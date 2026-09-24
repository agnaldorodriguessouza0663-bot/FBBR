# -*- coding: utf-8 -*-
"""Cenários desenhados em tamanho "mundo" (2208x1242) para permitir movimentos de câmera."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BW, BH = 2208, 1242
GROUND = 1080  # linha dos pés nos cenários externos e internos


def vgrad(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, np.float32)[None, None, :] * (1 - t) + np.array(bottom, np.float32)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8), "RGB")


def glow(img, xy, r, color, alpha=120):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=color + (alpha,))
    ov = ov.filter(ImageFilter.GaussianBlur(r / 2.5))
    return Image.alpha_composite(img.convert("RGBA"), ov)


def calcadao(w, h, c1=(236, 232, 222), c2=(30, 30, 32)):
    """Calçada de pedras portuguesas em ondas (estilo calçadão brasileiro)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    persp = 1 + y / h * 1.8
    wave = np.sin(x / (70 * persp) * 1.0 + np.sin(y / 18) * 0.0) * 22 * persp
    band = ((y * persp * 0.9 + wave) // (26 * persp)) % 2
    out = np.where(band[..., None] > 0, np.array(c1), np.array(c2)).astype(np.uint8)
    return Image.fromarray(out, "RGB")


def city_street(dusk=False):
    top, bot = ((34, 46, 84), (236, 150, 96)) if dusk else ((92, 150, 214), (236, 214, 176))
    img = vgrad(BW, BH, top, bot).convert("RGBA")
    img = glow(img, (1650, 520), 260, (255, 214, 150), 150 if dusk else 90)
    d = ImageDraw.Draw(img)
    rnd = random.Random(4)
    # prédios ao fundo
    x = 0
    while x < BW:
        w = rnd.randint(120, 240)
        h = rnd.randint(260, 560)
        c = (58, 70, 100) if dusk else (150, 168, 196)
        d.rectangle([x, 760 - h, x + w, 800], fill=c)
        for wy in range(760 - h + 24, 780, 38):
            for wx in range(x + 16, x + w - 20, 34):
                lit = rnd.random() < (0.5 if dusk else 0.15)
                d.rectangle([wx, wy, wx + 16, wy + 20], fill=(255, 214, 140) if lit else ((44, 54, 80) if dusk else (176, 192, 214)))
        x += w + rnd.randint(4, 30)
    # morro com vegetação ao fundo à esquerda
    d.polygon([(0, 640), (260, 470), (520, 560), (700, 800), (0, 800)], fill=(56, 96, 76) if not dusk else (32, 56, 50))
    # casarões coloniais coloridos
    colors = [(233, 196, 106), (42, 157, 143), (231, 111, 81), (244, 162, 97), (138, 177, 125), (201, 132, 164), (106, 153, 206)]
    x = -40
    k = 0
    while x < BW:
        w = rnd.randint(250, 330)
        c = colors[k % len(colors)]
        if dusk:
            c = tuple(int(v * 0.72) for v in c)
        top_y = rnd.randint(560, 640)
        d.rectangle([x, top_y, x + w, GROUND - 60], fill=c)
        d.rectangle([x - 6, top_y - 26, x + w + 6, top_y], fill=tuple(int(v * 0.8) for v in c))
        for wx in range(x + 34, x + w - 60, 92):
            d.rounded_rectangle([wx, top_y + 60, wx + 56, top_y + 170], radius=26, fill=(250, 246, 236))
            d.rounded_rectangle([wx + 6, top_y + 66, wx + 50, top_y + 164], radius=22, fill=(52, 82, 110) if not dusk else (255, 206, 130))
        dx = x + w // 2 - 44
        d.rounded_rectangle([dx, GROUND - 260, dx + 88, GROUND - 60], radius=40, fill=(96, 60, 40))
        x += w
        k += 1
    # palmeiras
    for px in (380, 1180, 1960):
        d.line([(px, GROUND - 40), (px + 20, 540)], fill=(110, 84, 60), width=18)
        for a in range(0, 360, 40):
            ang = math.radians(a)
            d.line([(px + 20, 540), (px + 20 + 150 * math.cos(ang), 540 + 70 * math.sin(ang) + 40)], fill=(46, 120, 74) if not dusk else (30, 70, 50), width=16)
    # calçada
    cal = calcadao(BW, BH - (GROUND - 60), (228, 222, 210) if not dusk else (170, 160, 150), (40, 40, 44))
    img.paste(cal, (0, GROUND - 60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, GROUND - 66, BW, GROUND - 56], fill=(180, 176, 168))
    return img.convert("RGB")


def interior_sala():
    img = vgrad(BW, BH, (206, 186, 160), (170, 148, 122)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # piso de madeira
    d.rectangle([0, 960, BW, BH], fill=(120, 82, 54))
    for y in range(960, BH, 40):
        d.line([(0, y), (BW, y)], fill=(100, 66, 42), width=3)
    for i, x in enumerate(range(-200, BW, 260)):
        off = (i % 2) * 130
        for y in range(960, BH, 80):
            d.line([(x + off, y), (x + off, y + 40)], fill=(100, 66, 42), width=3)
    d.rectangle([0, 950, BW, 966], fill=(90, 60, 40))
    # janela (fim de tarde)
    d.rectangle([220, 330, 700, 760], fill=(250, 240, 226))
    win = vgrad(440, 390, (70, 90, 150), (240, 160, 110))
    img.paste(win, (240, 350))
    d.line([(460, 350), (460, 740)], fill=(250, 240, 226), width=14)
    d.line([(240, 545), (680, 545)], fill=(250, 240, 226), width=14)
    d.rectangle([180, 300, 250, 800], fill=(150, 60, 50))
    d.rectangle([670, 300, 740, 800], fill=(150, 60, 50))
    # sofá
    d.rounded_rectangle([760, 780, 1320, 990], radius=30, fill=(80, 96, 120))
    d.rounded_rectangle([780, 700, 1300, 820], radius=30, fill=(92, 110, 136))
    # quadro e luminária
    d.rectangle([900, 380, 1160, 560], fill=(240, 232, 214), outline=(120, 90, 60), width=10)
    d.polygon([(940, 520), (1010, 440), (1060, 500), (1100, 460), (1130, 520)], fill=(120, 160, 140))
    d.line([(1400, 960), (1400, 560)], fill=(60, 50, 44), width=8)
    d.polygon([(1340, 560), (1460, 560), (1430, 470), (1370, 470)], fill=(240, 220, 170))
    img = glow(img, (1400, 520), 160, (255, 220, 160), 90)
    return img.convert("RGB")


DOOR = (1600, 520, 1830, 1070)  # porta da sala: x0, y0, x1, y1


def draw_door(d, openness, jiggle=0.0, box=DOOR, light=(255, 236, 190)):
    x0, y0, x1, y1 = box
    d.rectangle([x0 - 16, y0 - 16, x1 + 16, y1], fill=(236, 228, 214))
    d.rectangle([x0, y0, x1, y1], fill=light if openness > 0 else (60, 40, 28))
    w = (x1 - x0) * (1 - openness)
    if w > 2:
        d.rectangle([x0, y0, x0 + w, y1], fill=(126, 84, 52))
        if w > 60:
            d.rectangle([x0 + 18, y0 + 30, x0 + w - 18, y0 + 240], outline=(104, 68, 42), width=6)
            d.rectangle([x0 + 18, y0 + 290, x0 + w - 18, y1 - 40], outline=(104, 68, 42), width=6)
        hx, hy = x0 + w - 36, (y0 + y1) / 2 + jiggle
        d.rounded_rectangle([hx - 26, hy - 8, hx + 10, hy + 8], radius=6, fill=(212, 176, 80))
        d.ellipse([hx - 6, hy + 20, hx + 6, hy + 34], fill=(40, 30, 20))


def quarto():
    img = Image.new("RGB", (BW, BH), (120, 110, 128))
    d = ImageDraw.Draw(img)
    # caixa em perspectiva: parede do fundo, laterais, piso e teto
    bx0, by0, bx1, by1 = 560, 260, 1650, 900
    d.polygon([(0, 0), (BW, 0), (bx1, by0), (bx0, by0)], fill=(70, 66, 80))
    d.polygon([(0, 0), (bx0, by0), (bx0, by1), (0, BH)], fill=(96, 90, 108))
    d.polygon([(BW, 0), (bx1, by0), (bx1, by1), (BW, BH)], fill=(88, 82, 100))
    d.polygon([(0, BH), (bx0, by1), (bx1, by1), (BW, BH)], fill=(92, 72, 62))
    d.rectangle([bx0, by0, bx1, by1], fill=(116, 108, 126))
    # janela pequena com cortina
    d.rectangle([760, 380, 1000, 600], fill=(40, 52, 84))
    for gx in range(790, 1000, 40):
        d.line([(gx, 380), (gx, 600)], fill=(170, 170, 180), width=6)
    d.rectangle([740, 360, 1020, 380], fill=(80, 70, 70))
    # cama
    d.polygon([(1180, 760), (1600, 760), (1700, 900), (1120, 900)], fill=(200, 196, 210))
    d.rectangle([1120, 900, 1700, 960], fill=(150, 120, 100))
    d.rectangle([1170, 700, 1330, 770], fill=(236, 232, 240))
    # porta fechada na parede direita (em perspectiva)
    d.polygon([(1800, 330), (2050, 190), (2050, 1150), (1800, 990)], fill=(110, 76, 50))
    d.ellipse([1830, 640, 1856, 666], fill=(212, 176, 80))
    img = img.convert("RGBA")
    img = glow(img, (1100, 200), 300, (255, 230, 190), 60)
    return img.convert("RGB")


def sitio():
    img = vgrad(BW, BH, (120, 170, 220), (220, 226, 206)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.polygon([(0, 700), (500, 520), (1000, 650), (1500, 500), (2208, 680), (2208, 900), (0, 900)], fill=(96, 140, 90))
    d.rectangle([0, 820, BW, BH], fill=(118, 160, 92))
    # casa de fazenda
    d.polygon([(260, 620), (520, 470), (780, 620)], fill=(160, 80, 60))
    d.rectangle([300, 620, 740, 900], fill=(238, 226, 200))
    d.rectangle([480, 740, 560, 900], fill=(110, 76, 50))
    for wx in (340, 620):
        d.rectangle([wx, 680, wx + 80, 760], fill=(80, 110, 140))
    rnd = random.Random(9)
    for tx in (1000, 1300, 1700, 2000, 150):
        ty = rnd.randint(600, 680)
        d.rectangle([tx - 12, ty, tx + 12, ty + 180], fill=(110, 80, 60))
        d.ellipse([tx - 90, ty - 140, tx + 90, ty + 40], fill=(64, 126, 76))
    # cerca
    for fx in range(40, BW, 70):
        d.rectangle([fx, 900, fx + 14, 1100], fill=(150, 116, 80))
    for fy in (940, 1010, 1070):
        d.rectangle([0, fy, BW, fy + 12], fill=(170, 134, 94))
    # porteira trancada
    d.rectangle([1860, 880, 2100, 1110], fill=(120, 90, 60))
    for k in range(5):
        d.line([(1860, 900 + k * 50), (2100, 900 + k * 50)], fill=(170, 134, 94), width=12)
    d.line([(1860, 1110), (2100, 890)], fill=(170, 134, 94), width=12)
    return img.convert("RGB")


def casa_bruno_noite():
    img = vgrad(BW, BH, (30, 38, 64), (22, 26, 44)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # janela com a cidade à noite
    d.rectangle([1250, 260, 2000, 820], fill=(16, 22, 44))
    rnd = random.Random(2)
    for _ in range(26):
        x = rnd.randint(1270, 1940)
        w = rnd.randint(50, 110)
        h = rnd.randint(120, 380)
        d.rectangle([x, 820 - h, x + w, 820], fill=(30, 40, 70))
        for wy in range(830 - h, 810, 30):
            for wx in range(x + 8, x + w - 10, 22):
                if rnd.random() < 0.35:
                    d.rectangle([wx, wy, wx + 10, wy + 14], fill=(255, 214, 140))
    d.rectangle([1240, 250, 2010, 830], outline=(180, 180, 190), width=14)
    d.line([(1625, 260), (1625, 820)], fill=(180, 180, 190), width=10)
    d.rectangle([0, 1000, BW, BH], fill=(48, 44, 50))
    # mesa com luminária
    d.rectangle([200, 820, 900, 850], fill=(110, 80, 60))
    d.rectangle([230, 850, 260, 1000], fill=(90, 64, 48))
    d.rectangle([840, 850, 870, 1000], fill=(90, 64, 48))
    d.line([(300, 820), (360, 640)], fill=(40, 40, 44), width=8)
    d.polygon([(320, 650), (420, 610), (430, 680), (350, 700)], fill=(240, 210, 150))
    img = glow(img, (400, 740), 260, (255, 210, 140), 110)
    return img.convert("RGB")


def estudo_ana():
    img = vgrad(BW, BH, (236, 226, 220), (214, 200, 196)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # quadro da Justiça (Têmis) e balança dourada, como no cenário da foto
    d.rectangle([300, 240, 640, 640], fill=(250, 250, 250), outline=(20, 20, 20), width=14)
    d.ellipse([440, 300, 490, 350], fill=(20, 20, 20))
    d.polygon([(430, 350), (500, 350), (530, 600), (400, 600)], fill=(20, 20, 20))
    d.line([(500, 380), (590, 360)], fill=(20, 20, 20), width=6)
    d.line([(560, 360), (560, 430)], fill=(20, 20, 20), width=4)
    d.line([(1240, 180), (1240, 300)], fill=(200, 160, 60), width=8)
    d.line([(1160, 200), (1320, 200)], fill=(200, 160, 60), width=8)
    d.chord([1130, 240, 1190, 280], 0, 180, fill=(200, 160, 60))
    d.chord([1290, 240, 1350, 280], 0, 180, fill=(200, 160, 60))
    # cortina rosa
    d.rectangle([1850, 0, BW, BH], fill=(236, 206, 214))
    for x in range(1860, BW, 60):
        d.line([(x, 0), (x, BH)], fill=(220, 186, 196), width=10)
    # mesa e notebook "DIREITO"
    d.rectangle([0, 900, BW, BH], fill=(150, 120, 100))
    d.polygon([(760, 900), (1500, 900), (1450, 560), (810, 560)], fill=(30, 30, 36))
    d.polygon([(780, 880), (1480, 880), (1435, 580), (825, 580)], fill=(40, 70, 150))
    return img.convert("RGB")


def casa_fachada():
    img = vgrad(BW, BH, (120, 176, 230), (230, 230, 214)).convert("RGBA")
    img = glow(img, (400, 200), 220, (255, 240, 200), 110)
    d = ImageDraw.Draw(img)
    d.rectangle([900, 440, 1900, GROUND - 40], fill=(236, 214, 170))
    d.polygon([(860, 450), (1400, 250), (1940, 450)], fill=(170, 86, 64))
    d.rectangle([1320, 720, 1500, GROUND - 40], fill=(126, 84, 52))
    for wx in (1000, 1620):
        d.rectangle([wx, 560, wx + 180, 720], fill=(90, 130, 170), outline=(250, 246, 236), width=12)
    for px in (300, 2080):
        d.line([(px, GROUND - 40), (px + 20, 560)], fill=(110, 84, 60), width=18)
        for a in range(0, 360, 40):
            ang = math.radians(a)
            d.line([(px + 20, 560), (px + 20 + 150 * math.cos(ang), 560 + 70 * math.sin(ang) + 40)], fill=(46, 120, 74), width=16)
    cal = calcadao(BW, BH - (GROUND - 60))
    img.paste(cal, (0, GROUND - 60))
    return img.convert("RGB")


FACHADA_DOOR = (1320, 720, 1500, GROUND - 40)


def draw_police_car(d, x, y, t):
    """Viatura estilizada com giroflex alternando (x = centro, y = chão)."""
    d.rounded_rectangle([x - 300, y - 170, x + 300, y - 40], radius=40, fill=(240, 240, 240))
    d.polygon([(x - 170, y - 170), (x - 110, y - 270), (x + 130, y - 270), (x + 200, y - 170)], fill=(236, 236, 236))
    d.polygon([(x - 150, y - 175), (x - 100, y - 255), (x - 10, y - 255), (x - 10, y - 175)], fill=(120, 160, 200))
    d.polygon([(x + 10, y - 175), (x + 10, y - 255), (x + 120, y - 255), (x + 180, y - 175)], fill=(120, 160, 200))
    d.rectangle([x - 300, y - 120, x + 300, y - 90], fill=(30, 60, 140))
    for wx in (x - 190, x + 190):
        d.ellipse([wx - 55, y - 95, wx + 55, y + 15], fill=(30, 30, 32))
        d.ellipse([wx - 25, y - 65, wx + 25, y - 15], fill=(160, 160, 170))
    on = int(t * 3) % 2
    d.rounded_rectangle([x - 60, y - 292, x, y - 270], radius=6, fill=(230, 40, 50) if on else (110, 30, 36))
    d.rounded_rectangle([x, y - 292, x + 60, y - 270], radius=6, fill=(40, 90, 230) if not on else (30, 40, 100))
