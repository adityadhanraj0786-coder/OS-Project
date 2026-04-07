def recover_deadlock(resource_manager):
    print("\n🔧 Attempting Deadlock Recovery...")

    # Pick a process to terminate (simple strategy: first one)
    if resource_manager.allocation:
        victim = list(resource_manager.allocation.keys())[0]

        print(f"❌ Terminating process: {victim}")

        # Release all resources of that process
        for resource in resource_manager.allocation[victim]:
            resource_manager.available[resource] += 1

        # Remove process from allocation and request
        resource_manager.allocation.pop(victim, None)
        resource_manager.request.pop(victim, None)

        print(f"✅ Resources released from {victim}")
    else:
        print("No process to terminate.")