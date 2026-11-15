"""Shared look for diagrams and 2D animations, plus small P&ID-style drawing helpers.

    import sys; sys.path.insert(0, "lib")
    from style import *
    fig, ax = new_diagram("Horizontal three-phase separator", "Schematic, not to scale", xlim=(0, 16), ylim=(0, 9.6))
    ... draw ...
    save_diagram(fig, "out/diagram.png")
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, FancyBboxPatch

# palette (keep consistent across every lesson)
BG, PANEL = "#F7F5EF", "#FFFFFF"
INK, MUTED, STEEL, LINE = "#1F2328", "#5B6670", "#4F5B66", "#C9CED3"
TEAL, ACCENT = "#12332F", "#E4572E"
GAS, OIL, WATER, STEAM, HOT, COLD = "#8E9AA6", "#D0892C", "#2F6FC4", "#B9C3CC", "#C0392B", "#2E86C1"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK})


def new_diagram(title, subtitle="", xlim=(0, 16), ylim=(0, 9), size=(12.8, 7.2), dpi=150):
    """Figure with a title band and one equal-aspect drawing axis in data units."""
    fig = plt.figure(figsize=size, dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.86])
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")
    fig.text(0.03, 0.94, title, fontsize=20, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.03, 0.90, subtitle, fontsize=11, color=MUTED)
    return fig, ax


def save_diagram(fig, path):
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


# ---------- drawing helpers (data units) ----------
def pipe(ax, xs, ys, lw=5, color=STEEL, z=0):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt", zorder=z)


def valve(ax, x, y, vertical=False, d=0.28, fc="white"):
    """Gate-valve bow-tie symbol centred on (x, y)."""
    if vertical:
        tris = [[(x - d, y + d), (x + d, y + d), (x, y)], [(x - d, y - d), (x + d, y - d), (x, y)]]
    else:
        tris = [[(x - d, y - d), (x - d, y + d), (x, y)], [(x + d, y - d), (x + d, y + d), (x, y)]]
    for t in tris:
        ax.add_patch(Polygon(t, closed=True, fc=fc, ec=INK, lw=1.5, zorder=6))


def instrument(ax, x, y, tag, r=0.42):
    """ISA-style instrument bubble (e.g. 'PIC', 'LT')."""
    ax.add_patch(Circle((x, y), r, fc="white", ec=INK, lw=1.4, zorder=7))
    ax.text(x, y, tag, ha="center", va="center", fontsize=8.5, fontweight="bold", color=INK, zorder=8)


def signal(ax, xs, ys):
    """Dashed instrument signal line."""
    ax.plot(xs, ys, color=INK, lw=1, ls=(0, (3, 2)), zorder=5)


def label(ax, x, y, text, **kw):
    style = dict(fontsize=10, color=INK, fontweight="bold"); style.update(kw)
    return ax.text(x, y, text, **style)


def callout(ax, xy, xytext, text, **kw):
    """Small italic label with a leader line: use instead of placing text on top of geometry."""
    style = dict(fontsize=8.5, color=STEEL, style="italic"); style.update(kw)
    return ax.annotate(text, xy, xytext, arrowprops=dict(arrowstyle="-", color=STEEL, lw=0.8), **style)


def vessel_h(ax, x, y, w, h, **kw):
    """Horizontal vessel shell (rounded ends). Returns the patch (use it as a clip path)."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=kw.get("fc", "white"),
                       ec=kw.get("ec", STEEL), lw=kw.get("lw", 3), zorder=kw.get("zorder", 1))
    ax.add_patch(p); return p


def vessel_v(ax, x, y, w, h, **kw):
    """Vertical vessel shell (rounded heads)."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={w / 2}", fc=kw.get("fc", "white"),
                       ec=kw.get("ec", STEEL), lw=kw.get("lw", 3), zorder=kw.get("zorder", 1))
    ax.add_patch(p); return p


def fill_clipped(ax, clip, x, y, w, h, color, alpha=0.3, z=2):
    r = Rectangle((x, y), w, h, fc=color, alpha=alpha, ec="none", zorder=z)
    ax.add_patch(r); r.set_clip_path(clip); return r


# ---------- motion helpers ----------
def polyline(pts):
    """Return f(u) -> point along the polyline, u in [0, 1) wrapping."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])

    def f(u):
        d = (u % 1.0) * cum[-1]
        i = int(np.clip(np.searchsorted(cum, d) - 1, 0, len(seg) - 1))
        r = (d - cum[i]) / (seg[i] or 1)
        return pts[i] + (pts[i + 1] - pts[i]) * r
    return f


class Particles:
    """Families of dots moving along paths (flows, droplets, bubbles)."""

    def __init__(self, seed=7):
        self.rng = np.random.default_rng(seed)
        self.fams = []

    def add(self, n, make_path, speed, colour, size):
        """make_path(k, rng) -> polyline(...); speed in path-lengths per second; colour str or list."""
        paths = [make_path(k, self.rng) for k in range(n)]
        self.fams.append((paths, self.rng.random(n), speed * (0.85 + 0.3 * self.rng.random(n)), colour, size))

    def at(self, t):
        xy, cs, ss = [], [], []
        for paths, ph, sp, col, size in self.fams:
            for k, p in enumerate(paths):
                xy.append(p(ph[k] + sp[k] * t))
                cs.append(col[k % len(col)] if isinstance(col, (list, tuple)) else col)
                ss.append(size)
        return (np.array(xy) if xy else np.zeros((0, 2))), cs, ss
