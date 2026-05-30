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
        user_prompt = (
            f"You are currently at the '{funnel_state}' step of the insurance application.\n"
            f"Your available actions are: {allowed_actions}.\n"
            f"Based on your personality, decide your next action and how you behave.\n"
            f"Your response MUST be a single JSON object with the following keys:\n"
            f" - 'action': (string) One of the allowed actions.\n"
            f" - 'dwell_time_seconds': (integer) How long you spend on the page.\n"
            f" - 'hovers_on_element': (string, optional) The name of an element you hover over.\n"
            f" - 'scroll_behavior': (string, optional) 'scrolls up and down', 'no scrolling'.\n"
            f" - 'reasoning': (string) A brief explanation for your choice."
        )
        
        return self._send_prompt(user_prompt)

    def react_to_coach(self, coach_message, allowed_actions):
        """
        Prompts the persona LLM to react to an intervention message from the coach.
        """
        user_prompt = (
            f"A customer service coach just appeared and said to you: '{coach_message}'\n"
            f"Your available actions are still: {allowed_actions}.\n"
            f"How does this change your behavior? Decide your next action.\n"
            f"Your response MUST be a single JSON object with the same keys as before ('action', 'dwell_time_seconds', 'reasoning', etc.)."
        )
        return self._send_prompt(user_prompt)

    def _send_prompt(self, user_prompt):
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_prompt}
        ]

        raw_response = self.llm_client.chat_completion(messages)
        
        try:
            parsed_response = json.loads(raw_response)
            self.history.append({"role": "user", "content": user_prompt})
            self.history.append({"role": "assistant", "content": raw_response})
            return parsed_response
        except (json.JSONDecodeError, TypeError):
            print(f"FATAL ERROR: Failed to decode LLM response into JSON: {raw_response}")
            # Return None to signal a critical failure to the simulation engine
            return None
