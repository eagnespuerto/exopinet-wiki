"""Tkinter UI for browsing the local exoplanet cache."""

import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from . import __version__, classify, db, sync
from .paths import bmp_dir, png_dir


PLACEHOLDER_COLORS = {
    "terrestrial": "#2d6aa7",
    "super-earth": "#8a4a25",
    "mini-neptune": "#3a8f8a",
    "neptune-like": "#1e4fa0",
    "gas-giant": "#b07540",
    "unknown": "#54545c",
}
PLACEHOLDER_BG = "#000814"


SORT_OPTIONS = (
    ("Name", "name", False),
    ("Host star", "host", False),
    ("Discovery year (newest)", "discovery_year", True),
    ("Discovery year (oldest)", "discovery_year", False),
    ("Radius (largest)", "radius_earth", True),
    ("Mass (largest)", "mass_earth", True),
    ("Orbital period (longest)", "period_days", True),
    ("Earth Similarity Index (highest)", "esi", True),
)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"ExoPiNet Wiki {__version__}")
        self.geometry("980x600")
        self.minsize(720, 480)

        self._images: dict = {}
        self._current_image_label: Optional[ttk.Label] = None

        self._build_menu()
        self._build_layout()
        self._reload_list()

    # UI construction -------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Update Data", command=self._start_sync)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._reload_list())
        ttk.Entry(toolbar, textvariable=self.search_var, width=30).pack(
            side=tk.LEFT, padx=(4, 12)
        )

        ttk.Label(toolbar, text="Sort by:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value=SORT_OPTIONS[0][0])
        sort_combo = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            state="readonly",
            values=[label for label, *_ in SORT_OPTIONS],
            width=32,
        )
        sort_combo.pack(side=tk.LEFT, padx=4)
        sort_combo.bind("<<ComboboxSelected>>", lambda _: self._reload_list())

        self.status_var = tk.StringVar(value="")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.RIGHT)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        body.add(left, weight=1)

        cols = ("name", "host", "year", "type", "esi")
        self.tree = ttk.Treeview(
            left, columns=cols, show="headings", selectmode="browse"
        )
        headings = (
            ("name", "Planet", 200),
            ("host", "Host", 120),
            ("year", "Year", 60),
            ("type", "Type", 110),
            ("esi", "ESI", 60),
        )
        for cid, text, width in headings:
            self.tree.heading(cid, text=text)
            self.tree.column(cid, width=width, anchor=tk.W)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(body, padding=12)
        body.add(right, weight=1)

        self.detail_title = ttk.Label(
            right, text="Select a planet", font=("TkDefaultFont", 14, "bold")
        )
        self.detail_title.pack(anchor=tk.W)

        self.image_holder = ttk.Frame(right)
        self.image_holder.pack(anchor=tk.W, fill=tk.X, pady=(6, 12))

        detail_frame = ttk.Frame(right)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        detail_vsb = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL)
        detail_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text = tk.Text(
            detail_frame,
            wrap=tk.WORD,
            borderwidth=0,
            background=self.cget("background"),
            yscrollcommand=detail_vsb.set,
        )
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_vsb.config(command=self.detail_text.yview)
        self.detail_text.configure(state=tk.DISABLED)
        # Explicit mouse-wheel bindings — Tk on X11 (Raspberry Pi OS) doesn't
        # auto-forward wheel events to Text widgets.
        self.detail_text.bind(
            "<MouseWheel>",
            lambda e: self.detail_text.yview_scroll(int(-e.delta / 60), "units"),
        )
        self.detail_text.bind(
            "<Button-4>", lambda _e: self.detail_text.yview_scroll(-3, "units")
        )
        self.detail_text.bind(
            "<Button-5>", lambda _e: self.detail_text.yview_scroll(3, "units")
        )

    # Data -----------------------------------------------------------

    def _reload_list(self) -> None:
        self.tree.delete(*self.tree.get_children())
        label = self.sort_var.get()
        sort_key, descending = "name", False
        for entry_label, col, desc in SORT_OPTIONS:
            if entry_label == label:
                sort_key, descending = col, desc
                break

        with db.connect() as conn:
            total = db.count(conn)
            rows = db.all_planets(
                conn,
                search=self.search_var.get().strip(),
                order_by=sort_key,
                descending=descending,
            )
            last_sync = db.get_meta(conn, "last_sync")

        for row in rows:
            self.tree.insert(
                "",
                tk.END,
                iid=row["key"],
                values=(
                    row["name"],
                    row["host"] or "",
                    row["discovery_year"] or "",
                    classify.DISPLAY.get(row["planet_type"] or "unknown", "Unknown"),
                    f"{row['esi']:.2f}" if row["esi"] is not None else "",
                ),
            )

        shown = len(self.tree.get_children())
        parts = [f"{shown} shown / {total} total"]
        if last_sync:
            parts.append(f"last sync {last_sync}")
        else:
            parts.append("no sync yet — use File → Update Data")
        self.status_var.set("   ".join(parts))

    def _on_select(self, _event) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        key = sel[0]
        with db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM planets WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return
        self._render_detail(dict(row))

    def _render_detail(self, row: dict) -> None:
        self.detail_title.configure(text=row.get("name") or "Unnamed")
        self._show_planet_image(row.get("planet_type") or "unknown")

        def fmt(value, unit="", digits=3):
            if value is None or value == "":
                return "—"
            if isinstance(value, float):
                return f"{value:.{digits}g}{unit}"
            return f"{value}{unit}"

        fields = [
            ("Host star", row.get("host")),
            ("Type", classify.DISPLAY.get(row.get("planet_type") or "unknown", "Unknown")),
            ("Discovery year", row.get("discovery_year")),
            ("Discovery method", row.get("discovery_method")),
            ("Radius", fmt(row.get("radius_earth"), " R⊕")),
            ("Mass", fmt(row.get("mass_earth"), " M⊕")),
            ("Orbital period", fmt(row.get("period_days"), " days")),
            ("Semi-major axis", fmt(row.get("semimajor_au"), " AU")),
            ("Eccentricity", fmt(row.get("eccentricity"))),
            ("Equilibrium temp.", fmt(row.get("eq_temp_k"), " K", 4)),
            ("Star spectral type", row.get("star_spectype")),
            ("Star temp.", fmt(row.get("star_temp_k"), " K", 4)),
            ("Distance", fmt(row.get("star_distance_pc"), " pc")),
            ("Earth Similarity Index", fmt(row.get("esi"))),
            ("Source(s)", row.get("sources")),
        ]

        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        for label, value in fields:
            display = "—" if value in (None, "") else value
            self.detail_text.insert(tk.END, f"{label:<24}", ("label",))
            self.detail_text.insert(tk.END, f"{display}\n")
        self.detail_text.tag_configure("label", font=("TkDefaultFont", 9, "bold"))
        self.detail_text.configure(state=tk.DISABLED)

    def _show_planet_image(self, planet_type: str) -> None:
        for child in self.image_holder.winfo_children():
            child.destroy()
        img = self._load_image(planet_type)
        if img is not None:
            # Plain tk.Label — ttk.Label ignores keep-alive image refs on some
            # older Tk versions, which was making the picture silently vanish.
            label = tk.Label(self.image_holder, image=img, borderwidth=0)
            label.image = img
            label.pack(side=tk.LEFT)
        else:
            self._draw_placeholder(planet_type)
        caption = ttk.Label(
            self.image_holder,
            text=f"{classify.DISPLAY.get(planet_type, 'Unknown')} template",
            padding=(12, 0),
        )
        caption.pack(side=tk.LEFT, anchor=tk.S)

    def _draw_placeholder(self, planet_type: str) -> None:
        """Canvas fallback drawn when the BMP can't be loaded.

        Keeps the layout consistent (no mystery blank space) even if Pillow's
        ImageTk isn't installed or the asset is missing.
        """
        canvas = tk.Canvas(
            self.image_holder,
            width=128,
            height=128,
            highlightthickness=0,
            background=PLACEHOLDER_BG,
        )
        canvas.pack(side=tk.LEFT)
        color = PLACEHOLDER_COLORS.get(planet_type, "#666")
        canvas.create_oval(12, 12, 116, 116, fill=color, outline="")

    def _load_image(self, planet_type: str):
        """Load the planet artwork.

        Preference order:
          1. PNG via native Tk 8.6 PhotoImage (Pi OS ships Tk 8.6, no
             Pillow-ImageTk dependency needed for display).
          2. BMP via Pillow's ImageTk if Pillow is available.

        Returns None if everything failed; the caller then draws a Canvas
        placeholder so nothing appears blank.
        """
        if planet_type in self._images:
            return self._images[planet_type]

        png_path = png_dir() / f"{planet_type}.png"
        if png_path.exists():
            try:
                img = tk.PhotoImage(file=str(png_path))
                self._images[planet_type] = img
                return img
            except tk.TclError as exc:
                print(
                    f"exopinet-wiki: Tk could not decode {png_path}: {exc}",
                    file=sys.stderr,
                )

        bmp_path = bmp_dir() / f"{planet_type}.bmp"
        if bmp_path.exists():
            try:
                from PIL import Image, ImageTk
            except ImportError as exc:
                print(
                    f"exopinet-wiki: Pillow not available ({exc}); install "
                    "python3-pil.imagetk to fall back to BMP artwork.",
                    file=sys.stderr,
                )
            else:
                try:
                    with Image.open(bmp_path) as pil_img:
                        img = ImageTk.PhotoImage(pil_img.copy())
                    self._images[planet_type] = img
                    return img
                except Exception as exc:  # noqa: BLE001 - reported to stderr
                    print(
                        f"exopinet-wiki: failed to load {bmp_path}: {exc}",
                        file=sys.stderr,
                    )

        if not png_path.exists() and not bmp_path.exists():
            print(
                f"exopinet-wiki: no artwork found at {png_path} or {bmp_path}",
                file=sys.stderr,
            )
        return None

    # Actions --------------------------------------------------------

    def _start_sync(self) -> None:
        if getattr(self, "_sync_thread", None) and self._sync_thread.is_alive():
            return

        self.status_var.set("Starting data sync...")

        def worker():
            def report(msg: str) -> None:
                self.after(0, lambda: self.status_var.set(msg))
            try:
                result = sync.refresh(progress=report)
            except Exception as exc:  # noqa: BLE001
                self.after(
                    0,
                    lambda: messagebox.showerror("Sync failed", str(exc)),
                )
                return
            self.after(0, self._reload_list)
            if result.get("errors"):
                self.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Sync completed with warnings", "\n".join(result["errors"])
                    ),
                )

        self._sync_thread = threading.Thread(target=worker, daemon=True)
        self._sync_thread.start()

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About ExoPiNet Wiki",
            "ExoPiNet Wiki\n"
            f"Version {__version__}\n\n"
            "Offline exoplanet browser for Raspberry Pi OS.\n\n"
            "Data: Open Exoplanet Catalogue (CC0) and\n"
            "NASA Exoplanet Archive (public domain).",
        )


def main() -> None:
    App().mainloop()
