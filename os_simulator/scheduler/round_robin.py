def round_robin_scheduling(processes, quantum):
    queue = processes.copy()
    time = 0
    gantt = []
    
    # Add remaining burst time
    for p in queue:
        p["remaining"] = p["burst"]
    
    while queue:
        current = queue.pop(0)
        
        if current["remaining"] > quantum:
            start = time
            time += quantum
            end = time
            
            current["remaining"] -= quantum
            
            gantt.append({
                "process": current["id"],
                "start": start,
                "end": end
            })
            
            queue.append(current)
        
        else:
            start = time
            time += current["remaining"]
            end = time
            
            gantt.append({
                "process": current["id"],
                "start": start,
                "end": end
            })
    
    return gantt