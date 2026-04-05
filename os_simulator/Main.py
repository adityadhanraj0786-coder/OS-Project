# main.py

processes = [
    {"id": "P1", "arrival": 0, "burst": 5},
    {"id": "P2", "arrival": 1, "burst": 3},
    {"id": "P3", "arrival": 2, "burst": 4},
]
from scheduler.fcfs import fcfs_scheduling

processes = [
    {"id": "P1", "arrival": 0, "burst": 5},
    {"id": "P2", "arrival": 1, "burst": 3},
    {"id": "P3", "arrival": 2, "burst": 4},
]

result = fcfs_scheduling(processes)

for r in result:
    print(r)

    # graph1FCFS
    from visualization.gantt_chart import draw_gantt_chart

draw_gantt_chart(result)