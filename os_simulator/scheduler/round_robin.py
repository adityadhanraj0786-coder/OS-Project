from collections import deque


def round_robin_scheduling(processes, quantum):
    """Return a Round Robin execution timeline that respects process arrivals."""
    pending = sorted(
        (
            {
                "id": process["id"],
                "arrival": int(process["arrival"]),
                "burst": int(process["burst"]),
            }
            for process in processes
        ),
        key=lambda process: (process["arrival"], process["id"]),
    )

    remaining_time = {process["id"]: process["burst"] for process in pending}
    ready_queue = deque()
    gantt = []
    time = 0

    while pending or ready_queue:
        while pending and pending[0]["arrival"] <= time:
            ready_queue.append(pending.pop(0))

        if not ready_queue:
            next_arrival = pending[0]["arrival"]
            if time < next_arrival:
                gantt.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        current = ready_queue.popleft()
        start = time
        duration = min(quantum, remaining_time[current["id"]])
        time += duration
        end = time

        gantt.append({"process": current["id"], "start": start, "end": end})
        remaining_time[current["id"]] -= duration

        while pending and pending[0]["arrival"] <= time:
            ready_queue.append(pending.pop(0))

        if remaining_time[current["id"]] > 0:
            ready_queue.append(current)

    return gantt
