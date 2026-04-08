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


process_entries = []
resource_requests = []

def add_resource_request(entry):
    text = entry.get().strip()

    if "," not in text:
        messagebox.showerror("Error", "Format must be P1,R1")
        return

    p, r = text.split(",")

    resource_requests.append((p.strip(), r.strip()))

    entry.delete(0, tk.END)

    messagebox.showinfo("Added", f"Added request: {p} → {r}")


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

    y = 0
    for task in gantt:
        start = task["start"]
        duration = task["end"] - task["start"]
        process = task["process"]

        ax.barh(y, duration, left=start)

        # Center label inside bar
        ax.text(start + duration/2, y, process,
                ha='center', va='center', color='white', fontweight='bold')

    # Time markers
    times = [task["start"] for task in gantt] + [gantt[-1]["end"]]
    ax.set_xticks(times)

    ax.set_title("Gantt Chart (CPU Scheduling Timeline)")
    ax.set_xlabel("Time")
    ax.set_yticks([])

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
    resource_requests.clear()

def compare_algorithms(processes):
    results = {}

    # FCFS
    fcfs_result = fcfs_scheduling(processes)
    results["FCFS"] = calculate_avg_metrics(processes, fcfs_result)

    # SJF
    sjf_result = sjf_scheduling(processes)
    results["SJF"] = calculate_avg_metrics(processes, sjf_result)

    # Round Robin (use default quantum = 2)
    rr_result = round_robin_scheduling(processes, 2)
    results["Round Robin"] = calculate_avg_metrics(processes, rr_result)

    return results

