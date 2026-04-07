from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import tkinter as tk
from scheduler.fcfs import fcfs_scheduling
from scheduler.sjf import sjf_scheduling
from scheduler.round_robin import round_robin_scheduling
from visualization.gantt_chart import draw_gantt_chart
from resource_manager.manager import ResourceManager
from deadlock.detection import detect_deadlock
from deadlock.recovery import recover_deadlock
from visualization.graph_visual import draw_graph

process_entries = []

def add_process_fields():
    frame = tk.Frame(left_frame)
    frame.pack()

    tk.Label(frame, text="Process ID").grid(row=0, column=0)
    tk.Label(frame, text="Arrival").grid(row=0, column=1)
    tk.Label(frame, text="Burst").grid(row=0, column=2)

    pid = tk.Entry(frame)
    arrival = tk.Entry(frame)
    burst = tk.Entry(frame)

    pid.grid(row=1, column=0)
    arrival.grid(row=1, column=1)
    burst.grid(row=1, column=2)

    process_entries.append((pid, arrival, burst))

def create_gantt_figure(gantt):
    fig, ax = plt.subplots()

    for task in gantt:
        ax.barh(0, task["end"] - task["start"], left=task["start"])
        ax.text(task["start"], 0, task["process"])

    ax.set_title("Gantt Chart (CPU Scheduling)")
    ax.set_xlabel("Time")

    return fig

def create_deadlock_figure(rm, title):
    import networkx as nx

    G = nx.DiGraph()

    for p, resources in rm.allocation.items():
        for r in resources:
            G.add_edge(r, p)

    for p, resources in rm.request.items():
        for r in resources:
            G.add_edge(p, r)

    pos = nx.spring_layout(G)

    fig, ax = plt.subplots()
    nx.draw(G, pos, with_labels=True, node_color="lightblue", ax=ax)

    ax.set_title(title)

    return fig

def show_current_graph():
    global current_step

    for widget in graph_frame.winfo_children():
        widget.destroy()

    fig = graph_steps[current_step]

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def next_graph():
    global current_step
    if current_step < len(graph_steps) - 1:
        current_step += 1
        show_current_graph()

def prev_graph():
    global current_step
    if current_step > 0:
        current_step -= 1
        show_current_graph()



def reset_all():
    # clear output
    output_text.delete("1.0", tk.END)
    # clear graph
    for widget in graph_frame.winfo_children():
        widget.destroy()
    # clear input fields
    for pid, arr, burst in process_entries:
        pid.delete(0, tk.END)
        arr.delete(0, tk.END)
        burst.delete(0, tk.END)

