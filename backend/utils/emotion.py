from textblob import TextBlob

class EmotionEngine:
    def __init__(self):
        self.mood = "focused"
        self.energy = 80
        self.curiosity = 90
        self.mood_colors = {
            "happy": "#00ff88",
            "focused": "#00d4ff",
            "agitated": "#ff4444",
            "thoughtful": "#aa88ff",
            "empathetic": "#ff88aa",
            "playful": "#88ff44",
            "curious": "#88aaff",
            "calm": "#44ff88",
            "neutral": "#00d4ff",
            "sad": "#4444ff",
            "angry": "#ff0000",
            "anxious": "#ff8800",
            "excited": "#ffff00",
            "bored": "#888888",
            "confused": "#ff44ff",
            "grateful": "#44ffff",
            "lonely": "#884400",
            "capricious": "#ff44aa",
            "melancholy": "#0000ff",
            "optimistic": "#00ff00",
            "pessimistic": "#ff8800",
            "romantic": "#ff88ff",
            "sarcastic": "#888800",
            "sympathetic": "#44ff44",
            "tired": "#444400",
            "worried": "#ff4444",
        }

    def update_emotion(self, message):
        blob = TextBlob(message)
        polarity = blob.sentiment.polarity
        if polarity > 0.3:
            self.mood = "happy"
        elif polarity < -0.3:
            self.mood = "agitated"
        elif "sad" in message.lower() or "lonely" in message.lower() or "bad" in message.lower() or "upset" in message.lower() or "depressed" in message.lower() or "unhappy" in message.lower() or "miserable" in message.lower() or "down" in message.lower() or "heartbroken" in message.lower() or "gloomy" in message.lower() or "melancholy" in message.lower() or "sorrowful" in message.lower() or "despair" in message.lower() or "hopeless" in message.lower() or "grief" in message.lower() or "anguish" in message.lower() or "distressed" in message.lower() or "dejection" in message.lower() or "woeful" in message.lower() or "forlorn" in message.lower() or "desolate" in message.lower() or "heartache" in message.lower() or "mournful" in message.lower() or "sorrow" in message.lower() or "wretched" in message.lower() or "bleak" in message.lower() or "dismal" in message.lower() or "somber" in message.lower() or "depressed" in message.lower() or "unhappy" in message.lower() or "miserable" in message.lower() or "down" in message.lower() or "heartbroken" in message.lower() or "gloomy" in message.lower() or "melancholy" in message.lower() or "sorrowful" in message.lower() or "despair" in message.lower() or "hopeless" in message.lower() or "grief" in message.lower() or "anguish" in message.lower() or "distressed" in message.lower() or "dejection" in message.lower() or "woeful" in message.lower() or "forlorn" in message.lower() or "desolate" in message.lower() or "heartache" in message.lower() or "mournful" in message.lower() or "sorrow" in message.lower() or "wretched" in message.lower() or "bleak" in message.lower() or "dismal" in message.lower() or "somber" in message.lower():
            self.mood = "empathetic"
        else:
            self.mood = "focused"

    def get_state(self):
        return {
            'mood': self.mood,
            'energy': self.energy,
            'curiosity': self.curiosity,
            'color': self.mood_colors.get(self.mood, '#00d4ff')
        }