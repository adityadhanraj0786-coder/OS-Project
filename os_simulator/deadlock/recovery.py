def recover_deadlock(resource_manager):
    candidates = sorted(set(resource_manager.allocation.keys()) | set(resource_manager.request.keys()))
    if not candidates:
        return {
            "victim": None,
            "released_resources": [],
            "dropped_requests": [],
            "reallocated": [],
        }

    victim = max(
        candidates,
        key=lambda process_id: (
            len(resource_manager.allocation.get(process_id, [])),
            len(resource_manager.request.get(process_id, [])),
            process_id,
        ),
    )

    released_resources = resource_manager.release_all(victim)
    dropped_requests = list(resource_manager.request.pop(victim, []))
    reallocated = resource_manager.retry_waiting_processes()

    resource_manager.event_log.append(
        {
            "process": victim,
            "resource": ",".join(released_resources) if released_resources else "None",
            "action": "terminated_for_recovery",
        }
    )

    return {
        "victim": victim,
        "released_resources": released_resources,
        "dropped_requests": dropped_requests,
        "reallocated": reallocated,
    }
