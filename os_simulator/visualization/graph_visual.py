import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import networkx as nx


def build_deadlock_figure(resource_manager, title="Resource Allocation Graph", highlighted_nodes=None):
    highlighted = set(highlighted_nodes or [])
    fig, ax = plt.subplots(figsize=(10, 5.6), facecolor="#f8fafc")
    ax.set_facecolor("#ffffff")

    processes = sorted(set(resource_manager.allocation.keys()) | set(resource_manager.request.keys()))
    resources = sorted(resource_manager.resources.keys())

    if not processes and not resources:
        ax.text(0.5, 0.5, "No resource requests to display", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    graph = nx.DiGraph()
    graph.add_nodes_from(processes, kind="process")
    graph.add_nodes_from(resources, kind="resource")

    allocation_edges = []
    request_edges = []

    for process_id, allocated_resources in resource_manager.allocation.items():
        for resource in allocated_resources:
            graph.add_edge(resource, process_id)
            allocation_edges.append((resource, process_id))

    for process_id, requested_resources in resource_manager.request.items():
        for resource in requested_resources:
            graph.add_edge(process_id, resource)
            request_edges.append((process_id, resource))

    pos = {}
    process_spacing = max(len(processes) - 1, 1)
    resource_spacing = max(len(resources) - 1, 1)

    for index, process_id in enumerate(processes):
        pos[process_id] = (0, -index / process_spacing)
    for index, resource in enumerate(resources):
        pos[resource] = (1.6, -index / resource_spacing)

    process_colors = ["#ef4444" if process_id in highlighted else "#38bdf8" for process_id in processes]
    resource_colors = ["#f97316" if resource in highlighted else "#fde68a" for resource in resources]

    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=processes,
        node_color=process_colors,
        node_shape="o",
        node_size=1800,
        ax=ax,
        edgecolors="#1f2937",
        linewidths=1.4,
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=resources,
        node_color=resource_colors,
        node_shape="s",
        node_size=1800,
        ax=ax,
        edgecolors="#1f2937",
        linewidths=1.4,
    )
    nx.draw_networkx_labels(graph, pos, font_weight="bold", font_size=10, ax=ax)
    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=allocation_edges,
        edge_color="#16a34a",
        width=2.5,
        arrows=True,
        arrowsize=18,
        min_source_margin=22,
        min_target_margin=22,
        ax=ax,
    )
    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=request_edges,
        edge_color="#dc2626",
        width=2.5,
        style="dashed",
        arrows=True,
        arrowsize=18,
        min_source_margin=22,
        min_target_margin=22,
        ax=ax,
    )

    ax.text(-0.05, 0.1, "Processes", transform=ax.transAxes, fontsize=9, color="#475569", fontweight="bold")
    ax.text(0.78, 0.1, "Resources", transform=ax.transAxes, fontsize=9, color="#475569", fontweight="bold")

    allocation_line = mlines.Line2D([], [], color="#16a34a", linewidth=2.5, label="Allocated: Resource -> Process")
    request_line = mlines.Line2D([], [], color="#dc2626", linewidth=2.5, linestyle="--", label="Waiting: Process -> Resource")
    process_patch = mpatches.Patch(color="#38bdf8", label="Process")
    resource_patch = mpatches.Patch(color="#fde68a", label="Resource")
    cycle_patch = mpatches.Patch(color="#ef4444", label="Node in deadlock cycle")

    handles = [process_patch, resource_patch, allocation_line, request_line]
    if highlighted:
        handles.append(cycle_patch)

    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False, fontsize=8)
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_axis_off()
    fig.tight_layout()
    return fig
