class ConversationMemory:
    def __init__(self):
        self.history = []

    def add(self, user, bot):
        self.history.append({
            "user": user,
            "bot": bot
        })

    def get_context(self):
        context = ""
        for turn in self.history[-5:]:
            context += f"User: {turn['user']}\n"
            context += f"Bot: {turn['bot']}\n"
        return context