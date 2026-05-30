from enum import Enum, auto

class FunnelState(Enum):
    """Represents the states in the insurance application funnel."""
    START = auto()
    INPUTS_COVERAGE_TYPE = auto()
    INPUTS_INSURED_PERSON = auto()
    INPUTS_PERSONAL_DATA = auto()
    PRODUCT_TARIFF_SELECTION = auto()
    INPUTS_HEALTH_QUESTIONS = auto()
    RECOMMENDATION_FINAL_PRICE = auto()
    CLOSING_PERSONAL_DATA = auto()
    CONVERSION = auto()
    ABANDONMENT = auto()
    OUT_OF_SCOPE = auto()
    LLM_RESPONSE_ERROR = auto() # New terminal state for JSON errors

class Funnel:
    """
    Manages the state machine of the user journey, including allowed actions at each step.
    """
    def __init__(self):
        self.current_state = FunnelState.START
        self.history = [self.current_state]
        self._define_transitions()

    def _define_transitions(self):
        """Defines the state transitions and allowed actions."""
        self.transitions = {
            FunnelState.START: {"PROCEED": FunnelState.INPUTS_COVERAGE_TYPE},
            FunnelState.INPUTS_COVERAGE_TYPE: {
                "SELECT_DOCTOR_VISITS": FunnelState.INPUTS_INSURED_PERSON,
                "SELECT_HOSPITAL": FunnelState.OUT_OF_SCOPE,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.INPUTS_COVERAGE_TYPE
            },
            FunnelState.INPUTS_INSURED_PERSON: {
                "SELECT_MYSELF": FunnelState.INPUTS_PERSONAL_DATA,
                "SELECT_OTHERS": FunnelState.OUT_OF_SCOPE,
                "GO_BACK": FunnelState.INPUTS_COVERAGE_TYPE,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.INPUTS_INSURED_PERSON
            },
            FunnelState.INPUTS_PERSONAL_DATA: {
                "PROCEED": FunnelState.PRODUCT_TARIFF_SELECTION,
                "GO_BACK": FunnelState.INPUTS_INSURED_PERSON,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.INPUTS_PERSONAL_DATA
            },
            FunnelState.PRODUCT_TARIFF_SELECTION: {
                "SELECT_START_TARIFF": FunnelState.INPUTS_HEALTH_QUESTIONS,
                "SELECT_OPTIMAL_TARIFF": FunnelState.INPUTS_HEALTH_QUESTIONS,
                "SELECT_PREMIUM_TARIFF": FunnelState.OUT_OF_SCOPE, # Requires advisor
                "GO_BACK": FunnelState.INPUTS_PERSONAL_DATA,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.PRODUCT_TARIFF_SELECTION
            },
            FunnelState.INPUTS_HEALTH_QUESTIONS: {
                "PROCEED": FunnelState.RECOMMENDATION_FINAL_PRICE,
                "GO_BACK": FunnelState.PRODUCT_TARIFF_SELECTION,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.INPUTS_HEALTH_QUESTIONS
            },
            FunnelState.RECOMMENDATION_FINAL_PRICE: {
                "ACCEPT_PRICE": FunnelState.CLOSING_PERSONAL_DATA,
                "GO_BACK": FunnelState.INPUTS_HEALTH_QUESTIONS,
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.RECOMMENDATION_FINAL_PRICE
            },
            FunnelState.CLOSING_PERSONAL_DATA: {
                "PROCEED": FunnelState.CONVERSION, # Simplified for now
                "CANCEL": FunnelState.ABANDONMENT,
                "PAUSE": FunnelState.CLOSING_PERSONAL_DATA
            }
        }

    def get_allowed_actions(self):
        """Returns the list of possible actions for the current state."""
        return list(self.transitions.get(self.current_state, {}).keys())

    def next_state(self, action):
        """Transitions to the next state based on the chosen action."""
        next_state = self.transitions.get(self.current_state, {}).get(action)
        if next_state:
            self.current_state = next_state
            self.history.append(self.current_state)
        else:
            # Handle invalid action - for now, we just stay in the same state
            print(f"WARNING: Invalid action '{action}' for state '{self.current_state.name}'. Staying in the same state.")

        return self.current_state
