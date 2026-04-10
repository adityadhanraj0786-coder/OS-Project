import matplotlib.pyplot as plt


def build_algorithm_comparison_figure(comparison_reports):
    labels = list(comparison_reports.keys())
    average_turnaround = [comparison_reports[label]["summary"]["avg_turnaround"] for label in labels]
    average_waiting = [comparison_reports[label]["summary"]["avg_waiting"] for label in labels]
    average_response = [comparison_reports[label]["summary"]["avg_response"] for label in labels]

    x_positions = list(range(len(labels)))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar([x - width for x in x_positions], average_turnaround, width=width, label="Avg Turnaround", color="#2563eb")
    ax.bar(x_positions, average_waiting, width=width, label="Avg Waiting", color="#0f766e")
    ax.bar([x + width for x in x_positions], average_response, width=width, label="Avg Response", color="#b45309")

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Time")
    ax.set_title("Algorithm Comparison")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    return fig
