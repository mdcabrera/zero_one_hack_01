import json
import os
from utils.llm_client import LLMClient

class LLMInterventionModel:
    """
    An LLM-based model that decides whether to trigger the coach.
    It reads persona markdown files for context and maintains a history of the session.
    """
    def __init__(self, model_name):
        self.llm_client = LLMClient(model=model_name)
        self.history = []
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self):
        prompt = (
            "You are an AI orchestrator observing a user navigating a health insurance funnel.\n"
            "Your job is to decide whether a human-like customer service coach should intervene.\n"
            "Below is the context of the three main customer segments you need to identify:\n\n"
        )
        
        # Load the persona markdown files to provide rich context
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'tracks', 'insurance-uniqa')
        files = [
            'persona_judith_segment_1.md',
            'persona_franz_segment_2.md',
            'persona_peter_segment_3.md'
        ]
        
        for file in files:
            filepath = os.path.join(base_dir, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    prompt += f"--- {file} ---\n{f.read()}\n\n"
            except FileNotFoundError:
                prompt += f"--- {file} ---\n(File not found. Rely on general segment knowledge: 1=Hybrids, 2=Online Affine, 3=Service Affine)\n\n"
                
        prompt += (
            "At each turn, you will receive the user's current state, action, dwell time, and potentially their collected personal data.\n"
            "Keep track of their behavior over time. Intervene if they show signs of drop-off, hesitation, or overwhelm.\n"
            "Your response MUST be a single JSON object with the following keys:\n"
            " - 'trigger': (boolean) true if the coach should intervene, false otherwise.\n"
            " - 'strategy': (string) If trigger is true, describe the guessed personality and the intervention strategy. If false, output 'None'."
        )
        return prompt

    def should_trigger(self, turn_data):
        """
        Analyzes the behavioral data from a turn using an LLM and decides if an intervention is needed.
        
        Args:
            turn_data (dict): A dictionary containing the state, behavioral signals, and potentially personal data.

        Returns:
            tuple(bool, str): A boolean indicating whether to trigger the coach, and the strategy string.
        """
        user_prompt = (
            f"Turn Data:\n{json.dumps(turn_data, indent=2)}\n\n"
            "Based on the history and this new turn data, should the coach intervene now? Respond with JSON."
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_prompt}
        ]

        raw_response = self.llm_client.chat_completion(messages)
        
        try:
            parsed_response = json.loads(raw_response)
            trigger = parsed_response.get("trigger", False)
            strategy = parsed_response.get("strategy", "No strategy provided.")
            
            # Save history for the next turn to maintain context over the journey
            self.history.append({"role": "user", "content": user_prompt})
            self.history.append({"role": "assistant", "content": raw_response})
            
            return trigger, strategy
        except (json.JSONDecodeError, TypeError):
            print(f"ERROR: Intervention LLM failed to return JSON: {raw_response}")
            return False, "Failed to parse."


class RuleBasedInterventionModel:
    """
    A simple rule-based model for plug-and-play testing without an LLM.
    """
    def should_trigger(self, turn_data):
        state = turn_data.get("state")
        llm_response = turn_data.get("llm_response", {})
        dwell_time = llm_response.get("dwell_time_seconds", 0)
        hovers = llm_response.get("hovers_on_element")
        
        if state == "PRODUCT_TARIFF_SELECTION" and dwell_time > 30:
            return (True, "High dwell time on price page, likely 'Online Affine' comparing options.")
            
        if state == "RECOMMENDATION_FINAL_PRICE" and hovers and "cancel" in str(hovers).lower():
            return (True, "Hesitation on final price, hovering cancel. Possible 'Service Affine' feeling overwhelmed.")

        return (False, "No trigger condition met.")
