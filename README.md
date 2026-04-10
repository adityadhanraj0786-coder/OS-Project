# OS Process Simulator

An interactive desktop simulator for core operating system concepts:

- CPU scheduling with `FCFS`, `SJF`, `Round Robin`, and non-preemptive `Priority Scheduling`
- Detailed per-process performance metrics
- Algorithm comparison reports
- Resource allocation and deadlock detection
- Automatic deadlock recovery analysis
- Exportable simulation reports

The project is designed to be more than a demo. It now acts like a guided learning tool with structured inputs, richer output, and clearer visuals.

## What Improved

- The interface is now organized around user tasks instead of scattered text boxes.
- Processes and resource requests are managed in tables, with add, update, and remove actions.
- Round Robin now respects arrival times instead of rotating through processes from time 0.
- Reports include execution flow, per-process metrics, utilization, throughput, response time, and algorithm comparison.
- Deadlock analysis now shows before/after state, cycle participants, recovery choice, and resource reallocation results.
- A sample scenario is included so users can explore the simulator immediately.
- Reports can be exported to a `.txt` file.

## Requirements

- Python 3.10+
- Tkinter (normally bundled with Python on Windows)
- Packages listed in `requirements.txt`

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run project checks:

```powershell
python check_project.py
```

## Run

Option 1:

```powershell
cd os_simulator
python Main.py
```

Option 2 on Windows:

Double-click `run_simulator.bat`.

## How To Use

1. Choose a scheduling algorithm.
2. If using Round Robin, enter a time quantum.
3. Add one or more processes with ID, arrival time, burst time, and priority.
Priority rule: lower value = higher priority.
4. Add resource requests in `P1,R1` format.
5. Click `Run Selected + Compare`, or use the quick buttons: `Run FCFS`, `Run SJF`, `Run RR`, `Run Priority`.
6. Review the generated report and switch through the visual charts.
7. Export the report if needed.

## Visual Navigation

The `Previous` and `Next` buttons move through the required visual explanation:

1. Gantt Chart
2. Deadlock Graph Before Recovery
3. Deadlock Graph After Recovery

## Sample Deadlock Scenario

The built-in sample loads a classic circular wait:

- `P1 -> R1`
- `P2 -> R2`
- `P1 -> R2`
- `P2 -> R1`

That creates a cycle where `P1` waits for `R2` while `P2` waits for `R1`.

## Project Structure

```text
OS-Project/
|-- README.md
|-- requirements.txt
|-- run_simulator.bat
`-- os_simulator/
    |-- Main.py
    |-- gui/
    |-- scheduler/
    |-- resource_manager/
    |-- deadlock/
    `-- visualization/
```

## Notes

- Resource IDs are treated as single-instance resources.
- Resource requests are processed in the order shown in the table.
- If no resource requests are added, deadlock analysis still runs but stays informational.
