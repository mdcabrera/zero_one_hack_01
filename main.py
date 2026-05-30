import argparse
import random
from simulation.engine import SimulationEngine
from bots.persona_factory import PersonaFactory

def generate_training_data(personas_path, num_simulations, model_name):
    """
    Runs a specified number of simulations with randomly chosen personas
    to generate training data.
    """
    print(f"--- Generating {num_simulations} simulation(s) for training data using model: {model_name} ---")
    engine = SimulationEngine(personas_path, model_name=model_name)
    factory = PersonaFactory(personas_path)
    available_segments = factory.get_available_segments()

    for i in range(num_simulations):
        print(f"\n--- Simulation Run {i+1}/{num_simulations} ---")
        # Choose a random persona segment for each run
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
        help="Run in data generation mode."
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

    if args.generate_training_data:
        generate_training_data(personas_json_path, args.num_simulations, args.model)
    else:
        # This is where you could plug in your intervention model in the future
        print("--- Running in Standard Mode (no data generation) ---")
        # For now, just run a single simulation as an example
        engine = SimulationEngine(personas_json_path, model_name=args.model)
        engine.run_simulation('segment_2') # Run with Franz by default

if __name__ == "__main__":
    main()
