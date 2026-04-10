def build_resource_allocation_graph(resource_manager):
    graph = {}

    for process_id, resources in resource_manager.allocation.items():
        graph.setdefault(process_id, [])
        for resource in resources:
            graph.setdefault(resource, []).append(process_id)

    for process_id, resources in resource_manager.request.items():
        graph.setdefault(process_id, [])
        for resource in resources:
            graph.setdefault(process_id, []).append(resource)
            graph.setdefault(resource, [])

    return graph


def _find_cycle(graph):
    visited = set()
    recursion_stack = []
    stack_lookup = set()

    def depth_first_search(node):
        visited.add(node)
        recursion_stack.append(node)
        stack_lookup.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = depth_first_search(neighbor)
                if cycle:
                    return cycle
            elif neighbor in stack_lookup:
                cycle_start = recursion_stack.index(neighbor)
                return recursion_stack[cycle_start:] + [neighbor]

        recursion_stack.pop()
        stack_lookup.remove(node)
        return None

    for node in graph:
        if node not in visited:
            cycle = depth_first_search(node)
            if cycle:
                return cycle

    return []


def analyze_deadlock(resource_manager):
    graph = build_resource_allocation_graph(resource_manager)
    cycle = _find_cycle(graph)
    process_nodes = set(resource_manager.allocation.keys()) | set(resource_manager.request.keys())
    involved_processes = sorted({node for node in cycle if node in process_nodes})

    return {
        "has_deadlock": bool(cycle),
        "graph": graph,
        "cycle": cycle,
        "processes": involved_processes,
    }


def detect_deadlock(resource_manager):
    return analyze_deadlock(resource_manager)["has_deadlock"]
