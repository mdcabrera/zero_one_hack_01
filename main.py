from simulation.engine import SimulationEngine

def main():
    """
    Main entry point for the simulation.
    """
    personas_json_path = 'tracks/insurance-uniqa/personas.json'
    
    # --- Run with the Coach ---
    engine_with_coach = SimulationEngine(personas_json_path, with_coach=True)
    # We'll use the 'Online Affine' persona (Franz) for this example
    result_with_coach = engine_with_coach.run_simulation('segment_2')
    print(f"Result with Coach: {result_with_coach.name}\n")

    # --- Run without the Coach ---
    engine_without_coach = SimulationEngine(personas_json_path, with_coach=False)
    result_without_coach = engine_without_coach.run_simulation('segment_2')
    print(f"Result without Coach: {result_without_coach.name}\n")

if __name__ == "__main__":
    main()
