"""Example lesson media: separator diagram (PNG) + 2D narrated animation (MP4).
Run from the repo root:
    python3 lib/narrate.py examples/separator_2d/script.json work/sep2d
    python3 examples/separator_2d/make.py work/sep2d out/sep2d [max_seconds]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
from style import *
from anim2d import Anim2D

WORK, OUT = sys.argv[1], sys.argv[2]
MAXS = float(sys.argv[3]) if len(sys.argv) > 3 else 0
os.makedirs(OUT, exist_ok=True)
XL, YL = (0, 16), (0, 9.6)


def draw_static(ax, labels=True):
    shell = vessel_h(ax, 2.2, 2.5, 10.6, 4.0)
    fill_clipped(ax, shell, 2.0, 2.4, 8.0, 1.0, WATER, 0.30)      # water layer
    fill_clipped(ax, shell, 2.0, 3.4, 8.0, 0.9, OIL, 0.28)        # oil layer
    fill_clipped(ax, shell, 10.05, 2.4, 3.0, 0.9, OIL, 0.28)      # oil compartment
    ax.plot([2.4, 9.98], [4.3, 4.3], color=OIL, lw=1.2, zorder=3)
    ax.plot([2.4, 9.98], [3.4, 3.4], color=WATER, lw=1, ls="--", zorder=3)
    ax.add_patch(Rectangle((9.98, 2.5), 0.12, 1.85, fc=STEEL, ec="none", zorder=4))   # weir
    ax.add_patch(Rectangle((2.95, 4.9), 0.12, 1.2, fc=STEEL, ec="none", zorder=4))    # diverter
    ax.add_patch(Rectangle((10.9, 5.2), 1.0, 0.85, fc="white", ec=STEEL, hatch="xxxx", lw=1.2, zorder=4))  # mist pad
    pipe(ax, [0.3, 2.6], [5.8, 5.8]); pipe(ax, [11.6, 11.6, 15.8], [6.25, 8.0, 8.0])
    pipe(ax, [8.5, 8.5], [2.55, 0.4]); pipe(ax, [12.0, 12.0], [2.55, 0.4]); pipe(ax, [7.0, 7.0], [6.45, 7.6])
    valve(ax, 14.0, 8.0); valve(ax, 8.5, 1.3, True); valve(ax, 12.0, 1.3, True)
    ax.add_patch(Polygon([(6.75, 7.6), (7.25, 7.6), (7.0, 8.05)], closed=True, fc="white", ec=INK, lw=1.5, zorder=6))
    instrument(ax, 14.0, 8.9, "PIC"); signal(ax, [14.0, 14.0], [8.48, 8.28])
    instrument(ax, 13.7, 3.4, "LIC"); signal(ax, [13.28, 12.25], [3.2, 3.1]); signal(ax, [13.7, 13.7, 12.28], [2.98, 1.3, 1.3])
    instrument(ax, 6.9, 1.3, "LIC"); signal(ax, [6.9, 6.9], [1.72, 2.6]); signal(ax, [7.32, 8.22], [1.3, 1.3])
    label(ax, 7.35, 7.85, "PSV", fontsize=9, va="center")
    if labels:
        label(ax, 0.3, 6.15, "Well stream in"); label(ax, 14.2, 7.45, "Gas out")
        label(ax, 8.7, 0.45, "Water out"); label(ax, 12.2, 0.45, "Oil / condensate out")
        callout(ax, (3.0, 6.1), (3.3, 7.3), "inlet diverter"); callout(ax, (11.85, 5.7), (12.9, 6.7), "mist extractor")
        small = dict(fontsize=8.5, color=STEEL, style="italic", fontweight="normal")
        label(ax, 9.55, 4.5, "weir", **small); label(ax, 5.6, 5.5, "gas", **small)
        label(ax, 5.6, 3.75, "oil / condensate", **small); label(ax, 5.6, 2.85, "water", **small)
        label(ax, 5.0, 0.95, "interface level", **small); label(ax, 13.95, 2.95, "oil level", **small)


P = Particles(7)
P.add(10, lambda k, r: polyline([(0.4, 5.8), (2.95, 5.8)]), 0.9, [GAS, OIL, WATER], 26)
P.add(28, lambda k, r: (lambda y: polyline([(3.05, 5.8), (3.4, y), (10.7, y), (11.4, 5.7), (11.6, 6.4), (11.6, 8.0), (15.6, 8.0)]))(4.75 + 1.45 * r.random()), 0.16, GAS, 30)
P.add(8, lambda k, r: polyline([(3.0, 5.6), (3.15, 4.9), (3.35 + 0.4 * r.random(), 4.3)]), 0.7, [OIL, WATER], 22)
P.add(14, lambda k, r: (lambda x, y: polyline([(x, y), (x + 2.2, 4.3)]))(3.6 + 6.0 * r.random(), 5.6 + 0.6 * r.random()), 0.28, [OIL, WATER], 14)
P.add(5, lambda k, r: (lambda x: polyline([(x, 5.2), (x, 3.3)]))(11.0 + 0.8 * r.random()), 0.45, OIL, 12)
P.add(16, lambda k, r: (lambda x: polyline([(x, 4.15), (x + 0.4, 2.75)]))(3.6 + 5.8 * r.random()), 0.22, WATER, 18)
P.add(16, lambda k, r: (lambda x: polyline([(x, 2.7), (x + 0.4, 4.1)]))(3.6 + 5.8 * r.random()), 0.22, OIL, 18)
P.add(8, lambda k, r: polyline([(8.4, 4.1), (9.95, 4.32), (10.35, 4.15), (10.55, 3.3)]), 0.35, OIL, 20)
P.add(5, lambda k, r: polyline([(8.5, 2.6), (8.5, 0.5)]), 0.35, WATER, 20)
P.add(5, lambda k, r: polyline([(12.0, 2.6), (12.0, 0.5)]), 0.35, OIL, 20)

# still diagram
fig, ax = new_diagram("Horizontal three-phase separator",
                      "Gravity + time split the well stream into gas, oil/condensate and water. Schematic, not to scale.", XL, YL)
draw_static(ax)
xy, cs, ss = P.at(3.0); ax.scatter(xy[:, 0], xy[:, 1], c=cs, s=ss, zorder=5, edgecolors="none")
save_diagram(fig, os.path.join(OUT, "diagram.png"))

# animation
HL = {"inlet": (0.3, 4.4, 3.6, 6.6), "settling": (3.3, 4.4, 11.4, 6.5), "mist": (10.7, 4.9, 12.1, 6.6),
      "retention": (2.4, 2.5, 9.9, 4.4), "weir": (8.3, 2.5, 12.8, 4.6), "control": (5.8, 0.6, 14.6, 9.0)}
A = Anim2D(os.path.join(WORK, "timeline.json"), os.path.join(WORK, "narration.wav"), os.path.join(OUT, "animation.mp4"),
           tag="Three-phase separator", xlim=XL, ylim=YL, max_seconds=MAXS)
draw_static(A.ax)
sc = A.ax.scatter([], [], s=[], zorder=5, edgecolors="none")


def update(t, line):
    xy, cs, ss = P.at(t); sc.set_offsets(xy); sc.set_color(cs); sc.set_sizes(ss)
    A.highlight(HL.get(line["scene"]), t)


A.run(update)
