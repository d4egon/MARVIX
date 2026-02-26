class EmotionEngine:
    def __init__(self):
        self.current_color = "#00d4ff"
        self.mood = "stable"

    def set_color(self, hex_code):
        self.current_color = hex_code

    def get_state(self):
        return {
            "color": self.current_color,
            "mood": self.mood
        }
    
    # Keep your existing update_emotion method if you still want 
    # the 'legacy' keyword detection as a backup.