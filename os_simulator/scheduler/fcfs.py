def fcfs_scheduling(processes):
    # Sort by arrival time
    processes = sorted(processes, key=lambda x: x["arrival"])
    
    time = 0
    gantt = []
    
    for p in processes:
        if time < p["arrival"]:
            time = p["arrival"]
        
        start = time
        time += p["burst"]
        end = time
        
        gantt.append({
            "process": p["id"],
            "start": start,
            "end": end
        })
    
    return gantt