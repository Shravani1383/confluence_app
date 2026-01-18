from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import AzureChatOpenAI

# -----------------------
# Tools
# -----------------------
@tool
def say_hello(name: str) -> str:
    """Say hello to a user by name."""
    return f"Hello {name}!"

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

tools = [say_hello, add]

# -----------------------
# LLM (Azure)
# -----------------------
llm = AzureChatOpenAI(
    azure_endpoint="https://<your-resource>.openai.azure.com/",
    azure_deployment="<your-deployment>",
    openai_api_version="2024-02-15-preview",
    model="gpt-4o-mini",
    validate_base_url=False,
)

# -----------------------
# Prompt
# -----------------------
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# -----------------------
# Agent
# -----------------------
agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)

# -----------------------
# Run
# -----------------------
result = agent_executor.invoke(
    {"input": "Say hello to Bob and add 10 and 5"}
)

print(result["output"])
