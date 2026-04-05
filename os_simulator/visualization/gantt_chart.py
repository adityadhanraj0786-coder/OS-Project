import matplotlib.pyplot as plt

def draw_gantt_chart(gantt):
    fig, ax = plt.subplots()
    
    for i, task in enumerate(gantt):
        ax.barh(0, task["end"] - task["start"], left=task["start"])
        ax.text(task["start"], 0, task["process"])
    
    ax.set_xlabel("Time")
    ax.set_title("Gantt Chart")
    
    plt.show()