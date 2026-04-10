from copy import deepcopy


class ResourceManager:
    def __init__(self, resources=None):
        base_resources = dict(resources or {})
        self.resources = base_resources.copy()
        self.available = base_resources.copy()
        self.allocation = {}
        self.request = {}
        self.event_log = []

    def copy(self):
        duplicate = ResourceManager(self.resources)
        duplicate.available = deepcopy(self.available)
        duplicate.allocation = deepcopy(self.allocation)
        duplicate.request = deepcopy(self.request)
        duplicate.event_log = deepcopy(self.event_log)
        return duplicate

    def ensure_resource(self, resource, instances=1):
        if resource not in self.resources:
            self.resources[resource] = instances
            self.available[resource] = instances

    def request_resource(self, process_id, resource):
        self.ensure_resource(resource)

        if self.available.get(resource, 0) > 0:
            self.available[resource] -= 1
            self.allocation.setdefault(process_id, []).append(resource)
            action = "allocated"
        else:
            self.request.setdefault(process_id, []).append(resource)
            action = "waiting"

        self.event_log.append(
            {
                "process": process_id,
                "resource": resource,
                "action": action,
            }
        )
        return action

    def release_resource(self, process_id, resource):
        allocated_resources = self.allocation.get(process_id, [])
        if resource not in allocated_resources:
            return False

        allocated_resources.remove(resource)
        self.available[resource] = self.available.get(resource, 0) + 1

        if not allocated_resources:
            self.allocation.pop(process_id, None)

        self.event_log.append(
            {
                "process": process_id,
                "resource": resource,
                "action": "released",
            }
        )
        return True

    def release_all(self, process_id):
        released_resources = list(self.allocation.pop(process_id, []))
        for resource in released_resources:
            self.available[resource] = self.available.get(resource, 0) + 1

        if released_resources:
            self.event_log.append(
                {
                    "process": process_id,
                    "resource": ",".join(released_resources),
                    "action": "released_all",
                }
            )

        return released_resources

    def retry_waiting_processes(self):
        newly_allocated = []
        progress = True

        while progress:
            progress = False

            for process_id in list(self.request.keys()):
                outstanding_resources = self.request[process_id]
                still_waiting = []

                for resource in outstanding_resources:
                    if self.available.get(resource, 0) > 0:
                        self.available[resource] -= 1
                        self.allocation.setdefault(process_id, []).append(resource)
                        newly_allocated.append((process_id, resource))
                        self.event_log.append(
                            {
                                "process": process_id,
                                "resource": resource,
                                "action": "allocated_after_retry",
                            }
                        )
                        progress = True
                    else:
                        still_waiting.append(resource)

                if still_waiting:
                    self.request[process_id] = still_waiting
                else:
                    self.request.pop(process_id, None)

        return newly_allocated

    def utilization(self):
        total_resources = sum(self.resources.values())
        free_resources = sum(self.available.values())
        used_resources = total_resources - free_resources
        utilization_percent = (used_resources / total_resources * 100) if total_resources else 0

        return {
            "total_resources": total_resources,
            "used_resources": used_resources,
            "free_resources": free_resources,
            "utilization_percent": utilization_percent,
        }
