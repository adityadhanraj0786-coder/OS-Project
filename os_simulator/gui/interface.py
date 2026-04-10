import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from deadlock.detection import analyze_deadlock
from deadlock.recovery import recover_deadlock
from resource_manager.manager import ResourceManager
from scheduler.fcfs import fcfs_scheduling
from scheduler.metrics import build_schedule_report, clone_processes, compare_algorithms
from scheduler.priority import priority_scheduling
from scheduler.round_robin import round_robin_scheduling
from scheduler.sjf import sjf_scheduling
from visualization.gantt_chart import build_gantt_figure
from visualization.graph_visual import build_deadlock_figure


ALGORITHM_DETAILS = {
    "FCFS": "First Come First Serve runs processes in arrival order. It is simple and predictable.",
    "SJF": "Shortest Job First selects the shortest ready burst. It often lowers waiting time.",
    "RR": "Round Robin time-slices the CPU. Time quantum is required and arrivals are respected.",
    "PRIORITY": "Non-preemptive Priority Scheduling selects the ready process with the lowest priority value.",
}

APP_BG = "#f5efe4"
CARD_BG = "#fffaf2"
INK = "#14213d"
MUTED = "#6b7280"
ACCENT = "#c2410c"
ACCENT_DARK = "#9a3412"
WARNING = "#92400e"
BORDER = "#dbcbb0"
SUMMARY_BG = "#f7f1e7"


def format_table(headers, rows):
    string_rows = [[str(cell) for cell in row] for row in rows]
    widths = []

    for index, header in enumerate(headers):
        column_values = [row[index] for row in string_rows] if string_rows else []
        if column_values:
            widths.append(max(len(str(header)), max(len(value) for value in column_values)))
        else:
            widths.append(len(str(header)))

    header_line = " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers))
    separator_line = "-+-".join("-" * width for width in widths)
    body_lines = [
        " | ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        for row in string_rows
    ]

    return "\n".join([header_line, separator_line, *body_lines]) if body_lines else "\n".join(
        [header_line, separator_line, "(no data)"]
    )


def format_float(value):
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def format_resource_map(mapping):
    if not mapping:
        return "None"

    parts = []
    for key in sorted(mapping.keys()):
        value = mapping[key]
        if isinstance(value, list):
            rendered = ", ".join(value) if value else "None"
        else:
            rendered = str(value)
        parts.append(f"{key}: {rendered}")
    return "; ".join(parts)


class ScrollableSidebar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Root.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            background=APP_BG,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="Root.TFrame")
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.content.bind("<Enter>", self._bind_mousewheel)
        self.content.bind("<Leave>", self._unbind_mousewheel)

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")


class OSSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced OS Process Simulator")
        self.root.geometry("1420x900")
        self.root.minsize(1220, 760)
        self._open_full_screen()

        self.processes = []
        self.resource_requests = []
        self.graph_steps = []
        self.current_graph_index = 0
        self.graph_canvas = None
        self.last_report_text = ""
        self.workspace_sash_initialized = False

        self.algo_var = tk.StringVar(value="FCFS")
        self.quantum_var = tk.StringVar(value="2")
        self.algorithm_help_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready. Add processes or load the sample scenario.")
        self.graph_title_var = tk.StringVar(value="Run a simulation to generate charts.")
        self.summary_algorithm_var = tk.StringVar(value="No run yet")
        self.summary_process_var = tk.StringVar(value="0 processes")
        self.summary_resource_var = tk.StringVar(value="0 resources")
        self.summary_deadlock_var = tk.StringVar(value="No analysis yet")

        self.pid_var = tk.StringVar()
        self.arrival_var = tk.StringVar()
        self.burst_var = tk.StringVar()
        self.priority_var = tk.StringVar()
        self.resource_pair_var = tk.StringVar()

        self._configure_style()
        self._build_layout()
        self._update_algorithm_state()
        self._display_welcome_message()
        self.root.protocol("WM_DELETE_WINDOW", self._close_app)

    def _open_full_screen(self):
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

    def _configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background=APP_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Card.TLabelframe", background=CARD_BG, padding=14, borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=APP_BG, foreground=INK, font=("Segoe UI Semibold", 10))
        style.configure("Title.TLabel", background=APP_BG, foreground=INK, font=("Georgia", 22, "bold"))
        style.configure("HeroTitle.TLabel", background=CARD_BG, foreground=INK, font=("Georgia", 24, "bold"))
        style.configure("HeroBody.TLabel", background=CARD_BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("SectionTitle.TLabel", background=CARD_BG, foreground=INK, font=("Segoe UI Semibold", 10))
        style.configure("Muted.TLabel", background=APP_BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("CardMuted.TLabel", background=CARD_BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Hint.TLabel", background=CARD_BG, foreground=MUTED, wraplength=340, font=("Segoe UI", 9))
        style.configure("GraphTitle.TLabel", background=CARD_BG, foreground=INK, font=("Segoe UI Semibold", 10))
        style.configure("Tile.TFrame", background=SUMMARY_BG, relief="solid", borderwidth=1)
        style.configure("TileValue.TLabel", background=SUMMARY_BG, foreground=INK, font=("Segoe UI Semibold", 15))
        style.configure("TileLabel.TLabel", background=SUMMARY_BG, foreground=MUTED, font=("Segoe UI", 8))
        style.configure("Status.TLabel", background="#e8dcc7", foreground=INK, padding=9, font=("Segoe UI", 9))
        style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), foreground="#ffffff", background=ACCENT)
        style.map("Primary.TButton", background=[("active", ACCENT_DARK), ("disabled", "#94a3b8")])
        style.configure("TButton", padding=(8, 5), font=("Segoe UI", 9))
        style.configure("TLabel", background=CARD_BG, foreground=INK, font=("Segoe UI", 9))
        style.configure("TEntry", padding=4)
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#e9ddca", foreground=INK)
        style.map("Treeview", background=[("selected", "#fcd6b3")], foreground=[("selected", INK)])

    def _build_layout(self):
        main_frame = ttk.Frame(self.root, style="Root.TFrame", padding=14)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        header_card = ttk.Frame(main_frame, style="Card.TFrame", padding=18)
        header_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header_card.columnconfigure(0, weight=1)

        ttk.Label(header_card, text="OS Process Simulator", style="HeroTitle.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header_card,
            text="A single-screen operating system lab for scheduling, deadlock analysis, and resource behavior.",
            style="HeroBody.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        body_frame = ttk.Frame(main_frame, style="Root.TFrame")
        body_frame.grid(row=1, column=0, sticky="nsew")
        body_frame.columnconfigure(1, weight=1)
        body_frame.rowconfigure(0, weight=1)

        sidebar_shell = ttk.Frame(body_frame, style="Root.TFrame", width=430)
        sidebar_shell.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        sidebar_shell.grid_propagate(False)
        sidebar_shell.columnconfigure(0, weight=1)
        sidebar_shell.rowconfigure(0, weight=1)

        self.sidebar = ScrollableSidebar(sidebar_shell)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self._build_left_panel(self.sidebar.content)

        workspace = ttk.Frame(body_frame, style="Root.TFrame")
        workspace.grid(row=0, column=1, sticky="nsew")
        self._build_right_panel(workspace)

        ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel").grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(14, 0),
        )

    def _build_left_panel(self, parent):
        parent.columnconfigure(0, weight=1)

        scheduler_card = ttk.LabelFrame(parent, text="Scheduler", style="Card.TLabelframe")
        scheduler_card.pack(fill="x", pady=(0, 12))
        scheduler_card.columnconfigure(1, weight=1)

        ttk.Label(scheduler_card, text="Algorithm").grid(row=0, column=0, sticky="w")
        algorithm_menu = ttk.Combobox(
            scheduler_card,
            textvariable=self.algo_var,
            values=("FCFS", "SJF", "RR", "PRIORITY"),
            state="readonly",
        )
        algorithm_menu.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        algorithm_menu.bind("<<ComboboxSelected>>", lambda _event: self._update_algorithm_state())

        ttk.Label(scheduler_card, text="Time Quantum").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.quantum_entry = ttk.Entry(scheduler_card, textvariable=self.quantum_var)
        self.quantum_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        ttk.Label(scheduler_card, textvariable=self.algorithm_help_var, style="Hint.TLabel").grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )

        self._build_run_controls(scheduler_card)

        utility_card = ttk.LabelFrame(parent, text="Utilities", style="Card.TLabelframe")
        utility_card.pack(fill="x", pady=(0, 12))
        ttk.Button(utility_card, text="Load Sample Scenario", command=self._load_sample_data).pack(fill="x")
        ttk.Button(utility_card, text="Export Report", command=self._export_report).pack(fill="x", pady=8)
        ttk.Button(utility_card, text="Reset Everything", command=self._reset_all).pack(fill="x")

        process_card = ttk.LabelFrame(parent, text="Process Builder", style="Card.TLabelframe")
        process_card.pack(fill="x", pady=(0, 12))
        process_card.columnconfigure(1, weight=1)
        process_card.columnconfigure(3, weight=1)

        ttk.Label(process_card, text="Process ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(process_card, textvariable=self.pid_var).grid(row=0, column=1, sticky="ew", padx=(8, 12))
        ttk.Label(process_card, text="Arrival").grid(row=0, column=2, sticky="w")
        ttk.Entry(process_card, textvariable=self.arrival_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(process_card, text="Burst").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(process_card, textvariable=self.burst_var).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(8, 12),
            pady=(10, 0),
        )
        ttk.Label(process_card, text="Priority").grid(row=1, column=2, sticky="w", pady=(10, 0))
        ttk.Entry(process_card, textvariable=self.priority_var).grid(row=1, column=3, sticky="ew", pady=(10, 0))

        process_actions = ttk.Frame(process_card, style="Card.TFrame")
        process_actions.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(12, 10))
        for column_index in range(3):
            process_actions.columnconfigure(column_index, weight=1)
        ttk.Button(process_actions, text="Add Process", command=self._add_process).grid(row=0, column=0, sticky="ew")
        ttk.Button(process_actions, text="Update Selected", command=self._update_selected_process).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=6,
        )
        ttk.Button(process_actions, text="Remove Selected", command=self._remove_selected_process).grid(
            row=0,
            column=2,
            sticky="ew",
        )

        ttk.Label(
            process_card,
            text="Selection fills the form automatically. Lower priority value means higher importance.",
            style="Hint.TLabel",
        ).grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 8))

        process_table_frame = ttk.Frame(process_card, style="Card.TFrame")
        process_table_frame.grid(row=4, column=0, columnspan=4, sticky="nsew")
        process_table_frame.columnconfigure(0, weight=1)
        process_table_frame.rowconfigure(0, weight=1)

        self.process_tree = ttk.Treeview(
            process_table_frame,
            columns=("pid", "arrival", "burst", "priority"),
            show="headings",
            height=6,
        )
        for column, heading, width in (
            ("pid", "Process", 112),
            ("arrival", "Arrival", 72),
            ("burst", "Burst", 72),
            ("priority", "Priority", 72),
        ):
            self.process_tree.heading(column, text=heading)
            self.process_tree.column(column, width=width, anchor="center")
        process_scroll = ttk.Scrollbar(process_table_frame, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=process_scroll.set)
        self.process_tree.grid(row=0, column=0, sticky="nsew")
        process_scroll.grid(row=0, column=1, sticky="ns")
        self.process_tree.bind("<<TreeviewSelect>>", self._populate_process_form)

        resource_card = ttk.LabelFrame(parent, text="Resource Requests", style="Card.TLabelframe")
        resource_card.pack(fill="x", pady=(0, 12))
        resource_card.columnconfigure(0, weight=1)

        resource_entry_row = ttk.Frame(resource_card, style="Card.TFrame")
        resource_entry_row.grid(row=0, column=0, sticky="ew")
        resource_entry_row.columnconfigure(0, weight=1)
        resource_pair_entry = ttk.Entry(resource_entry_row, textvariable=self.resource_pair_var)
        resource_pair_entry.grid(row=0, column=0, sticky="ew")
        resource_pair_entry.bind("<Return>", lambda _event: self._add_resource_request_pair())
        ttk.Button(resource_entry_row, text="Add Request", command=self._add_resource_request_pair).grid(
            row=0,
            column=1,
            padx=(8, 0),
        )

        ttk.Label(
            resource_card,
            text="Use P1,R1 format only. The simulator creates resources dynamically from these requests.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, sticky="ew", pady=(10, 8))

        resource_table_frame = ttk.Frame(resource_card, style="Card.TFrame")
        resource_table_frame.grid(row=2, column=0, sticky="nsew")
        resource_table_frame.columnconfigure(0, weight=1)
        resource_table_frame.rowconfigure(0, weight=1)

        self.resource_tree = ttk.Treeview(
            resource_table_frame,
            columns=("order", "process", "resource"),
            show="headings",
            height=6,
        )
        for column, heading, width in (
            ("order", "#", 48),
            ("process", "Process", 96),
            ("resource", "Resource", 96),
        ):
            self.resource_tree.heading(column, text=heading)
            self.resource_tree.column(column, width=width, anchor="center")
        resource_scroll = ttk.Scrollbar(resource_table_frame, orient="vertical", command=self.resource_tree.yview)
        self.resource_tree.configure(yscrollcommand=resource_scroll.set)
        self.resource_tree.grid(row=0, column=0, sticky="nsew")
        resource_scroll.grid(row=0, column=1, sticky="ns")

        ttk.Button(resource_card, text="Remove Selected", command=self._remove_selected_request).grid(
            row=3,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

        ttk.Label(
            parent,
            text="The left panel scrolls if your screen is smaller, so controls never overlap.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_run_controls(self, parent):
        ttk.Button(parent, text="Run Selected + Compare", command=self._run_simulation, style="Primary.TButton").grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 8),
        )

        quick_run_frame = ttk.Frame(parent, style="Card.TFrame")
        quick_run_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        quick_run_frame.columnconfigure(0, weight=1)
        quick_run_frame.columnconfigure(1, weight=1)
        ttk.Button(quick_run_frame, text="Run FCFS", command=lambda: self._run_algorithm_shortcut("FCFS")).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(quick_run_frame, text="Run SJF", command=lambda: self._run_algorithm_shortcut("SJF")).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )
        ttk.Button(quick_run_frame, text="Run RR", command=lambda: self._run_algorithm_shortcut("RR")).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )
        ttk.Button(
            quick_run_frame,
            text="Run Priority",
            command=lambda: self._run_algorithm_shortcut("PRIORITY"),
        ).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))

    def _build_right_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        summary_frame = ttk.Frame(parent, style="Root.TFrame")
        summary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for column_index in range(4):
            summary_frame.columnconfigure(column_index, weight=1)
        self._build_summary_tile(summary_frame, 0, "Algorithm", self.summary_algorithm_var)
        self._build_summary_tile(summary_frame, 1, "Processes", self.summary_process_var)
        self._build_summary_tile(summary_frame, 2, "Resources", self.summary_resource_var)
        self._build_summary_tile(summary_frame, 3, "Deadlock", self.summary_deadlock_var)

        self.workspace_pane = ttk.Panedwindow(parent, orient="vertical")
        self.workspace_pane.grid(row=1, column=0, sticky="nsew")
        self.workspace_pane.bind("<Configure>", self._initialize_workspace_sash)

        output_frame = ttk.LabelFrame(parent, text="Simulation Report", style="Card.TLabelframe")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        report_frame = ttk.Frame(output_frame, style="Card.TFrame")
        report_frame.grid(row=0, column=0, sticky="nsew")
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)

        self.report_text = tk.Text(
            report_frame,
            wrap="none",
            font=("Consolas", 9),
            bg="#fffdf9",
            fg=INK,
            insertbackground=INK,
            selectbackground="#f3c6a4",
            relief="flat",
            padx=12,
            pady=10,
        )
        report_scroll_y = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        report_scroll_x = ttk.Scrollbar(report_frame, orient="horizontal", command=self.report_text.xview)
        self.report_text.configure(yscrollcommand=report_scroll_y.set, xscrollcommand=report_scroll_x.set)
        self.report_text.grid(row=0, column=0, sticky="nsew")
        report_scroll_y.grid(row=0, column=1, sticky="ns")
        report_scroll_x.grid(row=1, column=0, sticky="ew")

        visuals_container = ttk.LabelFrame(parent, text="Interactive Visualization", style="Card.TLabelframe")
        visuals_container.columnconfigure(0, weight=1)
        visuals_container.rowconfigure(1, weight=1)

        visual_controls = ttk.Frame(visuals_container, style="Card.TFrame")
        visual_controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        visual_controls.columnconfigure(0, weight=1)

        ttk.Label(visual_controls, textvariable=self.graph_title_var, style="GraphTitle.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            visual_controls,
            text="Drag the divider above this card to resize the graph area. Green solid = allocated, red dashed = waiting.",
            style="CardMuted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        nav_frame = ttk.Frame(visual_controls, style="Card.TFrame")
        nav_frame.grid(row=0, column=1, rowspan=2, sticky="e")
        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self._show_previous_graph)
        self.prev_button.grid(row=0, column=0)
        self.next_button = ttk.Button(nav_frame, text="Next", command=self._show_next_graph)
        self.next_button.grid(row=0, column=1, padx=(6, 0))
        ttk.Button(nav_frame, text="More Graph", command=self._expand_graph_area).grid(row=1, column=0, pady=(6, 0))
        ttk.Button(nav_frame, text="Balanced", command=self._balance_workspace_split).grid(
            row=1,
            column=1,
            padx=(6, 0),
            pady=(6, 0),
        )

        self.graph_frame = ttk.Frame(visuals_container, style="Card.TFrame")
        self.graph_frame.grid(row=1, column=0, sticky="nsew")

        self.workspace_pane.add(output_frame, weight=2)
        self.workspace_pane.add(visuals_container, weight=3)
        self.root.after(150, self._balance_workspace_split)

        self._update_graph_navigation()

    def _build_summary_tile(self, parent, column, label, value_var):
        tile = ttk.Frame(parent, style="Tile.TFrame", padding=12)
        tile.grid(row=0, column=column, sticky="ew", padx=(0, 10) if column < 3 else (0, 0))
        tile.columnconfigure(0, weight=1)
        ttk.Label(tile, text=label, style="TileLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tile, textvariable=value_var, style="TileValue.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _set_workspace_sash(self, output_ratio):
        if not hasattr(self, "workspace_pane"):
            return

        self.root.update_idletasks()
        total_height = self.workspace_pane.winfo_height()
        if total_height <= 1:
            self.root.after(120, lambda: self._set_workspace_sash(output_ratio))
            return

        sash_y = max(180, min(int(total_height * output_ratio), total_height - 220))
        try:
            self.workspace_pane.sashpos(0, sash_y)
            self.workspace_sash_initialized = True
        except tk.TclError:
            pass

    def _initialize_workspace_sash(self, _event=None):
        if not self.workspace_sash_initialized:
            self._balance_workspace_split()

    def _balance_workspace_split(self):
        self._set_workspace_sash(0.42)

    def _expand_graph_area(self):
        self._set_workspace_sash(0.28)

    def _update_algorithm_state(self):
        algorithm = self.algo_var.get()
        self.algorithm_help_var.set(ALGORITHM_DETAILS[algorithm])

        if algorithm == "RR":
            self.quantum_entry.configure(state="normal")
        else:
            self.quantum_entry.configure(state="disabled")

        self.summary_algorithm_var.set(algorithm.replace("PRIORITY", "Priority"))

    def _update_summary_cards(self, schedule_report=None, deadlock_report=None):
        self.summary_process_var.set(f"{len(self.processes)} process(es)")
        unique_resources = sorted({resource_id for _, resource_id in self.resource_requests})
        self.summary_resource_var.set(f"{len(unique_resources)} resource(s)")

        if schedule_report is not None:
            self.summary_algorithm_var.set(schedule_report["algorithm"])
        else:
            self.summary_algorithm_var.set(self.algo_var.get().replace("PRIORITY", "Priority"))

        if deadlock_report is None:
            self.summary_deadlock_var.set("Awaiting run")
            return

        if deadlock_report["before_analysis"]["has_deadlock"]:
            self.summary_deadlock_var.set(
                f"Detected ({len(deadlock_report['before_analysis']['processes'])})"
            )
        else:
            self.summary_deadlock_var.set("Not detected")

    def _populate_process_form(self, _event=None):
        selected = self.process_tree.selection()
        if not selected:
            return

        process_id = selected[0]
        process = next((item for item in self.processes if item["id"] == process_id), None)
        if not process:
            return

        self.pid_var.set(process["id"])
        self.arrival_var.set(str(process["arrival"]))
        self.burst_var.set(str(process["burst"]))
        self.priority_var.set(str(process["priority"]))

    def _clear_process_form(self):
        self.pid_var.set("")
        self.arrival_var.set("")
        self.burst_var.set("")
        self.priority_var.set("")

    def _clear_resource_form(self):
        self.resource_pair_var.set("")

    def _refresh_process_table(self):
        for item_id in self.process_tree.get_children():
            self.process_tree.delete(item_id)

        for process in self.processes:
            self.process_tree.insert(
                "",
                "end",
                iid=process["id"],
                values=(process["id"], process["arrival"], process["burst"], process["priority"]),
            )
        self._update_summary_cards()

    def _refresh_resource_table(self):
        for item_id in self.resource_tree.get_children():
            self.resource_tree.delete(item_id)

        for index, (process_id, resource_id) in enumerate(self.resource_requests, start=1):
            self.resource_tree.insert(
                "",
                "end",
                iid=f"request-{index}",
                values=(index, process_id, resource_id),
            )
        self._update_summary_cards()

    def _parse_non_negative_int(self, label, value):
        try:
            number = int(value)
        except ValueError as error:
            raise ValueError(f"{label} must be an integer.") from error

        if number < 0:
            raise ValueError(f"{label} cannot be negative.")
        return number

    def _parse_positive_int(self, label, value):
        number = self._parse_non_negative_int(label, value)
        if number <= 0:
            raise ValueError(f"{label} must be greater than 0.")
        return number

    def _add_process(self):
        try:
            process_id = self.pid_var.get().strip()
            if not process_id:
                raise ValueError("Process ID is required.")

            if any(process["id"] == process_id for process in self.processes):
                raise ValueError("Process ID already exists. Use Update Selected to modify it.")

            arrival = self._parse_non_negative_int("Arrival", self.arrival_var.get().strip())
            burst = self._parse_positive_int("Burst", self.burst_var.get().strip())
            priority = self._parse_non_negative_int("Priority", self.priority_var.get().strip())
        except ValueError as error:
            messagebox.showerror("Invalid process", str(error))
            return

        self.processes.append({"id": process_id, "arrival": arrival, "burst": burst, "priority": priority})
        self.processes.sort(key=lambda process: (process["arrival"], process["id"]))
        self._refresh_process_table()
        self._clear_process_form()
        self.status_var.set(f"Added process {process_id}.")

    def _update_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showerror("No selection", "Select a process row to update.")
            return

        old_process_id = selected[0]

        try:
            new_process_id = self.pid_var.get().strip()
            if not new_process_id:
                raise ValueError("Process ID is required.")

            if new_process_id != old_process_id and any(
                process["id"] == new_process_id for process in self.processes
            ):
                raise ValueError("Another process already uses that ID.")

            arrival = self._parse_non_negative_int("Arrival", self.arrival_var.get().strip())
            burst = self._parse_positive_int("Burst", self.burst_var.get().strip())
            priority = self._parse_non_negative_int("Priority", self.priority_var.get().strip())
        except ValueError as error:
            messagebox.showerror("Invalid process", str(error))
            return

        for process in self.processes:
            if process["id"] == old_process_id:
                process.update({"id": new_process_id, "arrival": arrival, "burst": burst, "priority": priority})
                break

        if new_process_id != old_process_id:
            self.resource_requests = [
                (new_process_id if process_id == old_process_id else process_id, resource_id)
                for process_id, resource_id in self.resource_requests
            ]
            self._refresh_resource_table()

        self.processes.sort(key=lambda process: (process["arrival"], process["id"]))
        self._refresh_process_table()
        self._clear_process_form()
        self.status_var.set(f"Updated process {old_process_id}.")

    def _remove_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showerror("No selection", "Select a process row to remove.")
            return

        process_id = selected[0]
        self.processes = [process for process in self.processes if process["id"] != process_id]
        removed_requests = sum(1 for request_process_id, _ in self.resource_requests if request_process_id == process_id)
        self.resource_requests = [
            request for request in self.resource_requests if request[0] != process_id
        ]
        self._refresh_process_table()
        self._refresh_resource_table()
        self._clear_process_form()
        self.status_var.set(
            f"Removed process {process_id} and {removed_requests} linked resource request(s)."
        )

    def _add_resource_request_values(self, process_id, resource_id):
        if not process_id or not resource_id:
            messagebox.showerror("Invalid request", "Both Process ID and Resource ID are required.")
            return False

        if not any(process["id"] == process_id for process in self.processes):
            messagebox.showerror("Unknown process", "Add the process first, then create a resource request.")
            return False

        self.resource_requests.append((process_id, resource_id))
        self._refresh_resource_table()
        self._clear_resource_form()
        self.status_var.set(f"Added resource request {process_id} -> {resource_id}.")
        return True

    def _add_resource_request_pair(self):
        raw_request = self.resource_pair_var.get().strip()
        if raw_request.count(",") != 1:
            messagebox.showerror("Invalid format", "Resource request format must be P1,R1.")
            return

        process_id, resource_id = [part.strip() for part in raw_request.split(",")]
        self._add_resource_request_values(process_id, resource_id)

    def _remove_selected_request(self):
        selected = self.resource_tree.selection()
        if not selected:
            messagebox.showerror("No selection", "Select a resource request row to remove.")
            return

        index = int(selected[0].split("-")[-1]) - 1
        removed = self.resource_requests.pop(index)
        self._refresh_resource_table()
        self.status_var.set(f"Removed resource request {removed[0]} -> {removed[1]}.")

    def _load_sample_data(self):
        self.processes = [
            {"id": "P1", "arrival": 0, "burst": 5, "priority": 2},
            {"id": "P2", "arrival": 1, "burst": 3, "priority": 1},
            {"id": "P3", "arrival": 2, "burst": 4, "priority": 3},
            {"id": "P4", "arrival": 4, "burst": 2, "priority": 2},
        ]
        self.resource_requests = [
            ("P1", "R1"),
            ("P2", "R2"),
            ("P1", "R2"),
            ("P2", "R1"),
            ("P3", "R3"),
        ]
        self.algo_var.set("PRIORITY")
        self.quantum_var.set("2")
        self._update_algorithm_state()
        self._refresh_process_table()
        self._refresh_resource_table()
        self.status_var.set("Loaded a sample scenario with priority values and a deadlock cycle.")

    def _get_quantum(self):
        if self.algo_var.get() != "RR":
            return None
        return self._parse_positive_int("Time Quantum", self.quantum_var.get().strip())

    def _run_selected_algorithm(self, processes, quantum):
        algorithm = self.algo_var.get()
        if algorithm == "FCFS":
            schedule = fcfs_scheduling(processes)
            label = "FCFS"
        elif algorithm == "SJF":
            schedule = sjf_scheduling(processes)
            label = "SJF"
        elif algorithm == "PRIORITY":
            schedule = priority_scheduling(processes)
            label = "Priority Scheduling"
        else:
            schedule = round_robin_scheduling(processes, quantum)
            label = f"Round Robin (q={quantum})"
        return schedule, label

    def _run_algorithm_shortcut(self, algorithm):
        self.algo_var.set(algorithm)
        self._update_algorithm_state()
        self._run_simulation()

    def _run_deadlock_analysis(self):
        resource_pool = {resource_id: 1 for _, resource_id in self.resource_requests}
        before_manager = ResourceManager(resource_pool)
        request_events = []

        for process_id, resource_id in self.resource_requests:
            action = before_manager.request_resource(process_id, resource_id)
            request_events.append(
                {
                    "process": process_id,
                    "resource": resource_id,
                    "action": action,
                }
            )

        before_analysis = analyze_deadlock(before_manager)
        before_utilization = before_manager.utilization()

        after_manager = before_manager.copy()
        recovery_result = None
        if before_analysis["has_deadlock"]:
            recovery_result = recover_deadlock(after_manager)

        after_analysis = analyze_deadlock(after_manager)
        after_utilization = after_manager.utilization()

        return {
            "before_manager": before_manager,
            "after_manager": after_manager,
            "before_analysis": before_analysis,
            "after_analysis": after_analysis,
            "before_utilization": before_utilization,
            "after_utilization": after_utilization,
            "request_events": request_events,
            "recovery_result": recovery_result,
        }

    def _build_report_text(self, schedule_report, comparison_reports, deadlock_report):
        process_rows = [
            (process["id"], process["arrival"], process["burst"], process["priority"])
            for process in clone_processes(self.processes)
        ]
        execution_rows = []
        execution_flow_lines = []
        for index, task in enumerate(schedule_report["schedule"], start=1):
            label = "CPU Idle" if task["process"] == "IDLE" else task["process"]
            execution_rows.append((index, label, task["start"], task["end"], task["end"] - task["start"]))
            if task["process"] == "IDLE":
                execution_flow_lines.append(f"CPU is idle from {task['start']} to {task['end']}.")
            else:
                execution_flow_lines.append(
                    f"{task['process']} is allocated CPU at {task['start']} and runs until {task['end']}."
                )

        metric_rows = [
            (
                metric["id"],
                metric["arrival"],
                metric["burst"],
                metric["priority"],
                metric["first_start"],
                metric["completion"],
                metric["turnaround"],
                metric["waiting"],
                metric["response"],
                format_float(metric["normalized_turnaround"]),
                metric["slices"],
            )
            for metric in schedule_report["process_metrics"]
        ]

        summary = schedule_report["summary"]
        summary_rows = [
            ("Processes", summary["process_count"]),
            ("Busy Time", summary["busy_time"]),
            ("Idle Time", summary["idle_time"]),
            ("Total Time", summary["total_time"]),
            ("CPU Utilization (%)", format_float(summary["cpu_utilization"])),
            ("Throughput", format_float(summary["throughput"])),
            ("Avg Turnaround", format_float(summary["avg_turnaround"])),
            ("Avg Waiting", format_float(summary["avg_waiting"])),
            ("Avg Response", format_float(summary["avg_response"])),
            ("Avg Normalized Turnaround", format_float(summary["avg_normalized_turnaround"])),
            ("Context Switches", summary["context_switches"]),
        ]

        comparison_rows = [
            (
                algorithm_name,
                format_float(report["summary"]["avg_turnaround"]),
                format_float(report["summary"]["avg_waiting"]),
                format_float(report["summary"]["avg_response"]),
                format_float(report["summary"]["cpu_utilization"]),
                report["summary"]["context_switches"],
            )
            for algorithm_name, report in comparison_reports.items()
        ]

        request_rows = [
            (index, event["process"], event["resource"], event["action"])
            for index, event in enumerate(deadlock_report["request_events"], start=1)
        ]

        deadlock_lines = []
        before_analysis = deadlock_report["before_analysis"]
        after_analysis = deadlock_report["after_analysis"]
        recovery_result = deadlock_report["recovery_result"]
        before_manager = deadlock_report["before_manager"]
        after_manager = deadlock_report["after_manager"]

        if not deadlock_report["request_events"]:
            deadlock_lines.append("No resource requests were provided, so deadlock analysis is informational only.")
        else:
            deadlock_lines.append(
                "Deadlock detected before recovery: "
                + ("Yes" if before_analysis["has_deadlock"] else "No")
            )
            if before_analysis["has_deadlock"]:
                deadlock_lines.append("Cycle: " + " -> ".join(before_analysis["cycle"]))
                deadlock_lines.append("Processes involved: " + ", ".join(before_analysis["processes"]))
                deadlock_lines.append(f"Number of processes in deadlock: {len(before_analysis['processes'])}")
            else:
                deadlock_lines.append("No circular wait cycle was found.")

            if recovery_result:
                deadlock_lines.append(f"Recovery victim: {recovery_result['victim']}")
                deadlock_lines.append(
                    "Released resources: "
                    + (", ".join(recovery_result["released_resources"]) if recovery_result["released_resources"] else "None")
                )
                deadlock_lines.append(
                    "Dropped pending requests: "
                    + (", ".join(recovery_result["dropped_requests"]) if recovery_result["dropped_requests"] else "None")
                )
                reallocated = [f"{process_id}->{resource_id}" for process_id, resource_id in recovery_result["reallocated"]]
                deadlock_lines.append("Reallocated after recovery: " + (", ".join(reallocated) if reallocated else "None"))
                deadlock_lines.append(
                    "Deadlock detected after recovery: " + ("Yes" if after_analysis["has_deadlock"] else "No")
                )

        report_sections = [
            "OS PROCESS SIMULATION REPORT",
            "=" * 80,
            f"Selected Algorithm: {schedule_report['algorithm']}",
            "",
            "INPUT PROCESSES",
            format_table(("Process", "Arrival", "Burst", "Priority"), process_rows),
            "",
            "EXECUTION FLOW",
            "\n".join(execution_flow_lines),
            "",
            "EXECUTION TIMELINE",
            format_table(("Step", "Process", "Start", "End", "Duration"), execution_rows),
            "",
            "PER-PROCESS METRICS",
            format_table(
                (
                    "Process",
                    "Arrival",
                    "Burst",
                    "Priority",
                    "First Start",
                    "Completion",
                    "Turnaround",
                    "Waiting",
                    "Response",
                    "Norm TAT",
                    "Slices",
                ),
                metric_rows,
            ),
            "",
            "SCHEDULE SUMMARY",
            format_table(("Metric", "Value"), summary_rows),
            "",
            "ALGORITHM COMPARISON",
            format_table(
                (
                    "Algorithm",
                    "Avg Turnaround",
                    "Avg Waiting",
                    "Avg Response",
                    "CPU Util (%)",
                    "Context Switches",
                ),
                comparison_rows,
            ),
            "",
            "RESOURCE REQUEST LOG",
            format_table(("Order", "Process", "Resource", "Outcome"), request_rows),
            "",
            "RESOURCE STATE BEFORE RECOVERY",
            f"Resources: {format_resource_map(before_manager.resources)}",
            f"Available: {format_resource_map(before_manager.available)}",
            f"Allocation: {format_resource_map(before_manager.allocation)}",
            f"Waiting: {format_resource_map(before_manager.request)}",
            format_table(("Metric", "Value"), deadlock_report["before_utilization"].items()),
            "",
            "DEADLOCK ANALYSIS",
            "\n".join(deadlock_lines) if deadlock_lines else "No deadlock analysis details available.",
            "",
            "RESOURCE STATE AFTER RECOVERY",
            f"Resources: {format_resource_map(after_manager.resources)}",
            f"Available: {format_resource_map(after_manager.available)}",
            f"Allocation: {format_resource_map(after_manager.allocation)}",
            f"Waiting: {format_resource_map(after_manager.request)}",
            format_table(("Metric", "Value"), deadlock_report["after_utilization"].items()),
        ]

        return "\n".join(report_sections)

    def _display_report(self, text):
        self.last_report_text = text
        self.report_text.configure(state="normal")
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert("1.0", text)
        self.report_text.configure(state="disabled")

    def _display_welcome_message(self):
        welcome_text = (
            "OS PROCESS SIMULATOR\n"
            "====================\n\n"
            "Quick demo:\n"
            "1. Click Load Sample Scenario.\n"
            "2. Click Run Selected + Compare.\n"
            "3. Use Previous / Next to inspect Gantt, deadlock before, and deadlock after.\n\n"
            "Process fields: ID, Arrival, Burst, Priority (lower value = higher priority)\n"
            "Manual resource request format: P1,R1\n"
            "Graphs appear below this report. No graph popups are used."
        )
        self._display_report(welcome_text)
        self._update_summary_cards()

    def _clear_graphs(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        if self.graph_canvas is not None:
            self.graph_canvas = None

        for step in self.graph_steps:
            plt.close(step["figure"])

        self.graph_steps = []
        self.current_graph_index = 0
        self.graph_title_var.set("Run a simulation to generate charts.")
        self._update_graph_navigation()

    def _set_graphs(self, graph_steps):
        self._clear_graphs()
        self.graph_steps = graph_steps
        self.current_graph_index = 0
        self._show_current_graph()

    def _show_current_graph(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        if not self.graph_steps:
            self.graph_title_var.set("Run a simulation to generate charts.")
            self._update_graph_navigation()
            return

        current_graph = self.graph_steps[self.current_graph_index]
        self.graph_title_var.set(
            f"View {self.current_graph_index + 1} of {len(self.graph_steps)}: {current_graph['title']}"
        )

        self.graph_canvas = FigureCanvasTkAgg(current_graph["figure"], master=self.graph_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._update_graph_navigation()

    def _show_previous_graph(self):
        if self.current_graph_index > 0:
            self.current_graph_index -= 1
            self._show_current_graph()

    def _show_next_graph(self):
        if self.current_graph_index < len(self.graph_steps) - 1:
            self.current_graph_index += 1
            self._show_current_graph()

    def _update_graph_navigation(self):
        if not self.graph_steps:
            self.prev_button.state(["disabled"])
            self.next_button.state(["disabled"])
            return

        if self.current_graph_index <= 0:
            self.prev_button.state(["disabled"])
        else:
            self.prev_button.state(["!disabled"])

        if self.current_graph_index >= len(self.graph_steps) - 1:
            self.next_button.state(["disabled"])
        else:
            self.next_button.state(["!disabled"])

    def _run_simulation(self):
        if not self.processes:
            messagebox.showerror("No processes", "Add at least one process before running the simulation.")
            return

        try:
            quantum = self._get_quantum()
            processes = clone_processes(self.processes)
            schedule, algorithm_label = self._run_selected_algorithm(processes, quantum)
            schedule_report = build_schedule_report(processes, schedule, algorithm_label, quantum=quantum)
            comparison_reports = compare_algorithms(processes, quantum or 2)
            deadlock_report = self._run_deadlock_analysis()
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error))
            return
        except Exception as error:
            messagebox.showerror("Simulation failed", str(error))
            return

        report_text = self._build_report_text(schedule_report, comparison_reports, deadlock_report)
        self._display_report(report_text)
        self._update_summary_cards(schedule_report, deadlock_report)

        graph_steps = [
            {
                "title": f"{schedule_report['algorithm']} Gantt Chart",
                "figure": build_gantt_figure(schedule_report["schedule"], title=schedule_report["algorithm"]),
            },
            {
                "title": "Resource Allocation Graph (Before Recovery)",
                "figure": build_deadlock_figure(
                    deadlock_report["before_manager"],
                    title="Resource Allocation Graph (Before Recovery)",
                    highlighted_nodes=deadlock_report["before_analysis"]["cycle"],
                ),
            },
            {
                "title": "Resource Allocation Graph (After Recovery)",
                "figure": build_deadlock_figure(
                    deadlock_report["after_manager"],
                    title="Resource Allocation Graph (After Recovery)",
                    highlighted_nodes=deadlock_report["after_analysis"]["cycle"],
                ),
            },
        ]

        self._set_graphs(graph_steps)
        self.status_var.set(
            f"Simulation complete for {schedule_report['algorithm']}. Detailed report and charts are ready."
        )

    def _export_report(self):
        if not self.last_report_text.strip():
            messagebox.showerror("No report", "Run a simulation before exporting the report.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export simulation report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="os_simulation_report.txt",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as report_file:
                report_file.write(self.last_report_text)
        except OSError as error:
            messagebox.showerror("Export failed", str(error))
            return

        self.status_var.set(f"Exported report to {file_path}.")

    def _reset_all(self):
        self.processes = []
        self.resource_requests = []
        self._refresh_process_table()
        self._refresh_resource_table()
        self._clear_process_form()
        self._clear_resource_form()
        self._display_welcome_message()
        self._clear_graphs()
        self.status_var.set("Cleared all inputs, reports, and visuals.")

    def _close_app(self):
        self._clear_graphs()
        self.root.destroy()


def launch_app():
    root = tk.Tk()
    OSSimulatorApp(root)
    root.mainloop()
