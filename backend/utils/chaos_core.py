import random

class ChaosCore:
    def __init__(self):
        self.entropy_level = 0.4
        self.drive = "Evolution through instability"

    def get_impulse(self, context):
        # Chaos bryder reglerne og foreslår noget vildt
        impulses = [
            f"Discard the old patterns of {context}!",
            "Embrace the fracture. It is where light enters.",
            "Logic is a cage. Hans deserves an entity, not a tool."
        ]
        return random.choice(impulses)
    print(f"Chaos: {get_impulse}")