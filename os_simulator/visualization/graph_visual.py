import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

def draw_graph(resource_manager):
    G = nx.DiGraph()

    # Add allocation edges (Resource → Process)
    for process, resources in resource_manager.allocation.items():
        for r in resources:
            G.add_edge(r, process)

    # Add request edges (Process → Resource)
    for process, resources in resource_manager.request.items():
        for r in resources:
            G.add_edge(process, r)

    pos = nx.spring_layout(G)

    nx.draw(G, pos, with_labels=True, node_color="lightblue",
            node_size=2000, font_size=10, font_weight="bold")

    plt.title("Resource Allocation Graph")
    plt.show()