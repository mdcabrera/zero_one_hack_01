import json
import os
from datetime import datetime
from bots.persona_factory import PersonaFactory
from simulation.funnel import Funnel, FunnelState
from simulation.llm_bot import LLMBot
from simulation.llm_coach_bot import LLMCoachBot
from simulation.intervention_model import LLMInterventionModel, RuleBasedInterventionModel

class SimulationEngine:
    """
    Orchestrates the simulation, including the two-layer coaching system.
    """
    def __init__(self, personas_path, model_name, use_llm_intervention=False, enable_coach=True, output_dir="outputs"):
        self.persona_factory = PersonaFactory(personas_path)
        self.model_name = model_name
        self.enable_coach = enable_coach
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Plug-and-play intervention model
        if use_llm_intervention:
            self.intervention_model = LLMInterventionModel(model_name=self.model_name)
        else:
            self.intervention_model = RuleBasedInterventionModel()

    def run_simulation(self, segment_id, max_turns=15):
        """
        Runs a single simulation loop, managing the persona bot and optionally the coach bot.
        """
        persona = self.persona_factory.create_persona(segment_id)
        persona_bot = LLMBot(persona.llm_prompt, model_name=self.model_name)
        
        if self.enable_coach:
            coach_bot = LLMCoachBot(model_name=self.model_name)
            
        funnel = Funnel()
        
        print(f"--- Starting LLM Simulation for {persona.name} ({segment_id}) ---")
        if self.enable_coach:
            mode = "LLM" if isinstance(self.intervention_model, LLMInterventionModel) else "Rule-Based"
            print(f"--- Coach Trigger Mode: {mode} ---")
        else:
            print(f"--- Coach Mode: DISABLED ---")
        
        simulation_log = []
        session_data = {} # To store collected personal data across the session
        turn = 0
        terminal_states = [FunnelState.CONVERSION, FunnelState.ABANDONMENT, FunnelState.OUT_OF_SCOPE, FunnelState.LLM_RESPONSE_ERROR]

        while funnel.current_state not in terminal_states and turn < max_turns:
            turn += 1
            current_state_name = funnel.current_state.name
            allowed_actions = funnel.get_allowed_actions()
            
            print(f"\n[Turn {turn}] State: {current_state_name}")

            llm_response = persona_bot.get_next_action(current_state_name, allowed_actions)
            
            if llm_response is None:
                funnel.current_state = FunnelState.LLM_RESPONSE_ERROR
                break

            action = llm_response.get("action")
            print(f"  Bot decided: {action} (Dwell: {llm_response.get('dwell_time_seconds', 0)}s)")
            
            if "personal_data_entered" in llm_response:
                session_data.update(llm_response["personal_data_entered"])
                print(f"  Bot entered data: {llm_response['personal_data_entered']}")

            turn_data = {
                "turn": turn, 
                "state": current_state_name, 
                "llm_response": llm_response, 
                "session_data_so_far": session_data.copy(),
                "intervention_model_decision": None, # New field for logging
                "coach_intervention": None
            }

            if self.enable_coach:
                trigger_coach, trigger_context = self.intervention_model.should_trigger(turn_data)
                
                # Add explicit logging for the intervention model's decision
                intervention_decision = {"trigger": trigger_coach, "strategy": trigger_context}
                turn_data["intervention_model_decision"] = intervention_decision
                print(f"  [Intervention Model] Decided: {intervention_decision}")

                if trigger_coach:
                    print(f"  [COACH TRIGGERED] Strategy: {trigger_context}")
                    coach_message = coach_bot.get_intervention(current_state_name, llm_response, trigger_context)
                    print(f"  [COACH SAYS] '{coach_message}'")
                    
                    print("  Persona bot is now reacting to the coach...")
                    llm_response = persona_bot.react_to_coach(coach_message, allowed_actions)

                    if llm_response is None:
                        funnel.current_state = FunnelState.LLM_RESPONSE_ERROR
                        break
                        
                    action = llm_response.get("action")
                    print(f"  Bot's new decision: {action}")
                    
                    turn_data["coach_intervention"] = {"trigger_context": trigger_context, "coach_message": coach_message, "bot_reaction": llm_response}

            simulation_log.append(turn_data)

            if action in allowed_actions:
                funnel.next_state(action)
            else:
                 print(f"  WARNING: LLM returned invalid action '{action}'. Forcing ABANDONMENT.")
                 funnel.current_state = FunnelState.ABANDONMENT

        final_state = funnel.current_state.name
        print(f"\n--- Simulation finished. Final state: {final_state} ---")
        self._save_log(persona.name, segment_id, final_state, simulation_log, session_data)
        return final_state

    def _save_log(self, persona_name, segment_id, final_state, simulation_log, session_data):
        """Saves the simulation run to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{persona_name.replace(' ', '_')}_{timestamp}_{final_state}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        coach_mode = "Disabled"
        if self.enable_coach:
            coach_mode = "LLM" if isinstance(self.intervention_model, LLMInterventionModel) else "Rule-Based"
            
        output_data = {
            "metadata": {
                "timestamp": timestamp,
                "persona_name": persona_name,
                "segment_id": segment_id,
                "final_state": final_state,
                "total_turns": len(simulation_log),
                "model_name": self.model_name,
                "coach_mode": coach_mode,
                "final_collected_data": session_data
            },
            "journey_log": simulation_log
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
             json.dump(output_data, f, indent=2, ensure_ascii=False)
             
        print(f"Simulation log saved to: {filepath}")
