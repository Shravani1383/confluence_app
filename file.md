from langchain_openai import AzureChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool

# ------------------------------------------------------------------
# 1. Your existing imports / config
# ------------------------------------------------------------------
from common import gpt_4o_config
from config.env_setup import init_env_and_session

# Initialize env and session (as in your code)
session = init_env_and_session()

# ------------------------------------------------------------------
# 2. Initialize Azure OpenAI LLM (UNCHANGED from your usage)
# ------------------------------------------------------------------
llm = AzureChatOpenAI(
    openai_api_version=gpt_4o_config["api_version"],
    azure_endpoint=gpt_4o_config["api_base"],
    azure_deployment=gpt_4o_config["deployment"],
    model=gpt_4o_config["model"],
    validate_base_url=False,
)

# ------------------------------------------------------------------
# 3. Define tools (agent capabilities)
# ------------------------------------------------------------------

@tool
def say_hello(name: str) -> str:
    """Say hello to a user by name."""
    return f"Hello {name}! 👋"

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

tools = [say_hello, add_numbers]

# ------------------------------------------------------------------
# 4. Create agent prompt
# ------------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# ------------------------------------------------------------------
# 5. Create the agent
# ------------------------------------------------------------------
agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# ------------------------------------------------------------------
# 6. Create agent executor (runs the loop)
# ------------------------------------------------------------------
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True  # IMPORTANT: shows tool calls
)

# ------------------------------------------------------------------
# 7. Run the agent
# ------------------------------------------------------------------
if __name__ == "__main__":
    response = agent_executor.invoke({
        "input": "Say hello to Alice and then add 4 and 7"
    })

    print("\nFINAL OUTPUT:")
    print(response["output"])
