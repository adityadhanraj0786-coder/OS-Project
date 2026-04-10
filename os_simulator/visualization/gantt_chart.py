import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


PROCESS_COLORS = [
    "#0f766e",
    "#1d4ed8",
    "#c2410c",
    "#6d28d9",
    "#be123c",
    "#047857",
    "#0369a1",
]


def build_gantt_figure(gantt, title="CPU Scheduling Timeline"):
    fig, ax = plt.subplots(figsize=(11, 3.8), facecolor="#f8fafc")
    ax.set_facecolor("#ffffff")

    if not gantt:
        ax.text(0.5, 0.5, "No schedule to display", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    process_colors = {}

    for task in gantt:
        process_id = task["process"]
        start = task["start"]
        duration = task["end"] - task["start"]

        if process_id == "IDLE":
            color = "#cbd5e1"
            text_color = "#0f172a"
        else:
            color = process_colors.setdefault(
                process_id,
                PROCESS_COLORS[len(process_colors) % len(PROCESS_COLORS)],
            )
            text_color = "white"

        ax.barh(0, duration, left=start, height=0.56, color=color, edgecolor="#0f172a", linewidth=1.2)
        ax.text(
            start + duration / 2,
            0,
            process_id,
            ha="center",
            va="center",
            color=text_color,
            fontweight="bold",
            fontsize=9,
        )

    time_markers = sorted({task["start"] for task in gantt} | {gantt[-1]["end"]})
    ax.set_xticks(time_markers)
    ax.set_ylim(-0.75, 0.75)
    ax.set_yticks([])
    ax.set_xlabel("Time")
    ax.set_title(title, fontweight="bold", pad=12)
    ax.grid(axis="x", linestyle="--", color="#cbd5e1", alpha=0.9)
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.spines["bottom"].set_color("#64748b")

    legend_handles = [
        mpatches.Patch(color=color, label=process_id)
        for process_id, color in process_colors.items()
    ]
    if any(task["process"] == "IDLE" for task in gantt):
        legend_handles.append(mpatches.Patch(color="#cbd5e1", label="CPU Idle"))

    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.2),
            ncol=min(5, len(legend_handles)),
            frameon=False,
            fontsize=8,
        )

    fig.tight_layout()
    return fig
