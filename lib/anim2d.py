"""2D narrated animation: matplotlib frames piped to ffmpeg, synced to timeline.json.

    import sys; sys.path.insert(0, "lib")
    from style import *
    from anim2d import Anim2D

    A = Anim2D("work/timeline.json", "work/narration.wav", "out/animation.mp4", tag="Three-phase separator",
               xlim=(0, 16), ylim=(0, 9.6))
    draw_static(A.ax)                          # your lesson drawing
    sc = A.ax.scatter([], [], s=[], zorder=5, edgecolors="none")
    HL = {"inlet": (0.3, 4.4, 3.6, 6.6)}       # optional highlight box per scene key

    def update(t, line):                       # called every frame
        xy, cs, ss = parts.at(t); sc.set_offsets(xy); sc.set_color(cs); sc.set_sizes(ss)
        A.highlight(HL.get(line["scene"]), t)

    A.run(update)

Title shows line["title"] (falls back to the last non-empty title); captions show line["caption"];
a progress bar runs along the bottom. Check frames are saved as check_*.png for review.
"""
import json, os, subprocess, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from style import BG, INK, MUTED, TEAL, ACCENT


class Anim2D:
    def __init__(self, timeline, audio, out_mp4, tag="", xlim=(0, 16), ylim=(0, 9), fps=20, size=(12.8, 7.2),
                 max_seconds=0, checks=(0.25, 0.5, 0.8)):
        self.tl = json.load(open(timeline))
        self.audio, self.out, self.fps, self.size = audio, out_mp4, fps, size
        self.total = min(self.tl["total"], max_seconds) if max_seconds else self.tl["total"]
        self.checks = checks
        self.fig = plt.figure(figsize=size, dpi=100, facecolor=BG)
        self.ax = self.fig.add_axes([0.02, 0.12, 0.96, 0.78])
        self.ax.set_xlim(*xlim); self.ax.set_ylim(*ylim); self.ax.set_aspect("equal"); self.ax.axis("off")
        self.title = self.fig.text(0.03, 0.935, "", fontsize=20, fontweight="bold", color=INK)
        self.fig.text(0.97, 0.94, tag, fontsize=11, color=MUTED, ha="right")
        self.fig.add_artist(Rectangle((0, 0), 1, 0.105, transform=self.fig.transFigure, fc=TEAL, ec="none"))
        self.cap = self.fig.text(0.5, 0.052, "", fontsize=15, color="white", ha="center", va="center")
        self.bar = self.fig.add_artist(Rectangle((0, 0.105), 0, 0.006, transform=self.fig.transFigure, fc=ACCENT, ec="none"))
        self.hl = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.1,rounding_size=0.3", fc="none", ec=ACCENT,
                                 lw=3, zorder=9, visible=False)
        self.ax.add_patch(self.hl)

    def line_at(self, t):
        L = self.tl["lines"]; cur = L[0]
        for ln in L:
            if t >= ln["start"] - 0.2:
                cur = ln
        return cur

    def title_at(self, t):
        title = ""
        for ln in self.tl["lines"]:
            if ln["start"] - 0.2 <= t and ln.get("title"):
                title = ln["title"]
        return title

    def caption_at(self, t):
        for ln in self.tl["lines"]:
            if ln["start"] - 0.1 <= t <= ln["end"] + 0.35:
                return ln["caption"]
        return ""

    def highlight(self, box, t):
        """box = (x0, y0, x1, y1) in data units, or None to hide."""
        if box:
            x0, y0, x1, y1 = box
            self.hl.set_bounds(x0, y0, x1 - x0, y1 - y0); self.hl.set_visible(True)
            self.hl.set_alpha(0.55 + 0.45 * abs(np.sin(t * 2.2)))
        else:
            self.hl.set_visible(False)

    def run(self, update):
        W, H = int(self.size[0] * 100), int(self.size[1] * 100)
        os.makedirs(os.path.dirname(os.path.abspath(self.out)), exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", str(self.fps), "-i", "-", "-i", self.audio, "-c:v", "libx264", "-preset", "veryfast",
                               "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest",
                               "-movflags", "+faststart", self.out], stdin=subprocess.PIPE)
        n = int(self.total * self.fps)
        check_frames = {int(n * c) for c in self.checks}
        out_dir = os.path.dirname(os.path.abspath(self.out))
        for i in range(n):
            t = i / self.fps
            line = self.line_at(t)
            self.title.set_text(self.title_at(t))
            update(t, line)
            self.cap.set_text("\n".join(textwrap.wrap(self.caption_at(t), 95)))
            self.bar.set_width(t / self.total)
            self.fig.canvas.draw()
            ff.stdin.write(self.fig.canvas.buffer_rgba().tobytes())
            if i in check_frames:
                self.fig.savefig(os.path.join(out_dir, f"check2d_{i}.png"), facecolor=BG, dpi=60)
        ff.stdin.close(); ff.wait()
        if ff.returncode:
            raise SystemExit(f"ffmpeg failed ({ff.returncode})")
        print(f"2D video {self.total:.1f}s, {n} frames -> {self.out}")
