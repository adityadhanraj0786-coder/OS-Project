from scheduler.fcfs import fcfs_scheduling
from scheduler.priority import priority_scheduling
from scheduler.round_robin import round_robin_scheduling
from scheduler.sjf import sjf_scheduling


def clone_processes(processes):
    return [
        {
            "id": str(process["id"]).strip(),
            "arrival": int(process["arrival"]),
            "burst": int(process["burst"]),
            "priority": int(process["priority"]),
        }
        for process in processes
    ]


def build_schedule_report(processes, schedule, algorithm_name, quantum=None):
    normalized_processes = clone_processes(processes)
    ordered_processes = sorted(normalized_processes, key=lambda process: (process["arrival"], process["id"]))

    first_start = {}
    completion_time = {}
    slice_count = {process["id"]: 0 for process in ordered_processes}
    busy_time = 0
    context_switches = 0
    last_process = None

    for task in schedule:
        process_id = task["process"]
        duration = task["end"] - task["start"]

        if process_id == "IDLE":
            continue

        busy_time += duration
        slice_count[process_id] = slice_count.get(process_id, 0) + 1
        completion_time[process_id] = task["end"]

        if process_id not in first_start:
            first_start[process_id] = task["start"]

        if last_process is not None and last_process != process_id:
            context_switches += 1

        last_process = process_id

    per_process_metrics = []
    for process in ordered_processes:
        process_id = process["id"]
        completion = completion_time.get(process_id, process["arrival"])
        turnaround = completion - process["arrival"]
        waiting = turnaround - process["burst"]
        response = first_start.get(process_id, process["arrival"]) - process["arrival"]
        normalized_turnaround = turnaround / process["burst"] if process["burst"] else 0

        per_process_metrics.append(
            {
                "id": process_id,
                "arrival": process["arrival"],
                "burst": process["burst"],
                "priority": process["priority"],
                "first_start": first_start.get(process_id, process["arrival"]),
                "completion": completion,
                "turnaround": turnaround,
                "waiting": waiting,
                "response": response,
                "normalized_turnaround": normalized_turnaround,
                "slices": slice_count.get(process_id, 0),
            }
        )

    total_time = schedule[-1]["end"] if schedule else 0
    idle_time = total_time - busy_time
    process_count = len(ordered_processes)

    avg_turnaround = sum(item["turnaround"] for item in per_process_metrics) / process_count if process_count else 0
    avg_waiting = sum(item["waiting"] for item in per_process_metrics) / process_count if process_count else 0
    avg_response = sum(item["response"] for item in per_process_metrics) / process_count if process_count else 0
    avg_normalized_turnaround = (
        sum(item["normalized_turnaround"] for item in per_process_metrics) / process_count if process_count else 0
    )

    summary = {
        "process_count": process_count,
        "busy_time": busy_time,
        "idle_time": idle_time,
        "total_time": total_time,
        "throughput": process_count / total_time if total_time else 0,
        "cpu_utilization": (busy_time / total_time * 100) if total_time else 0,
        "avg_turnaround": avg_turnaround,
        "avg_waiting": avg_waiting,
        "avg_response": avg_response,
        "avg_normalized_turnaround": avg_normalized_turnaround,
        "context_switches": context_switches,
    }

    return {
        "algorithm": algorithm_name,
        "quantum": quantum,
        "schedule": schedule,
        "process_metrics": per_process_metrics,
        "summary": summary,
    }


def compare_algorithms(processes, quantum):
    normalized_processes = clone_processes(processes)
    report_specs = [
        ("FCFS", fcfs_scheduling(normalized_processes), None),
        ("SJF", sjf_scheduling(normalized_processes), None),
        (f"Round Robin (q={quantum})", round_robin_scheduling(normalized_processes, quantum), quantum),
        ("Priority Scheduling", priority_scheduling(normalized_processes), None),
    ]

    comparison = {}
    for algorithm_name, schedule, algorithm_quantum in report_specs:
        comparison[algorithm_name] = build_schedule_report(
            normalized_processes,
            schedule,
            algorithm_name,
            quantum=algorithm_quantum,
        )

    return comparison
