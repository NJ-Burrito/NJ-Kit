"""Verify a workflow-figure role palette numerically.

  · WCAG 2.1 relative luminance + contrast ratio (w3.org/TR/WCAG21/relative-luminance.html)
  · CIEDE2000 pairwise distance between line colours, under normal vision and
    under Machado et al. (2009) severity-1.0 dichromacy simulations.
"""
import sys, json, math, itertools
import numpy as np

# ── WCAG ────────────────────────────────────────────────────────────────
def srgb(hexs):
    h = hexs.lstrip('#')
    return np.array([int(h[i:i+2], 16) / 255 for i in (0, 2, 4)])

def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def lum(hexs):
    r, g, b = lin(srgb(hexs))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

# ── CIE Lab / CIEDE2000 ─────────────────────────────────────────────────
M_RGB2XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                      [0.2126729, 0.7151522, 0.0721750],
                      [0.0193339, 0.1191920, 0.9503041]])
WHITE = np.array([0.95047, 1.0, 1.08883])

def lab(rgb_lin):
    xyz = M_RGB2XYZ @ rgb_lin / WHITE
    f = np.where(xyz > (6/29)**3, np.cbrt(xyz), xyz / (3 * (6/29)**2) + 4/29)
    return np.array([116*f[1] - 16, 500*(f[0]-f[1]), 200*(f[1]-f[2])])

def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb**7 / (Cb**7 + 25**7))) if Cb > 0 else 0.5
    a1p, a2p = (1+G)*a1, (1+G)*a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17*math.cos(math.radians(hbp-30)) + 0.24*math.cos(math.radians(2*hbp))
         + 0.32*math.cos(math.radians(3*hbp+6)) - 0.20*math.cos(math.radians(4*hbp-63)))
    dTh = 30 * math.exp(-(((hbp-275)/25)**2))
    Rc = 2 * math.sqrt(Cbp**7 / (Cbp**7 + 25**7)) if Cbp > 0 else 0
    Sl = 1 + (0.015 * (Lbp-50)**2) / math.sqrt(20 + (Lbp-50)**2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2*dTh)) * Rc
    return math.sqrt((dLp/Sl)**2 + (dCp/Sc)**2 + (dHp/Sh)**2 + Rt*(dCp/Sc)*(dHp/Sh))

# ── Machado et al. 2009, severity 1.0 (linear-RGB 3x3) ──────────────────
CVD = {
 'protan': np.array([[0.152286, 1.052583, -0.204868],
                     [0.114503, 0.786281,  0.099216],
                     [-0.003882,-0.048116, 1.051998]]),
 'deutan': np.array([[0.367322, 0.860646, -0.227968],
                     [0.280085, 0.672501,  0.047413],
                     [-0.011820, 0.042940, 0.968881]]),
 'tritan': np.array([[1.255528,-0.076749, -0.178779],
                     [-0.078411, 0.930809, 0.147602],
                     [0.004733, 0.691367,  0.303900]]),
}

def sim(hexs, kind):
    return CVD[kind] @ lin(srgb(hexs)) if kind else lin(srgb(hexs))

def main(path):
    P = json.load(open(path, encoding='utf-8'))
    roles = P['roles']
    print('=== WCAG contrast (W3C relative luminance) ===')
    print(f"{'role':<11} {'ink/fill':>9} {'line/fill':>10} {'line/white':>11} {'fill/white':>11}")
    worst_ink = worst_sub = worst_edge = 99
    for k, v in roles.items():
        a = ratio(v['ink'], v['fill'])
        b = ratio(v['line'], v['fill'])
        c = ratio(v['line'], '#FFFFFF')
        d = ratio(v['fill'], '#FFFFFF')
        worst_ink = min(worst_ink, a); worst_sub = min(worst_sub, b); worst_edge = min(worst_edge, c)
        flag = lambda x, t: '' if x >= t else f'  << under {t}'
        print(f'{k:<11} {a:9.2f} {b:10.2f} {c:11.2f} {d:11.2f}'
              + flag(a, 7.0) + flag(b, 4.5) + flag(c, 3.0))
    print(f'\nworst title-ink on fill  {worst_ink:.2f}:1  (AAA body 7:1, AA 4.5:1)')
    print(f'worst subtitle on fill   {worst_sub:.2f}:1  (AA 4.5:1)')
    print(f'worst outline on paper   {worst_edge:.2f}:1  (SC 1.4.11 non-text 3:1)')

    # A terminator is a stadium carrying its own ✓ / ✕ glyph, so colour is not
    # the only thing telling it from a rectangle: those pairs are reported apart.
    # The pairs colour has to carry **alone** are the five task rectangles, and
    # the two terminators against each other.
    ks = list(roles)
    term = {'stop', 'ok'}
    alone = [p for p in itertools.combinations(ks, 2)
             if not (set(p) & term) or set(p) == term]
    shaped = [p for p in itertools.combinations(ks, 2) if p not in alone]
    for what in ('fill', 'line'):
        print(f'\n=== pairwise CIEDE2000 on the {what} — colour is the only channel ===')
        for label, key in (('normal', None), ('protan', 'protan'),
                           ('deutan', 'deutan'), ('tritan', 'tritan')):
            ds = sorted((de2000(lab(sim(roles[x][what], key)), lab(sim(roles[y][what], key))), x, y)
                        for x, y in alone)
            print(f'  {label:<7} min ΔE00 {ds[0][0]:5.2f} ({ds[0][1]}/{ds[0][2]})    then  '
                  + '   '.join(f'{a}/{b} {d:.1f}' for d, a, b in ds[1:3]))
        print('  --- pairs a stadium and a glyph also separate ---')
        for label, key in (('normal', None), ('protan', 'protan'),
                           ('deutan', 'deutan'), ('tritan', 'tritan')):
            ds = sorted((de2000(lab(sim(roles[x][what], key)), lab(sim(roles[y][what], key))), x, y)
                        for x, y in shaped)
            print(f'  {label:<7} min ΔE00 {ds[0][0]:5.2f} ({ds[0][1]}/{ds[0][2]})')

    if 'wires' in P:
        print('\n=== connector inks on paper (SC 1.4.11, 3:1) ===')
        for k, v in P['wires'].items():
            print(f'  {k:<10} {v}  {ratio(v, "#FFFFFF"):.2f}:1')

if __name__ == '__main__':
    main(sys.argv[1])
