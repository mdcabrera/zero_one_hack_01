import argparse
import random
from simulation.engine import SimulationEngine
from bots.persona_factory import PersonaFactory

def run_simulations(personas_path, num_simulations, model_name, use_llm_intervention, enable_coach):
    """
    Runs a specified number of simulations with randomly chosen personas.
    """
    mode_text = "DISABLED"
    if enable_coach:
        mode_text = "LLM" if use_llm_intervention else "Rule-Based"
    
    print(f"--- Running {num_simulations} simulation(s) [Coach Trigger Mode: {mode_text}] using model: {model_name} ---")
    
    engine = SimulationEngine(
        personas_path, 
        model_name=model_name, 
        use_llm_intervention=use_llm_intervention,
        enable_coach=enable_coach
    )
    factory = PersonaFactory(personas_path)
    available_segments = factory.get_available_segments()

    for i in range(num_simulations):
        print(f"\n--- Simulation Run {i+1}/{num_simulations} ---")
        random_segment = random.choice(available_segments)
        engine.run_simulation(random_segment)

def main():
    """
    Main entry point for the simulation.
    Handles command-line arguments to switch between generating training data
    and running other modes (which can be added later).
    """
    parser = argparse.ArgumentParser(
        description="Run persona-based simulations of an insurance funnel."
    )
    parser.add_argument(
        '--generate-training-data',
        action='store_true',
        help="Run in data generation mode (disables the coach)."
    )
    parser.add_argument(
        '--use-llm-intervention',
        action='store_true',
        help="Use the LLM Intervention Model to trigger the coach (default is simple rules)."
    )
    parser.add_argument(
        '--num-simulations',
        type=int,
        default=1,
        help="Number of simulations to run."
    )
    parser.add_argument(
        '--model',
        type=str,
        default="deepseek-ai/DeepSeek-V4-Pro",
        help="The name of the LLM model to use (default: deepseek-ai/DeepSeek-V4-Pro)."
    )
    args = parser.parse_args()

    personas_json_path = 'tracks/insurance-uniqa/personas.json'

    # When generating training data, the coach is always disabled.
    coach_is_enabled = not args.generate_training_data

    run_simulations(
        personas_path=personas_json_path, 
        num_simulations=args.num_simulations, 
        model_name=args.model, 
        use_llm_intervention=True,#args.use_llm_intervention,
        enable_coach=True#coach_is_enabled
    )

if __name__ == "__main__":
    main()
