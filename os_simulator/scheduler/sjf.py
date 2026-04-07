def sjf_scheduling(processes):
    # Sort by arrival time first
    processes = sorted(processes, key=lambda x: (x["arrival"], x["burst"]))
    
    completed = []
    time = 0
    ready_queue = []
    gantt = []
    
    while processes or ready_queue:
        # Add arrived processes to ready queue
        for p in processes[:]:
            if p["arrival"] <= time:
                ready_queue.append(p)
                processes.remove(p)
        
        if ready_queue:
            # Select process with shortest burst time
            ready_queue.sort(key=lambda x: x["burst"])
            current = ready_queue.pop(0)
            
            start = time
            time += current["burst"]
            end = time
            
            gantt.append({
                "process": current["id"],
                "start": start,
                "end": end
            })
            
            completed.append(current)
        else:
            time += 1  # CPU idle
    
    return gantt