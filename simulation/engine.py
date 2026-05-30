import json
import os
from datetime import datetime
from bots.persona_factory import PersonaFactory
from simulation.funnel import Funnel, FunnelState
from simulation.llm_bot import LLMBot

class SimulationEngine:
    """
    Orchestrates the simulation of a user journey using an LLM-driven bot.
    """
    def __init__(self, personas_path, model_name, output_dir="outputs"):
        self.persona_factory = PersonaFactory(personas_path)
        self.model_name = model_name
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_simulation(self, segment_id, max_turns=10):
        """
        Runs a single simulation loop for a given persona segment.
        """
        # 1. Generate the Persona and get the LLM Prompt
        persona = self.persona_factory.create_persona(segment_id)
        
        # 2. Initialize the LLM Bot and the Funnel State Machine
        llm_bot = LLMBot(persona.llm_prompt, model_name=self.model_name)
        funnel = Funnel()
        
        print(f"--- Starting LLM Simulation for {persona.name} ({segment_id}) ---")
        
        simulation_log = []
        turn = 0
        terminal_states = [FunnelState.CONVERSION, FunnelState.ABANDONMENT, FunnelState.OUT_OF_SCOPE]

        # 3. Main Simulation Loop
        while funnel.current_state not in terminal_states and turn < max_turns:
            turn += 1
            current_state_name = funnel.current_state.name
            allowed_actions = funnel.get_allowed_actions()
            
            print(f"\n[Turn {turn}] State: {current_state_name}")
            print(f"  Available actions: {allowed_actions}")

            # Get action and signals from the LLM Bot
            llm_response = llm_bot.get_next_action(current_state_name, allowed_actions)
            
            action = llm_response.get("action")
            dwell_time = llm_response.get("dwell_time_seconds", 0)
            reasoning = llm_response.get("reasoning", "No reasoning provided.")
            
            print(f"  Bot decided: {action} (Dwell: {dwell_time}s) -> Reason: {reasoning}")
            
            # Log the turn data
            turn_data = {
                "turn": turn,
                "state": current_state_name,
                "allowed_actions": allowed_actions,
                "llm_response": llm_response
            }
            simulation_log.append(turn_data)

            # Update the funnel state based on the bot's action
            if action in allowed_actions:
                funnel.next_state(action)
            else:
                 print(f"  WARNING: LLM returned invalid action '{action}'. Forcing CANCEL to end loop.")
                 funnel.next_state("CANCEL")

        # 4. Save the results
        final_state = funnel.current_state.name
        print(f"\n--- Simulation finished. Final state: {final_state} ---")
        
        self._save_log(persona.name, segment_id, final_state, simulation_log)
        
        return final_state

    def _save_log(self, persona_name, segment_id, final_state, simulation_log):
        """Saves the simulation run to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{persona_name.replace(' ', '_')}_{timestamp}_{final_state}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        output_data = {
            "metadata": {
                "timestamp": timestamp,
                "persona_name": persona_name,
                "segment_id": segment_id,
                "final_state": final_state,
                "total_turns": len(simulation_log),
                "model_name": self.model_name
            },
            "journey_log": simulation_log
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
             json.dump(output_data, f, indent=2, ensure_ascii=False)
             
        print(f"Simulation log saved to: {filepath}")