def calculate_avg_metrics(processes, result):
    completion_times = {}

    for task in result:
        completion_times[task["process"]] = task["end"]

    total_tat = 0
    total_wt = 0

    for p in processes:
        pid = p["id"]
        arrival = p["arrival"]
        burst = p["burst"]

        ct = completion_times.get(pid, 0)
        tat = ct - arrival
        wt = tat - burst

        total_tat += tat
        total_wt += wt

    n = len(processes)

    return {
        "avg_turnaround": total_tat / n,
        "avg_waiting": total_wt / n
    }

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

    # ---------------- EXECUTION FLOW ----------------
    output_text.insert(tk.END, "\n=== Execution Flow ===\n")

    for task in result:
        process = task["process"]
        start = task["start"]
        end = task["end"]

        output_text.insert(
            tk.END,
            f"{process} is allocated CPU at {start} and finishes at {end}\n"
        )

        # ---------------- SCHEDULING METRICS ----------------
    output_text.insert(tk.END, "\n=== Scheduling Performance Analysis ===\n")

    completion_times = {}
    turnaround_times = {}
    waiting_times = {}

    # Step 1: get completion time of each process
    for task in result:
        completion_times[task["process"]] = task["end"]

    # Step 2: calculate metrics
    # Get first execution time of each process
    first_start = {}

    for task in result:
        if task["process"] not in first_start:
            first_start[task["process"]] = task["start"]
    for p in processes:
        process_id = p["id"]
        arrival_time = p["arrival"]
        burst_time = p["burst"]

        completion_time = completion_times.get(process_id, 0)
        turnaround_time = completion_time - arrival_time
        waiting_time = turnaround_time - burst_time
        turnaround_times[process_id] = turnaround_time
        waiting_times[process_id] = waiting_time

        response_time = first_start.get(process_id, 0) - arrival_time

        output_text.insert(
            tk.END,
            f"{process_id} → Completion Time = {completion_time}, "
            f"Turnaround Time = {turnaround_time}, "
            f"Waiting Time = {waiting_time}\n"
            f"Response Time = {response_time}\n"
        )

    # ---------------- THROUGHPUT ----------------
    total_time = result[-1]["end"] if result else 0

    throughput = len(processes) / total_time if total_time > 0 else 0

    output_text.insert(
        tk.END,
        f"\nThroughput = {throughput:.2f} processes per unit time\n"
    )

    # Step 3: calculate averages
    average_turnaround = sum(turnaround_times.values()) / len(turnaround_times)
    average_waiting = sum(waiting_times.values()) / len(waiting_times)

    output_text.insert(
        tk.END,
        f"\nAverage Turnaround Time = {average_turnaround:.2f}\n"
    )
    output_text.insert(
        tk.END,
        f"Average Waiting Time = {average_waiting:.2f}\n"
)
    # ---------------- ALGORITHM COMPARISON ----------------
    comparison = compare_algorithms(processes)

    output_text.insert(tk.END, "\n=== Algorithm Comparison ===\n")

    for algo, values in comparison.items():
        output_text.insert(
            tk.END,
            f"{algo} → Average Turnaround Time = {values['avg_turnaround']:.2f}, "
            f"Average Waiting Time = {values['avg_waiting']:.2f}\n"
        )

    # Gantt
    graph_steps.append(create_gantt_figure(result))


    # ---------------- DEADLOCK ----------------
    
    output_text.insert(tk.END, "\n=== Deadlock Analysis ===\n")
   
    rm = ResourceManager({})

    # ---------------- DYNAMIC RESOURCE CREATION ----------------
    all_resources = set()

    for p, r in resource_requests:
        all_resources.add(r)

    for r in all_resources:
        rm.available[r] = 1

    

    

    # Apply user-defined resource requests (if added later)
    for p, r in resource_requests:

    # ✅ VALIDATION (ADD HERE)
        if r not in rm.available:
            output_text.insert(tk.END, f"\n⚠️ Resource {r} not defined!\n")
            continue
        rm.request_resource(p, r)

    # ---------------- RESOURCE UTILIZATION ----------------
    total_resources = len(rm.available)
    used_resources = sum(len(v) for v in rm.allocation.values())
    free_resources = sum(rm.available.values())

    output_text.insert(
        tk.END,
        f"\nResource Utilization:\n"
        f"Total Resources = {total_resources}\n"
        f"Used Resources = {used_resources}\n"
        f"Free Resources = {free_resources}\n"
    )

    is_deadlock = detect_deadlock(rm)

    if is_deadlock:
        output_text.insert(tk.END, "\n🔴 DEADLOCK DETECTED\n")

        deadlocked_processes = list(rm.request.keys())
        output_text.insert(
            tk.END,
            f"\nNumber of processes involved in deadlock: {len(deadlocked_processes)}\n"
        )
        

        output_text.insert(
        tk.END,
        f"\nProcesses involved in deadlock: {', '.join(deadlocked_processes)}\n"
    )
    
        # BEFORE STATE
        output_text.insert(tk.END, "\n--- BEFORE RECOVERY ---\n")
        output_text.insert(tk.END, f"Allocation: {rm.allocation}\n")
        output_text.insert(tk.END, f"Request: {rm.request}\n")
        output_text.insert(tk.END, f"Available: {rm.available}\n")

        output_text.insert(tk.END, "\n📊 Graph BEFORE Recovery\n")
        output_text.insert(tk.END,
        "\n In this graph:\n"
        "• Processes and Resources are shown as nodes\n"
        "• Arrow P → R means process is requesting resource\n"
        "• Arrow R → P means resource is allocated to process\n"
        "• A cycle in the graph indicates DEADLOCK\n"
        )
        graph_steps.append(create_deadlock_figure(rm, "Deadlock Graph (Before Recovery)"))

        # RECOVERY
        output_text.insert(tk.END, "\n🔧 Applying Recovery...\n")
        # Select process to terminate (simple strategy: first one)
        max_resources = -1
        terminated_process = None

        for p in deadlocked_processes:
            count = len(rm.allocation.get(p, []))
            if count > max_resources:
                max_resources = count
                terminated_process = p

        output_text.insert(
            tk.END,
            f"\nTerminating process to resolve deadlock: {terminated_process}\n"
        )

# ---------------- CUSTOM RECOVERY ----------------
        released = rm.allocation.pop(terminated_process, [])

        for r in released:
            rm.available[r] += 1

        rm.request.pop(terminated_process, None)

        for p in rm.request:
            rm.request[p] = [r for r in rm.request[p] if r in rm.available]

        # AFTER STATE
        output_text.insert(tk.END, "\n--- AFTER RECOVERY ---\n")

      
        # ✅ Then print it
        output_text.insert(
            tk.END,
            f"Resources released: {', '.join(released) if released else 'None'}\n"
        )

        # continue normal output
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

# ---------------- RESOURCE INPUT UI ----------------
tk.Label(left_frame, text="Resource Requests (P,R)").pack()

resource_entry = tk.Entry(left_frame)
resource_entry.pack(pady=5)

tk.Label(left_frame, text="Example: P1,R1").pack()

tk.Button(
    left_frame,
    text="Add Resource Request",
    command=lambda: add_resource_request(resource_entry)
).pack(pady=5)

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