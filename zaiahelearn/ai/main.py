from dotenv import load_dotenv
from pydantic import BaseModel
#from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
#from langchain.agents import create_tool_calling_agent

load_dotenv()


class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

#llm1 = ChatOpenAI(model="gpt-4o-mini")
llm2 = ChatAnthropic(model="claude-haiku-4-5-20251001")

#parser = PydanticOutputParser(pydantic_object=ResearchResponse)

#prompt = ChatPromptTemplate.from_messages()

'''
agent = create_tool_calling_agent(
    tool=llm2,
    prompt=prompt,
    tools=[],
)
'''

def ai_generate_questions(content):
    pass

#response = llm2.invoke("what is a topological space?")

#print (response)