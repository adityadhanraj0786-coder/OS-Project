import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SIMULATOR_ROOT = PROJECT_ROOT / "os_simulator"
sys.path.insert(0, str(SIMULATOR_ROOT))

from deadlock.detection import analyze_deadlock
from deadlock.recovery import recover_deadlock
from resource_manager.manager import ResourceManager
from scheduler.fcfs import fcfs_scheduling
from scheduler.metrics import build_schedule_report, compare_algorithms
from scheduler.priority import priority_scheduling
from scheduler.round_robin import round_robin_scheduling
from scheduler.sjf import sjf_scheduling


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label):
    if not value:
        raise AssertionError(f"{label}: expected a truthy value")


def run_resource_sequence(resource_requests):
    resource_pool = {resource_id: 1 for _, resource_id in resource_requests}
    manager = ResourceManager(resource_pool)

    for process_id, resource_id in resource_requests:
        manager.request_resource(process_id, resource_id)

    return manager


def check_scheduling():
    processes = [
        {"id": "P1", "arrival": 0, "burst": 5, "priority": 2},
        {"id": "P2", "arrival": 2, "burst": 3, "priority": 1},
        {"id": "P3", "arrival": 4, "burst": 1, "priority": 3},
    ]

    fcfs = build_schedule_report(processes, fcfs_scheduling(processes), "FCFS")
    sjf = build_schedule_report(processes, sjf_scheduling(processes), "SJF")
    rr_schedule = round_robin_scheduling(processes, 2)
    rr = build_schedule_report(processes, rr_schedule, "Round Robin (q=2)", quantum=2)
    priority_schedule = priority_scheduling(processes)
    priority = build_schedule_report(processes, priority_schedule, "Priority Scheduling")
    comparison = compare_algorithms(processes, 2)

    assert_equal(fcfs["summary"]["process_count"], 3, "FCFS process count")
    assert_equal(sjf["summary"]["process_count"], 3, "SJF process count")
    assert_equal(rr["summary"]["process_count"], 3, "RR process count")
    assert_equal(priority["summary"]["process_count"], 3, "Priority process count")
    assert_equal(len(comparison), 4, "algorithm comparison count")
    assert_true(any(step["process"] == "P2" for step in rr_schedule), "RR includes P2")
    assert_true(any(step["process"] == "P2" for step in priority_schedule), "Priority includes P2")


def check_priority_scheduling():
    processes = [
        {"id": "P1", "arrival": 0, "burst": 3, "priority": 2},
        {"id": "P2", "arrival": 0, "burst": 2, "priority": 1},
        {"id": "P3", "arrival": 0, "burst": 4, "priority": 3},
    ]

    schedule = priority_scheduling(processes)
    ordered_processes = [step["process"] for step in schedule if step["process"] != "IDLE"]
    assert_equal(ordered_processes, ["P2", "P1", "P3"], "priority scheduling order")


def check_two_process_deadlock():
    manager = run_resource_sequence(
        [
            ("P1", "R1"),
            ("P2", "R2"),
            ("P1", "R2"),
            ("P2", "R1"),
        ]
    )

    before = analyze_deadlock(manager)
    assert_true(before["has_deadlock"], "two-process deadlock detection")
    assert_equal(before["processes"], ["P1", "P2"], "two-process deadlock participants")

    recovery = recover_deadlock(manager)
    after = analyze_deadlock(manager)
    assert_true(recovery["victim"], "two-process recovery victim")
    assert_equal(after["has_deadlock"], False, "two-process deadlock recovery")


def check_three_process_deadlock():
    manager = run_resource_sequence(
        [
            ("P1", "R1"),
            ("P2", "R2"),
            ("P3", "R3"),
            ("P1", "R2"),
            ("P2", "R3"),
            ("P3", "R1"),
        ]
    )

    before = analyze_deadlock(manager)
    assert_true(before["has_deadlock"], "three-process deadlock detection")
    assert_equal(before["processes"], ["P1", "P2", "P3"], "three-process deadlock participants")

    recovery = recover_deadlock(manager)
    after = analyze_deadlock(manager)
    assert_true(recovery["victim"], "three-process recovery victim")
    assert_equal(after["has_deadlock"], False, "three-process deadlock recovery")


def main():
    check_scheduling()
    check_priority_scheduling()
    check_two_process_deadlock()
    check_three_process_deadlock()
    print("PASS: scheduling, priority, metrics, comparison, deadlock detection, and recovery checks")


if __name__ == "__main__":
    main()
