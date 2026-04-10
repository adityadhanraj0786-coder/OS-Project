def fcfs_scheduling(processes):
    """Return an FCFS execution timeline with explicit idle periods."""
    ordered_processes = sorted(
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

    time = 0
    gantt = []

    for process in ordered_processes:
        if time < process["arrival"]:
            gantt.append(
                {
                    "process": "IDLE",
                    "start": time,
                    "end": process["arrival"],
                }
            )
            time = process["arrival"]

        start = time
        end = start + process["burst"]
        gantt.append({"process": process["id"], "start": start, "end": end})
        time = end

    return gantt
