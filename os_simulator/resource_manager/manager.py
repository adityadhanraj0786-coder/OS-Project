class ResourceManager:
    def __init__(self, resources):
        # resources = {"R1": 1, "R2": 1}
        self.resources = resources
        self.available = resources.copy()
        self.allocation = {}  # {P1: [R1]}
        self.request = {}     # {P1: [R2]}
    
    def request_resource(self, process_id, resource):
        print(f"{process_id} requesting {resource}")
        
        if self.available.get(resource, 0) > 0:
            # Allocate resource
            self.available[resource] -= 1
            self.allocation.setdefault(process_id, []).append(resource)
            print(f"{resource} allocated to {process_id}")
        else:
            # Add to request list
            self.request.setdefault(process_id, []).append(resource)
            print(f"{process_id} waiting for {resource}")
    
    def release_resource(self, process_id, resource):
        print(f"{process_id} releasing {resource}")
        
        if process_id in self.allocation and resource in self.allocation[process_id]:
            self.allocation[process_id].remove(resource)
            self.available[resource] += 1
    
    def print_status(self):
        print("\n--- Resource Status ---")
        print("Available:", self.available)
        print("Allocation:", self.allocation)
        print("Request:", self.request)