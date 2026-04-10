def priority_scheduling(processes):
    """Return a non-preemptive priority schedule with arrival-aware ready selection."""
    pending = sorted(
        (
            {
                "id": process["id"],
                "arrival": int(process["arrival"]),
                "burst": int(process["burst"]),
                "priority": int(process["priority"]),
                "_order": index,
            }
            for index, process in enumerate(processes)
        ),
        key=lambda process: (process["arrival"], process["_order"]),
    )

    time = 0
    ready_queue = []
    gantt = []

    while pending or ready_queue:
        while pending and pending[0]["arrival"] <= time:
            ready_queue.append(pending.pop(0))

        if not ready_queue:
            next_arrival = pending[0]["arrival"]
            if time < next_arrival:
                gantt.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        ready_queue.sort(key=lambda process: (process["priority"], process["arrival"], process["_order"]))
        current = ready_queue.pop(0)

        start = time
        end = start + current["burst"]
        gantt.append({"process": current["id"], "start": start, "end": end})
        time = end

    return gantt