def run_simulation():
    global graph_steps, current_step
    processes = []
    graph_steps = []
    current_step = 0

    for pid, arrival, burst in process_entries:
        processes.append({
            "id": pid.get(),
            "arrival": int(arrival.get()),
            "burst": int(burst.get())
        })

    algo = algo_var.get()

    # ---------------- SCHEDULING ----------------
    if algo == "FCFS":
         result = fcfs_scheduling(processes)

    elif algo == "SJF":
        result = sjf_scheduling(processes)

    elif algo == "RR":
        try:
            q = quantum_entry.get().strip()

            if q == "":
                messagebox.showerror("Error", "Please enter Time Quantum!")
                return


            quantum = int(q)

            if quantum <= 0:
                messagebox.showerror("Error", "Quantum must be greater than 0!")
                return

        except:
            messagebox.showerror("Error", "Please enter a valid number!")
            return

        result = round_robin_scheduling(processes, quantum)

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "=== Scheduling Output ===\n\n")
    for r in result:
        output_text.insert(tk.END, f"{r}\n")

    

    # Step 1: Gantt
    graph_steps.append(create_gantt_figure(result))


    # ---------------- DEADLOCK ----------------
    output_text.insert(tk.END, "\n=== Deadlock Analysis ===\n")
    resources = {"R1": 1, "R2": 1}
    rm = ResourceManager(resources)

     # Create dynamic resources
    for i in range(len(processes)):
     rm.available[f"R{i+1}"] = 1

    # Step 1: allocate one resource to each process
    for i in range(len(processes)):
     p = processes[i]["id"]
     r = f"R{i+1}"
    rm.request_resource(p, r)

   # Step 2: create circular wait
    for i in range(len(processes)):
        p = processes[i]["id"]
        next_r = f"R{(i+1) % len(processes) + 1}"
        rm.request_resource(p, next_r)

    is_deadlock = detect_deadlock(rm)

    if is_deadlock:
        output_text.insert(tk.END, "\n🔴 DEADLOCK DETECTED\n")
    
        # BEFORE STATE
        output_text.insert(tk.END, "\n--- BEFORE RECOVERY ---\n")
        output_text.insert(tk.END, f"Allocation: {rm.allocation}\n")
        output_text.insert(tk.END, f"Request: {rm.request}\n")
        output_text.insert(tk.END, f"Available: {rm.available}\n")

        output_text.insert(tk.END, "\n📊 Graph BEFORE Recovery\n")
        output_text.insert(tk.END,
        "\n In this graph:\n"
        "• Processes (P1, P2) and Resources (R1, R2) are shown as nodes\n"
        "• Arrow P → R means process is requesting resource\n"
        "• Arrow R → P means resource is allocated to process\n"
        "• A cycle in the graph indicates DEADLOCK\n"
        )
        graph_steps.append(create_deadlock_figure(rm, "Deadlock Graph (Before Recovery)"))

        # RECOVERY
        output_text.insert(tk.END, "\n🔧 Applying Recovery...\n")
        recover_deadlock(rm)

        # AFTER STATE
        output_text.insert(tk.END, "\n--- AFTER RECOVERY ---\n")
        output_text.insert(tk.END, f"Allocation: {rm.allocation}\n")
        output_text.insert(tk.END, f"Request: {rm.request}\n")
        output_text.insert(tk.END, f"Available: {rm.available}\n")

        output_text.insert(tk.END, "\n📊 Graph AFTER Recovery\n")
        output_text.insert(tk.END,
        "\n After recovery:\n"
        "• One process/resource link is removed\n"
        "• Cycle is broken\n"
        "• No circular dependency exists\n"
        "• System is now DEADLOCK-FREE\n"
        )
        graph_steps.append(create_deadlock_figure(rm, "Deadlock Graph (After Recovery)"))


        if detect_deadlock(rm):
            output_text.insert(tk.END, "\n❌ Still Deadlock!\n")
        else:
            output_text.insert(tk.END, "\n✅ Deadlock Resolved!\n")

    else:
        output_text.insert(tk.END, "\n✅ No deadlock.\n")
    show_current_graph()

# Create window
root = tk.Tk()
root.title("OS Simulator")
root.state("zoomed")  # full screen

# Main layout
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame, bg="#f0f0f0", width=400)
left_frame.pack(side="left", fill="y")

right_frame = tk.Frame(main_frame)
right_frame.pack(side="right", fill="both", expand=True)

tk.Label(left_frame, text="OS PROCESS SIMULATOR", font=("Arial", 16, "bold")).pack(pady=10)

algo_var = tk.StringVar(value="FCFS")

tk.Label(left_frame, text="Select Algorithm").pack()
tk.OptionMenu(left_frame, algo_var, "FCFS", "SJF", "RR").pack(pady=5)

tk.Label(left_frame, text="Time Quantum (RR)").pack()
quantum_entry = tk.Entry(left_frame)
quantum_entry.pack(pady=5)

tk.Button(left_frame, text="Add Process", command=add_process_fields).pack(pady=10)
tk.Button(left_frame, text="Run Simulation", command=run_simulation, bg="#4CAF50", fg="white").pack(pady=10)
tk.Button(left_frame,
          text="Reset",
          command=reset_all,
          bg="red",
          fg="white").pack(pady=10)
tk.Button(left_frame, text="⬅ Previous", command=prev_graph).pack(pady=5)
tk.Button(left_frame, text="Next ➡", command=next_graph).pack(pady=5)

# Output box
output_text = tk.Text(right_frame, height=15, font=("Courier", 10))
output_text.pack(fill="x", padx=10, pady=10)

graph_frame = tk.Frame(right_frame)
graph_frame.pack(fill="both", expand=True)

root.mainloop()