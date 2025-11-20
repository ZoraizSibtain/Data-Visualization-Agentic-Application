from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class LLMManager:
    def __init__(self):
        # Use gpt-4o-mini for faster responses (3-5x faster than gpt-4o)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        # Keep gpt-4o for complex tasks if needed
        self.llm_advanced = ChatOpenAI(model="gpt-4o", temperature=0)

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        response = self.llm.invoke(messages)
        return response.content

    def invoke_advanced(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        """Use for complex reasoning tasks that need gpt-4o"""
        messages = prompt.format_messages(**kwargs)
        response = self.llm_advanced.invoke(messages)
        return response.content