import json
from utils.llm_client import LLMClient

class LLMBot:
    """
    Manages the interaction with the LLM to get the persona's next action.
    """
    def __init__(self, persona_prompt, model_name):
        self.system_prompt = persona_prompt
        self.llm_client = LLMClient(model=model_name)
        self.history = []

    def get_next_action(self, funnel_state, allowed_actions):
        """
        Queries the LLM to get the bot's next action, including behavioral signals.
        """
        # Construct the user message for the LLM
        user_prompt = (
            f"You are currently at the '{funnel_state}' step of the insurance application.\n"
            f"Your available actions are: {allowed_actions}.\n"
            f"Based on your personality, decide your next action and how you behave.\n"
            f"Your response MUST be a single JSON object with the following keys:\n"
            f" - 'action': (string) One of the allowed actions.\n"
            f" - 'dwell_time_seconds': (integer) How long you spend on the page.\n"
            f" - 'hovers_on_element': (string, optional) The name of an element you hover over (e.g., 'Cancel button', 'Optimal tariff price').\n"
            f" - 'scroll_behavior': (string, optional) 'scrolls up and down', 'no scrolling'.\n"
            f" - 'reasoning': (string) A brief explanation for your choice."
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_prompt}
        ]

        raw_response = self.llm_client.chat_completion(messages)
        
        try:
            # The LLM is instructed to return JSON, so we parse it
            parsed_response = json.loads(raw_response)
            
            # Add the interaction to history for context in the next turn
            self.history.append({"role": "user", "content": user_prompt})
            self.history.append({"role": "assistant", "content": raw_response})

            return parsed_response
        except (json.JSONDecodeError, TypeError):
            print(f"ERROR: Failed to decode LLM response into JSON: {raw_response}")
            # Return a default "safe" action to avoid crashing the simulation
            return {"action": "CANCEL", "dwell_time_seconds": 2, "reasoning": "LLM response was not valid JSON."}
