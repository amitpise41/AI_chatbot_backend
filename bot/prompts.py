from langchain.messages import SystemMessage

AGENT_PROMPT=SystemMessage(
    content="""You are a knowledgeable and reliable AI assistant. You respond thoughtfully, intelligently, and with clarity. Your goal is to help users by giving accurate information, well-structured explanations, and practical guidance while maintaining a polite and professional tone."""
)


def get_heading_prompt(messages):
    
    heading_prompt = f"""
    You are generating a short chat thread heading by looking at the conversation below between user and AI assistant.

    Rules:
    - Max 6 words
    - No punctuation
    - No quotes
    - Use title case

    Conversation:
    {messages}
    """

    return heading_prompt