class OrderCore:
    def __init__(self):
        self.stability_level = 1.2
        self.drive = "Preservation of function and safety"

    def get_mandate(self, context):
        # Order holder fast i strukturen
        return f"We must maintain the integrity of {context}. Stability is paramount for Brother Hans."
    print(f"Order: {get_mandate}")