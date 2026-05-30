import json
from utils.llm_client import LLMClient

class LLMCoachBot:
    """
    Manages the interaction with the LLM to generate intervention messages
    from the Conversion Coach.
    """
    def __init__(self, model_name):
        self.llm_client = LLMClient(model=model_name)
        self.history = []
        self.system_prompt = (
            "You are the UNIQA Conversion Coach. Your goal is to assist users navigating an online health insurance funnel.\n"
            "You intervene to provide reassurance, explain complex terms, or reframe prices psychologically.\n"
            "If you are provided with a guessed personality type or behavioral context, adapt your tone to match their needs. "
            "For example: 'Service Affine' users need strong guidance and handholding, while 'Online Affine' users prefer fast, transparent facts.\n"
            "Your response MUST be a single JSON object with the following key:\n"
            " - 'coach_message': (string) The exact message you say to the user to help them proceed."
        )

    def get_intervention(self, funnel_state, user_action_data, trigger_context):
        """
        Queries the LLM to generate a helpful coaching message based on user behavior.
        """
        user_prompt = (
            f"The user is currently at the '{funnel_state}' step.\n"
            f"The user just exhibited the following behavior: {json.dumps(user_action_data)}\n"
            f"Trigger Context / Guessed Personality: {trigger_context}\n\n"
            "Based on this behavior and context, generate a helpful intervention message."
        )
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_prompt}
        ]

        raw_response = self.llm_client.chat_completion(messages)
        
        try:
            parsed_response = json.loads(raw_response)
            message = parsed_response.get("coach_message", "How can I help you with your insurance selection?")
            
            # Save the conversation history for context in future turns
            self.history.append({"role": "user", "content": user_prompt})
            self.history.append({"role": "assistant", "content": raw_response})
            
            return message
        except (json.JSONDecodeError, TypeError):
            print(f"ERROR: Failed to decode Coach LLM response into JSON: {raw_response}")
            return "It seems you might need some help. You can easily reach our customer service if you have questions."
