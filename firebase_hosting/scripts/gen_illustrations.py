"""
Draws the home page illustrations: an at-a-glance template of the AuraCommerce 360 console for each service,
in the app's own structure (Google colour band, header, service tabs, page row, title, figure cards, content),
with placeholder bars instead of real text and numbers, and the kinds of features each service offers.
Run: python scripts/gen_illustrations.py   (writes public/images/overview.svg, maas.svg, paas.svg, taas.svg, saas.svg)
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'images')
BLUE, RED, YELLOW, GREEN = '#4285F4', '#EA4335', '#FBBC04', '#34A853'
TEAL, TEAL_L = '#008080', '#B2DFDB'
G50, G100, G200, G300, G400 = '#F8F9FA', '#F1F3F4', '#E8EAED', '#DADCE0', '#BDC1C6'
SVC = {
    'maas': dict(solid=BLUE, light='#E8F0FE', soft='#AECBFA'),
    'paas': dict(solid=GREEN, light='#E6F4EA', soft='#A8DAB5'),
    'taas': dict(solid=YELLOW, light='#FEF7E0', soft='#FDE293'),
    'saas': dict(solid=RED, light='#FCE8E6', soft='#F6AEA9'),
}
ORDER = ['maas', 'paas', 'taas', 'saas']
DEFS = ('<defs>'
        '<linearGradient id="{p}band" x1="0" x2="1"><stop offset="0" stop-color="#4285F4"/><stop offset=".33" stop-color="#EA4335"/><stop offset=".66" stop-color="#FBBC04"/><stop offset="1" stop-color="#34A853"/></linearGradient>'
        '<linearGradient id="{p}logo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4285F4"/><stop offset=".35" stop-color="#EA4335"/><stop offset=".65" stop-color="#FBBC04"/><stop offset="1" stop-color="#34A853"/></linearGradient>'
        '<linearGradient id="{p}btn" x1="0" x2="1"><stop offset="0" stop-color="#4285F4"/><stop offset="1" stop-color="#34A853"/></linearGradient>'
        '<clipPath id="{p}win"><rect x="40" y="26" width="720" height="388" rx="14"/></clipPath>'
        '<filter id="{p}sh" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0B1F44" flood-opacity=".18"/></filter>'
        '</defs>')

def r(x, y, w, h, fill, rx=0, stroke=None, sw=1, extra=''):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{st}{extra}/>'

def c(x, y, rad, fill, stroke=None, sw=1):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{fill}"{st}/>'

def line(x, y, w, fill=G200, h=5):
    """A placeholder line of text"""
    return r(x, y, w, h, fill, h / 2)

def card(x, y, w, h, title_w=70, title=TEAL_L):
    return r(x, y, w, h, '#fff', 8, G200) + line(x + 12, y + 12, title_w, title, 6)

def kpis(X, y, W, tones):
    o, cw = [], (W - 32 - 30) / 4
    for i, tone in enumerate(tones):
        cx = X + 16 + i * (cw + 10)
        o += [r(cx, y, cw, 50, '#fff', 8, G200), line(cx + 10, y + 11, 44, G300, 4), line(cx + 10, y + 22, 60, TEAL_L, 10),
              line(cx + 10, y + 38, 70, G200, 4), r(cx + cw - 30, y + 9, 20, 20, SVC[tone]['light'], 5), c(cx + cw - 20, y + 19, 4.5, 'none', SVC[tone]['solid'], 1.6)]
    return ''.join(o)

PANEL_H = 212  # height of the main content panels under the figure cards

def frame(key, body, p=''):
    """The console window: Google colour band and logo, then the page title, figure cards and content.
    No account, search, workspace, service tabs or page menu: the picture is about what the service does."""
    s = SVC[key or 'maas']
    X, Y, W, H = 40, 26, 720, 388
    o = [f'<g clip-path="url(#{p}win)">', r(X, Y, W, H, G50),
         r(X, Y, W, 4, f'url(#{p}band)'), r(X, Y + 4, W, 38, '#fff'),
         r(X + 16, Y + 12, 22, 22, f'url(#{p}logo)', 6), f'<path d="M{X+27},{Y+16} l2,5 5,2 -5,2 -2,5 -2,-5 -5,-2 5,-2z" fill="#fff"/>',
         line(X + 46, Y + 20, 92, G300, 7), r(X, Y + 42, W, 1, G200)]
    dots = [SVC[k]['solid'] for k in ORDER] if key is None else [s['solid']]
    for i, d in enumerate(dots):
        o.append(c(X + 20 + i * 9, Y + 58, 3, d))
    o += [line(X + 20 + len(dots) * 9 + 4, Y + 55, 110, G300, 5),
          line(X + 16, Y + 66, 150, TEAL_L, 11), line(X + 16, Y + 83, 220, G200, 5)]
    o.append(body(X, Y + 100, W, s, p))
    o.append('</g>')
    o.append(f'<rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="14" fill="none" stroke="{G200}" stroke-width="1.5"/>')
    return ''.join(o)

def svg(content, label, light, p=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 440" width="800" height="440" role="img" aria-label="{label}">'
            + DEFS.format(p=p) + r(0, 0, 800, 440, light, 24)
            + '<circle cx="730" cy="40" r="110" fill="#fff" opacity=".45"/><circle cx="60" cy="420" r="90" fill="#fff" opacity=".45"/>'
            + content + '</svg>')

def toggle(x, y, on):
    return r(x, y, 22, 12, GREEN if on else G300, 6) + c(x + (16 if on else 6), y + 6, 4.5, '#fff')

def sparkle(x, y, size, fill):
    k = size
    return f'<path d="M{x},{y-k} l{k*.28},{k*.72} {k*.72},{k*.28} -{k*.72},{k*.28} -{k*.28},{k*.72} -{k*.28},-{k*.72} -{k*.72},-{k*.28} {k*.72},-{k*.28}z" fill="{fill}"/>'

# ---- Management: workspace health, cost by service, roles and access, customization ----
def maas(X, y, W, s, p):
    o = [kpis(X, y, W, ['maas', 'paas', 'taas', 'saas'])]
    cy, h = y + 60, PANEL_H
    w1 = (W - 52) * 0.36
    # cost by service: donut + legend
    o.append(card(X + 16, cy, w1, h))
    cxx, cyy = X + 16 + 58, cy + 22 + h / 2
    circ = 2 * 3.14159 * 36
    off = 0
    for col, frac in [(BLUE, .12), (GREEN, .5), (YELLOW, .17), (RED, .21)]:
        o.append(f'<circle cx="{cxx}" cy="{cyy}" r="36" fill="none" stroke="{col}" stroke-width="14" stroke-dasharray="{circ*frac:.1f} {circ:.1f}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {cxx} {cyy})"/>')
        off += circ * frac
    for i, col in enumerate([BLUE, GREEN, YELLOW, RED]):
        o += [c(X + 16 + 118, cy + h / 2 - 8 + i * 20, 4, col), line(X + 16 + 128, cy + h / 2 - 11 + i * 20, w1 - 150, G200, 5)]
    # usage over time: bars
    x2 = X + 26 + w1
    w2 = (W - 52) * 0.34
    o.append(card(x2, cy, w2, h))
    for i, hh in enumerate([40, 62, 50, 78, 66, 92, 84, 104]):
        o.append(r(x2 + 16 + i * ((w2 - 32) / 8), cy + h - 16 - hh, (w2 - 32) / 8 - 6, hh, [BLUE, GREEN, YELLOW, RED][i % 4], 3))
    # roles and access: avatars with toggles
    x3 = x2 + w2 + 10
    w3 = W - 32 - (x3 - X - 16)
    o.append(card(x3, cy, w3, h))
    for i, col in enumerate([BLUE, GREEN, YELLOW, RED]):
        yy = cy + 44 + i * (h - 60) / 3
        o += [r(x3 + 13, yy - 9, 18, 18, col, 5), f'<path d="M{x3+17.5},{yy} l3,3 6,-6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
              line(x3 + 38, yy - 6, w3 - 90, G300, 5), line(x3 + 38, yy + 3, w3 - 120, G200, 4), toggle(x3 + w3 - 34, yy - 6, i != 2)]
    return ''.join(o)

# ---- Product: catalog cards, live multi-seller bidding, demand forecast ----
def paas(X, y, W, s, p):
    o = [kpis(X, y, W, ['paas', 'maas', 'taas', 'saas'])]
    cy, h = y + 60, PANEL_H
    w1 = (W - 42) * 0.5
    o.append(card(X + 16, cy, w1, h))
    cw = (w1 - 44) / 3
    for i, (col, light) in enumerate([(BLUE, '#E8F0FE'), (YELLOW, '#FEF7E0'), (GREEN, '#E6F4EA')]):
        px = X + 28 + i * (cw + 10)
        o += [r(px, cy + 26, cw, h - 38, '#fff', 8, G200), r(px + 6, cy + 32, cw - 12, 50 + (h - 160), light, 6)]
        if i == 0:   # watch
            o += [r(px + cw / 2 - 5, cy + 36, 10, 42, col, 4), c(px + cw / 2, cy + 57, 13, '#fff', RED, 3)]
        elif i == 1:  # headphones
            o += [f'<path d="M{px+cw/2-14},{cy+66} v-6 a14,14 0 0 1 28,0 v6" fill="none" stroke="{col}" stroke-width="4"/>', r(px + cw / 2 - 17, cy + 62, 7, 12, col, 3), r(px + cw / 2 + 10, cy + 62, 7, 12, col, 3)]
        else:        # power bank
            o += [r(px + cw / 2 - 10, cy + 38, 20, 38, col, 4), c(px + cw / 2, cy + 48, 4, YELLOW), line(px + cw / 2 - 6, cy + 58, 12, '#fff', 3), line(px + cw / 2 - 6, cy + 64, 12, '#fff', 3)]
        d = h - 160
        o += [line(px + 8, cy + 90 + d, cw - 24, G300, 5), line(px + 8, cy + 101 + d, 32, TEAL_L, 7), r(px + 6, cy + 120 + d, cw - 12, 18, f'url(#{p}btn)', 6), line(px + cw / 2 - 16, cy + 127 + d, 32, '#fff', 4)]
    # live bidding
    x2 = X + 26 + w1
    w2 = (W - 42) - w1
    hb = int(h * 0.46)
    o.append(card(x2, cy, w2, hb, 60))
    o += [c(x2 + w2 - 50, cy + 15, 3.5, GREEN), line(x2 + w2 - 42, cy + 13, 28, '#A8DAB5', 4)]
    for i, (col, wv) in enumerate([(GREEN, .9), (BLUE, .7), (YELLOW, .55)]):
        yy = cy + 30 + i * 13
        o += [c(x2 + 18, yy + 3, 4.5, col), r(x2 + 28, yy, (w2 - 80) * wv, 6, s['light'] if i else '#A8DAB5', 3), line(x2 + w2 - 42, yy, 28, TEAL_L if i == 0 else G300, 6)]
    # forecast line chart
    fy = cy + hb + 10
    hf = h - hb - 10
    o.append(card(x2, fy, w2, hf, 56))
    pts = [(0, .55), (.12, .45), (.24, .6), (.36, .4), (.48, .5), (.6, .3), (.72, .38), (.84, .2), (1, .26)]
    gx, gy, gw, gh = x2 + 14, fy + 26, w2 - 28, hf - 34
    path = ' '.join(f'{"M" if i == 0 else "L"}{gx + px * gw:.1f},{gy + py * gh:.1f}' for i, (px, py) in enumerate(pts))
    o += [f'<path d="{path} L{gx+gw},{gy+gh} L{gx},{gy+gh}z" fill="{s["light"]}"/>', f'<path d="{path}" fill="none" stroke="{GREEN}" stroke-width="2.4" stroke-linejoin="round"/>',
          f'<path d="M{gx+.6*gw},{gy} V{gy+gh}" stroke="{G300}" stroke-dasharray="3 3"/>', c(gx + .6 * gw, gy + .3 * gh, 3.5, '#fff', GREEN, 2)]
    return ''.join(o)

# ---- Transport: route map with the AI pick, vehicle choice, delivery timeline ----
def taas(X, y, W, s, p):
    o = [kpis(X, y, W, ['taas', 'maas', 'paas', 'paas'])]
    cy, h = y + 60, PANEL_H
    w1 = (W - 42) * 0.55
    o.append(card(X + 16, cy, w1, h))
    mx, my, mw, mh = X + 28, cy + 26, w1 - 24, h - 38
    o.append(r(mx, my, mw, mh, '#EEF3EA', 6))
    o += [f'<path d="M{mx},{my+mh*.62} C{mx+mw*.25},{my+mh*.5} {mx+mw*.4},{my+mh*.8} {mx+mw},{my+mh*.55}" fill="none" stroke="#fff" stroke-width="7"/>',
          f'<path d="M{mx+mw*.3},{my} C{mx+mw*.35},{my+mh*.4} {mx+mw*.55},{my+mh*.5} {mx+mw*.6},{my+mh}" fill="none" stroke="#fff" stroke-width="6"/>',
          r(mx + mw * .68, my + mh * .1, 40, 26, '#DCEBD6', 4), r(mx + mw * .08, my + mh * .12, 32, 20, '#DCEBD6', 4)]
    # alternative route (grey dashed) and AI pick (green)
    o += [f'<path d="M{mx+30},{my+mh-24} C{mx+mw*.25},{my+20} {mx+mw*.55},{my+mh*.9} {mx+mw-34},{my+30}" fill="none" stroke="{G400}" stroke-width="3" stroke-dasharray="5 5"/>',
          f'<path d="M{mx+30},{my+mh-24} C{mx+mw*.35},{my+mh*.55} {mx+mw*.6},{my+mh*.2} {mx+mw-34},{my+30}" fill="none" stroke="{GREEN}" stroke-width="4" stroke-linecap="round"/>',
          c(mx + 30, my + mh - 24, 7, BLUE, '#fff', 2.5), f'<path d="M{mx+mw-34},{my+18} c-8,0 -8,12 0,20 c8,-8 8,-20 0,-20z" fill="{RED}"/>', c(mx + mw - 34, my + 25, 2.5, '#fff')]
    o += [r(mx + mw * .42, my + mh * .38, 54, 18, '#fff', 9, G200), c(mx + mw * .42 + 10, my + mh * .38 + 9, 4, GREEN), line(mx + mw * .42 + 18, my + mh * .38 + 7, 28, '#A8DAB5', 4)]
    # AI plan: vehicle choice with selected option + why
    x2 = X + 26 + w1
    w2 = (W - 42) - w1
    o.append(card(x2, cy, w2, h, 80))
    o.append(sparkle(x2 + w2 - 20, cy + 15, 6, BLUE))
    vy = cy + 30
    for i, col in enumerate([GREEN, BLUE, YELLOW]):
        bx = x2 + 12 + i * ((w2 - 24) / 3)
        bw = (w2 - 24) / 3 - 6
        o.append(r(bx, vy, bw, 40, '#E6F4EA' if i == 0 else G50, 6, GREEN if i == 0 else G200, 1.5 if i == 0 else 1))
        o += [r(bx + bw / 2 - 12, vy + 9, 16, 11, col, 2), r(bx + bw / 2 + 4, vy + 12, 7, 8, col, 2), c(bx + bw / 2 - 7, vy + 22, 2.6, G400), c(bx + bw / 2 + 6, vy + 22, 2.6, G400), line(bx + 8, vy + 29, bw - 16, G300, 4)]
    ty = vy + 52 + (h - 160) * 0.4
    for i in range(3):   # delivery timeline: packed, on the way, delivered
        tx = x2 + 22 + i * ((w2 - 44) / 2)
        o.append(c(tx, ty, 5, GREEN if i < 2 else G300))
        if i < 2:
            o.append(r(tx + 5, ty - 1.5, (w2 - 44) / 2 - 10, 3, GREEN if i == 0 else G300, 1.5))
        o.append(line(tx - 12, ty + 9, 24, G200, 4))
    o += [r(x2 + 12, ty + 22, w2 - 24, 34, '#E8F0FE', 6), line(x2 + 20, ty + 30, w2 - 60, '#AECBFA', 5), line(x2 + 20, ty + 40, w2 - 90, '#AECBFA', 5),
          r(x2 + w2 - 52, ty + 28, 30, 10, '#fff', 5), line(x2 + w2 - 47, ty + 31, 20, TEAL_L, 4)]
    return ''.join(o)

# ---- Support: tickets, conversation with the assistant, photo grading of a return ----
def saas(X, y, W, s, p):
    o = [kpis(X, y, W, ['saas', 'maas', 'paas', 'taas'])]
    cy, h = y + 60, PANEL_H
    w1 = (W - 52) * 0.3
    o.append(card(X + 16, cy, w1, h))
    for i, col in enumerate([RED, BLUE, GREEN, YELLOW]):
        yy = cy + 28 + i * (h - 40) / 4
        if i == 0:
            o.append(r(X + 20, yy - 4, w1 - 8, 28, s['light'], 6))
        o += [c(X + 34, yy + 10, 8, col), line(X + 48, yy + 3, w1 - 92, G300, 5), line(X + 48, yy + 12, w1 - 112, G200, 4), r(X + 16 + w1 - 38, yy + 4, 26, 10, [s['light'], '#E8F0FE', '#E6F4EA', '#FEF7E0'][i], 5)]
    # conversation
    x2 = X + 26 + w1
    w2 = (W - 52) * 0.4
    o.append(card(x2, cy, w2, h))
    o += [r(x2 + 12, cy + 28, w2 * .62, 22, G100, 10), line(x2 + 20, cy + 36, w2 * .5, G300, 5),
          r(x2 + w2 * .32, cy + 56, w2 * .68 - 12, 30, '#E8F0FE', 10), line(x2 + w2 * .32 + 8, cy + 63, w2 * .5, '#AECBFA', 5), line(x2 + w2 * .32 + 8, cy + 73, w2 * .35, '#AECBFA', 5),
          r(x2 + 12, cy + 92, w2 * .5, 22, G100, 10)]
    for i, hh in enumerate([6, 12, 18, 10, 16, 8, 14, 6, 10]):   # voice message waveform
        o.append(r(x2 + 22 + i * 7, cy + 103 - hh / 2, 3, hh, RED, 1.5))
    d = h - 160
    o += [r(x2 + 12, cy + 124 + d, w2 - 70, 24, '#fff', 8, G300), line(x2 + 20, cy + 134 + d, 70, G200, 5), r(x2 + w2 - 52, cy + 124 + d, 40, 24, f'url(#{p}btn)', 8), line(x2 + w2 - 42, cy + 134 + d, 20, '#fff', 4)]
    # return graded from a photo
    x3 = x2 + w2 + 10
    w3 = W - 32 - (x3 - X - 16)
    o.append(card(x3, cy, w3, h, 64))
    e = (h - 160) * 0.6
    o += [r(x3 + 12, cy + 26, w3 - 24, 64 + e, '#FCE8E6', 8), r(x3 + w3 / 2 - 18, cy + 40 + e / 2, 36, 28, '#fff', 5, RED, 2), c(x3 + w3 / 2, cy + 54 + e / 2, 8, 'none', RED, 2),
          f'<path d="M{x3+18},{cy+32} h8 M{x3+18},{cy+32} v8 M{x3+w3-18},{cy+84+e} h-8 M{x3+w3-18},{cy+84+e} v-8" stroke="{RED}" stroke-width="2"/>',
          r(x3 + 12, cy + 98 + e, 44, 16, '#E6F4EA', 8), line(x3 + 20, cy + 104 + e, 28, '#81C995', 4), line(x3 + 64, cy + 103 + e, w3 - 80, TEAL_L, 6)]
    for i, col in enumerate([GREEN, BLUE, YELLOW, RED]):   # where it goes next: resale, refurbish, parts, recycle
        bx = x3 + 12 + i * ((w3 - 24) / 4)
        o.append(r(bx, cy + 122 + e * 1.5, (w3 - 24) / 4 - 5, 24, '#E6F4EA' if i == 0 else G50, 6, GREEN if i == 0 else G200))
        o.append(c(bx + ((w3 - 24) / 4 - 5) / 2, cy + 134 + e * 1.5, 4, col))
    return ''.join(o)

BODIES = {'maas': maas, 'paas': paas, 'taas': taas, 'saas': saas}
LABELS = {'maas': 'Management as a Service', 'paas': 'Product as a Service', 'taas': 'Transport as a Service', 'saas': 'Support as a Service'}

def write(name, text):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(text)
    print('wrote', name)

for key in ORDER:
    write(f'{key}.svg', svg(frame(key, BODIES[key]), f'{LABELS[key]} in the AuraCommerce 360 console', SVC[key]['light']))

# ---- Home page banner: the console with feature cards beside it, and who uses it ----
def floating(x, y, w, h, inner, p):
    return f'<g filter="url(#{p}sh)">{r(x, y, w, h, "#fff", 14)}</g>{inner}'

# ---- Home page banner: all four services in one console, and what each one does ----
def all_services(X, y, W, s, p):
    """One panel per service, each in its own colour."""
    o = [kpis(X, y, W, ORDER)]
    gy = y + 60
    pw, ph = (W - 42) / 2, (PANEL_H - 10) / 2
    def panel(i, j, key):
        px, py = X + 16 + j * (pw + 10), gy + i * (ph + 10)
        col = SVC[key]
        return px, py, (r(px, py, pw, ph, '#fff', 8, G200) + r(px, py + 10, 3, ph - 20, col['solid'], 1.5)
                        + c(px + 18, py + 15, 4, col['solid']) + line(px + 27, py + 12, 70, TEAL_L, 6))
    # Management: cost by service (donut) and access switches
    px, py, base = panel(0, 0, 'maas')
    o.append(base)
    cx, cy0 = px + 40, py + 44
    circ, off = 2 * 3.14159 * 18, 0
    for col, frac in [(BLUE, .15), (GREEN, .45), (YELLOW, .18), (RED, .22)]:
        o.append(f'<circle cx="{cx}" cy="{cy0}" r="18" fill="none" stroke="{col}" stroke-width="8" stroke-dasharray="{circ*frac:.1f} {circ:.1f}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {cx} {cy0})"/>')
        off += circ * frac
    for k in range(3):
        o += [line(px + 72, py + 30 + k * 13, pw - 120, G200, 5), toggle(px + pw - 38, py + 27 + k * 13, k != 1)]
    # Product: catalog with a bid button
    px, py, base = panel(0, 1, 'paas')
    o.append(base)
    cw = (pw - 40) / 3
    for k, (colr, light) in enumerate([(BLUE, '#E8F0FE'), (YELLOW, '#FEF7E0'), (GREEN, '#E6F4EA')]):
        bx = px + 14 + k * (cw + 6)
        o += [r(bx, py + 24, cw, 40, '#fff', 6, G200), r(bx + 4, py + 28, cw - 8, 16, light, 4), c(bx + cw / 2, py + 36, 5, colr), r(bx + 4, py + 50, cw - 8, 9, f'url(#{p}btn)', 4)]
    # Transport: route on a map
    px, py, base = panel(1, 0, 'taas')
    o.append(base)
    mx, my, mw, mh = px + 14, py + 26, pw - 28, 36
    o += [r(mx, my, mw, mh, '#EEF3EA', 6),
          f'<path d="M{mx+12},{my+mh-10} C{mx+mw*.35},{my+mh*.55} {mx+mw*.6},{my+mh*.15} {mx+mw-14},{my+10}" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>',
          c(mx + 12, my + mh - 10, 4, BLUE, '#fff', 1.5), c(mx + mw - 14, my + 10, 4, RED, '#fff', 1.5),
          r(mx + mw * .42, my + 8, 18, 11, '#B06000', 2), r(mx + mw * .42 + 18, my + 10, 7, 9, '#B06000', 2)]
    # Support: conversation and a graded return photo
    px, py, base = panel(1, 1, 'saas')
    o.append(base)
    o += [r(px + 14, py + 26, pw * .5, 14, G100, 7), r(px + 14 + pw * .2, py + 45, pw * .5, 14, '#E8F0FE', 7),
          r(px + pw - 62, py + 24, 48, 38, '#FCE8E6', 6), r(px + pw - 50, py + 33, 24, 18, '#fff', 3, RED, 1.6), c(px + pw - 38, py + 42, 4.5, 'none', RED, 1.6)]
    return ''.join(o)

def overview():
    """Left: the console showing all four services. Right: one card per service showing what it does."""
    p = 'o'
    WX, WW = 14, 540
    WY = 206 - WW * 388 / 720 / 2
    WH = WW * 388 / 720
    win = f'<svg x="{WX}" y="{WY}" width="{WW}" height="{WH:.1f}" viewBox="40 26 720 388">{DEFS.format(p="w")}{frame(None, all_services, "w")}</svg>'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 8 800 392" width="800" height="392" role="img" aria-label="The AuraCommerce 360 console with its four services: management, products, transport and support">',
         DEFS.format(p=p), f'<g filter="url(#{p}sh)">{win}</g>']

    x, w, h, gap = 566, 220, 84, 8
    def svc_card(i, key, art):
        y = 20 + i * (h + gap)
        col = SVC[key]
        return floating(x, y, w, h, r(x, y + 14, 4, h - 28, col['solid'], 2) + art(x, y, col), p)

    # Management: who may do what, and what it costs
    def maas_art(x, y, col):
        o = [r(x + 16, y + 14, 30, 30, col['light'], 8), f'<path d="M{x+31},{y+20} l8,3 v6 c0,6 -4,9 -8,11 c-4,-2 -8,-5 -8,-11 v-6z" fill="none" stroke="{col["solid"]}" stroke-width="2" stroke-linejoin="round"/>',
             f'<path d="M{x+27.5},{y+30} l2.6,2.8 4.8,-5.4" fill="none" stroke="{col["solid"]}" stroke-width="2" stroke-linecap="round"/>',
             line(x + 56, y + 18, 90, TEAL_L, 7), line(x + 56, y + 30, 120, G200, 5)]
        for k in range(2):
            o += [line(x + 16, y + 56 + k * 12, w - 70, G200, 5), toggle(x + w - 44, y + 53 + k * 12, k == 0)]
        return ''.join(o)

    # Product: products sold through live multi-seller bidding
    def paas_art(x, y, col):
        o = [r(x + 16, y + 14, 30, 30, col['light'], 8), f'<path d="M{x+23},{y+37} l10,-10 m-4,-4 l8,8 m-12,-2 l8,8" stroke="#1E8E3E" stroke-width="2.2" stroke-linecap="round"/>',
             line(x + 56, y + 18, 80, TEAL_L, 7), c(x + w - 30, y + 21, 3.5, GREEN), line(x + w - 23, y + 19, 12, '#A8DAB5', 4)]
        for k, (dot, wv) in enumerate([(GREEN, .95), (BLUE, .7), (YELLOW, .45)]):
            yy = y + 36 + k * 12
            o += [c(x + 62, yy + 2.5, 3, dot), r(x + 70, yy, (w - 120) * wv, 5, '#A8DAB5' if k == 0 else col['light'], 2.5), line(x + w - 40, yy, 24, TEAL_L if k == 0 else G300, 5)]
        return ''.join(o)

    # Transport: the AI picks the greener route
    def taas_art(x, y, col):
        mx, my, mw, mh = x + 56, y + 14, w - 72, h - 28
        return ''.join([r(x + 16, y + 14, 30, 30, col['light'], 8), r(x + 22, y + 24, 12, 9, '#B06000', 2), r(x + 34, y + 26, 6, 7, '#B06000', 1.5), c(x + 25, y + 34, 2, '#B06000'), c(x + 36, y + 34, 2, '#B06000'),
                        r(mx, my, mw, mh, '#EEF3EA', 8),
                        f'<path d="M{mx+12},{my+mh-10} C{mx+mw*.3},{my+6} {mx+mw*.6},{my+mh} {mx+mw-14},{my+12}" fill="none" stroke="{G400}" stroke-width="2" stroke-dasharray="4 4"/>',
                        f'<path d="M{mx+12},{my+mh-10} C{mx+mw*.4},{my+mh*.7} {mx+mw*.6},{my+mh*.2} {mx+mw-14},{my+12}" fill="none" stroke="{GREEN}" stroke-width="3.5" stroke-linecap="round"/>',
                        c(mx + 12, my + mh - 10, 4.5, BLUE, '#fff', 2), c(mx + mw - 14, my + 12, 4.5, RED, '#fff', 2), sparkle(x + 31, y + 60, 6, BLUE)])

    # Support: a return graded from a photo and sent to its best next use, with the assistant
    def saas_art(x, y, col):
        o = [r(x + 16, y + 14, 56, 56, col['light'], 10), r(x + 30, y + 30, 28, 22, '#fff', 4, RED, 2), c(x + 44, y + 41, 6, 'none', RED, 2),
             f'<path d="M{x+22},{y+20} h7 M{x+22},{y+20} v7 M{x+66},{y+64} h-7 M{x+66},{y+64} v-7" stroke="{RED}" stroke-width="2"/>',
             line(x + 84, y + 18, 80, TEAL_L, 7), r(x + 84, y + 32, 44, 16, '#E6F4EA', 8), line(x + 92, y + 38, 28, '#81C995', 4)]
        o += [c(x + 92 + k * 16, y + 62, 5.5, dot) for k, dot in enumerate([GREEN, BLUE, YELLOW, RED])]
        o += [r(x + w - 52, y + 54, 38, 14, '#E8F0FE', 7)] + [r(x + w - 46 + k * 5, y + 61 - hh / 2, 2.5, hh, BLUE, 1.2) for k, hh in enumerate([4, 8, 6, 9, 5, 3])]
        return ''.join(o)

    cards = [svc_card(i, key, art) for i, (key, art) in enumerate([('maas', maas_art), ('paas', paas_art), ('taas', taas_art), ('saas', saas_art)])]
    o += cards
    o.append('</svg>')
    write('overview.svg', ''.join(o))

    # The same picture in two parts, for the home page banner, which turns them in 3D:
    # the console leans back towards its right edge, the cards lean back towards their left edge.
    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{label}">' + DEFS.format(p=p)
    vb = (WX - 14, WY - 12, WW + 28, WH + 34)
    write('overview-console.svg', head.format(vb=' '.join(f'{v:.1f}' for v in vb), w=vb[2], h=vb[3], label='The AuraCommerce 360 console with its four services')
          + f'<g filter="url(#{p}sh)">{win}</g></svg>')
    vb = (x - 12, 8, w + 24, 4 * (h + gap) + 28)
    write('overview-cards.svg', head.format(vb=' '.join(f'{v:.1f}' for v in vb), w=vb[2], h=vb[3], label='What each service does: access control, live bidding, AI routes and graded returns')
          + ''.join(cards) + '</svg>')

overview()
