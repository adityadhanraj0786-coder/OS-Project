def detect_deadlock(resource_manager):
    graph = {}

    # Build graph from allocation
    for process, resources in resource_manager.allocation.items():
        for r in resources:
            graph.setdefault(r, []).append(process)

    # Build graph from requests
    for process, resources in resource_manager.request.items():
        for r in resources:
            graph.setdefault(process, []).append(r)

    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True

    return False