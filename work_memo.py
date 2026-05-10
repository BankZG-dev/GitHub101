import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work_memo_data.json")

# ── Color palette ──────────────────────────────────────────────────────────────
BG        = "#F7F6F3"
SURFACE   = "#FFFFFF"
BORDER    = "#E2E0D8"
TEXT      = "#1A1A1A"
MUTED     = "#888780"
ACCENT    = "#4F46E5"       # indigo
HIGH_BG   = "#FCEBEB"
HIGH_FG   = "#A32D2D"
MED_BG    = "#FAEEDA"
MED_FG    = "#854F0B"
LOW_BG    = "#EAF3DE"
LOW_FG    = "#3B6D11"
DONE_FG   = "#AAAAAA"
GREEN     = "#1D9E75"
RED_DEL   = "#E24B4A"

PRIO_COLORS = {
    "High":   (HIGH_BG, HIGH_FG, "#E24B4A"),
    "Medium": (MED_BG,  MED_FG,  "#EF9F27"),
    "Low":    (LOW_BG,  LOW_FG,  "#639922"),
}

# ── Persistence ────────────────────────────────────────────────────────────────

def load_tasks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# ── Main App ───────────────────────────────────────────────────────────────────

class WorkMemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Work Memo")
        self.geometry("700x780")
        self.minsize(520, 500)
        self.configure(bg=BG)

        self.tasks = load_tasks()
        self.current_filter = tk.StringVar(value="All")
        self.selected_prio  = tk.StringVar(value="Medium")
        self.search_var     = tk.StringVar()

        self._build_ui()
        # Attach trace AFTER UI is built so scroll_frame exists
        self.search_var.trace_add("write", lambda *_: self.refresh_list())
        self.refresh_list()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=ACCENT, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📋  Work Memo", font=("Helvetica", 16, "bold"),
                 bg=ACCENT, fg="white").pack(side="left", padx=20, pady=12)

        # ── Add-task panel ──
        panel = tk.Frame(self, bg=SURFACE, bd=0, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER)
        panel.pack(fill="x", padx=16, pady=(14, 0))

        inner = tk.Frame(panel, bg=SURFACE)
        inner.pack(fill="x", padx=16, pady=14)

        # Task title
        tk.Label(inner, text="Task", font=("Helvetica", 11, "bold"),
                 bg=SURFACE, fg=TEXT).grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        title_entry = tk.Entry(inner, textvariable=self.title_var,
                               font=("Helvetica", 12), bg="#F1EFE8", fg=TEXT,
                               relief="flat", bd=6)
        title_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 10))
        title_entry.bind("<Return>", lambda e: self.add_task())

        # Priority buttons
        tk.Label(inner, text="Priority", font=("Helvetica", 11, "bold"),
                 bg=SURFACE, fg=TEXT).grid(row=2, column=0, sticky="w")
        prio_frame = tk.Frame(inner, bg=SURFACE)
        prio_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 10))
        self._prio_btns = {}
        for p in ("High", "Medium", "Low"):
            _, fg, border = PRIO_COLORS[p]
            b = tk.Button(prio_frame, text=p, font=("Helvetica", 10),
                          bg=SURFACE, fg=MUTED, relief="flat", bd=0,
                          padx=14, pady=5, cursor="hand2",
                          command=lambda p=p: self._set_prio(p))
            b.pack(side="left", padx=(0, 6))
            self._prio_btns[p] = b
        self._set_prio("Medium")

        # Memo
        tk.Label(inner, text="Memo / Notes", font=("Helvetica", 11, "bold"),
                 bg=SURFACE, fg=TEXT).grid(row=4, column=0, sticky="w")
        self.memo_text = tk.Text(inner, height=3, font=("Helvetica", 11),
                                 bg="#F1EFE8", fg=TEXT, relief="flat", bd=6,
                                 wrap="word")
        self.memo_text.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 12))

        # Add button
        add_btn = tk.Button(inner, text="＋  Add Task",
                            font=("Helvetica", 11, "bold"),
                            bg=ACCENT, fg="white", relief="flat", bd=0,
                            padx=20, pady=8, cursor="hand2",
                            command=self.add_task,
                            activebackground="#4338CA", activeforeground="white")
        add_btn.grid(row=6, column=0, sticky="w")

        inner.columnconfigure(0, weight=1)

        # ── Stats bar ──
        self.stats_frame = tk.Frame(self, bg=BG)
        self.stats_frame.pack(fill="x", padx=16, pady=(14, 0))
        self._stat_labels = {}
        for key in ("Total", "Open", "Done", "Urgent"):
            card = tk.Frame(self.stats_frame, bg=SURFACE,
                            highlightthickness=1, highlightbackground=BORDER)
            card.pack(side="left", expand=True, fill="x", padx=(0, 8))
            num = tk.Label(card, text="0", font=("Helvetica", 20, "bold"),
                           bg=SURFACE, fg=TEXT)
            num.pack(pady=(10, 0))
            tk.Label(card, text=key, font=("Helvetica", 10),
                     bg=SURFACE, fg=MUTED).pack(pady=(0, 10))
            self._stat_labels[key] = num

        # ── Filters + search ──
        frow = tk.Frame(self, bg=BG)
        frow.pack(fill="x", padx=16, pady=(14, 0))

        self._filter_btns = {}
        for f in ("All", "Open", "Done", "High", "Medium", "Low"):
            b = tk.Button(frow, text=f, font=("Helvetica", 10),
                          bg=SURFACE, fg=MUTED, relief="flat", bd=0,
                          padx=12, pady=5, cursor="hand2",
                          highlightthickness=1, highlightbackground=BORDER,
                          command=lambda f=f: self._set_filter(f))
            b.pack(side="left", padx=(0, 6))
            self._filter_btns[f] = b

        # Search box on right
        search_entry = tk.Entry(frow, textvariable=self.search_var,
                                font=("Helvetica", 10), bg=SURFACE, fg=TEXT,
                                relief="flat", bd=4, width=18)
        search_entry.pack(side="right")
        tk.Label(frow, text="🔍", bg=BG).pack(side="right", padx=(0, 4))

        # highlight default filter button only — no refresh yet (scroll_frame not built)
        for name, btn in self._filter_btns.items():
            btn.configure(bg=TEXT if name == "All" else SURFACE,
                          fg="white" if name == "All" else MUTED)

        # ── Task list (scrollable) ──
        list_container = tk.Frame(self, bg=BG)
        list_container.pack(fill="both", expand=True, padx=16, pady=14)

        canvas = tk.Canvas(list_container, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                  command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=BG)

        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_prio(self, p):
        self.selected_prio.set(p)
        for name, btn in self._prio_btns.items():
            if name == p:
                bg, fg, _ = PRIO_COLORS[name]
                btn.configure(bg=bg, fg=fg,
                              highlightthickness=1,
                              highlightbackground=PRIO_COLORS[name][2])
            else:
                btn.configure(bg=SURFACE, fg=MUTED,
                              highlightthickness=1,
                              highlightbackground=BORDER)

    def _set_filter(self, f):
        self.current_filter.set(f)
        for name, btn in self._filter_btns.items():
            if name == f:
                btn.configure(bg=TEXT, fg="white")
            else:
                btn.configure(bg=SURFACE, fg=MUTED)
        self.refresh_list()

    # ── Task operations ───────────────────────────────────────────────────────

    def add_task(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Empty task", "Please enter a task title.")
            return
        memo = self.memo_text.get("1.0", "end").strip()
        task = {
            "id":    datetime.now().isoformat(),
            "title": title,
            "memo":  memo,
            "prio":  self.selected_prio.get(),
            "done":  False,
            "date":  datetime.now().strftime("%d %b %Y"),
        }
        self.tasks.insert(0, task)
        save_tasks(self.tasks)
        self.title_var.set("")
        self.memo_text.delete("1.0", "end")
        self.refresh_list()

    def toggle_done(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]
                break
        save_tasks(self.tasks)
        self.refresh_list()

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        save_tasks(self.tasks)
        self.refresh_list()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def refresh_list(self):
        if not hasattr(self, "scroll_frame"):
            return
        # Update stats
        total  = len(self.tasks)
        open_  = sum(1 for t in self.tasks if not t["done"])
        done   = sum(1 for t in self.tasks if t["done"])
        urgent = sum(1 for t in self.tasks if t["prio"] == "High" and not t["done"])
        self._stat_labels["Total"].configure(text=str(total))
        self._stat_labels["Open"].configure(text=str(open_))
        self._stat_labels["Done"].configure(text=str(done))
        self._stat_labels["Urgent"].configure(text=str(urgent))

        # Filter
        f = self.current_filter.get()
        q = self.search_var.get().lower()
        filtered = self.tasks
        if f == "Open":   filtered = [t for t in filtered if not t["done"]]
        elif f == "Done": filtered = [t for t in filtered if t["done"]]
        elif f in ("High", "Medium", "Low"):
            filtered = [t for t in filtered if t["prio"] == f]
        if q:
            filtered = [t for t in filtered
                        if q in t["title"].lower() or q in t["memo"].lower()]

        # Clear old cards
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not filtered:
            tk.Label(self.scroll_frame, text="No tasks here yet.",
                     font=("Helvetica", 12), bg=BG, fg=MUTED
                     ).pack(pady=40)
            return

        for task in filtered:
            self._render_card(task)

    def _render_card(self, task):
        prio = task.get("prio", "Medium")
        bg_p, fg_p, bar_color = PRIO_COLORS.get(prio, PRIO_COLORS["Medium"])
        done = task["done"]

        # Outer wrapper for the colored left bar
        wrapper = tk.Frame(self.scroll_frame, bg=BG)
        wrapper.pack(fill="x", pady=(0, 8))

        bar = tk.Frame(wrapper, bg=bar_color, width=4)
        bar.pack(side="left", fill="y")

        card = tk.Frame(wrapper, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(side="left", fill="x", expand=True)

        inner = tk.Frame(card, bg=SURFACE)
        inner.pack(fill="x", padx=14, pady=10)

        # Checkbox
        check_var = tk.BooleanVar(value=done)
        chk = tk.Checkbutton(inner, variable=check_var, bg=SURFACE,
                             activebackground=SURFACE,
                             selectcolor=GREEN if done else SURFACE,
                             command=lambda tid=task["id"]: self.toggle_done(tid))
        chk.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 10), pady=2)

        # Title
        title_fg = DONE_FG if done else TEXT
        title_font = ("Helvetica", 12, "overstrike") if done else ("Helvetica", 12, "bold")
        tk.Label(inner, text=task["title"], font=title_font,
                 bg=SURFACE, fg=title_fg, anchor="w", wraplength=460,
                 justify="left").grid(row=0, column=1, sticky="w")

        # Memo
        if task.get("memo"):
            memo_fg = DONE_FG if done else MUTED
            tk.Label(inner, text=task["memo"], font=("Helvetica", 10),
                     bg=SURFACE, fg=memo_fg, anchor="w", wraplength=460,
                     justify="left").grid(row=1, column=1, sticky="w", pady=(2, 4))

        # Meta row
        meta = tk.Frame(inner, bg=SURFACE)
        meta.grid(row=2, column=1, sticky="w", pady=(4, 0))

        badge = tk.Label(meta, text=prio,
                         font=("Helvetica", 9, "bold"),
                         bg=bg_p, fg=fg_p, padx=8, pady=2)
        badge.pack(side="left", padx=(0, 8))

        tk.Label(meta, text=f"📅 {task.get('date','')}",
                 font=("Helvetica", 9), bg=SURFACE, fg=MUTED
                 ).pack(side="left")

        # Delete button
        del_btn = tk.Button(inner, text="🗑", font=("Helvetica", 12),
                            bg=SURFACE, fg=MUTED, relief="flat", bd=0,
                            cursor="hand2", activebackground=HIGH_BG,
                            activeforeground=RED_DEL,
                            command=lambda tid=task["id"]: self._confirm_delete(tid))
        del_btn.grid(row=0, column=2, rowspan=3, sticky="ne", padx=(10, 0))

        inner.columnconfigure(1, weight=1)

    def _confirm_delete(self, task_id):
        if messagebox.askyesno("Delete task", "Remove this task?"):
            self.delete_task(task_id)


if __name__ == "__main__":
    app = WorkMemoApp()
    app.mainloop()