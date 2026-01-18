from langchain_openai import AzureChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool

from common import gpt_4o_config
from config.env_setup import init_env_and_session

# ------------------------------------------------------------------
# 1. Init env
# ------------------------------------------------------------------
session = init_env_and_session()

# ------------------------------------------------------------------
# 2. Azure OpenAI LLM
# ------------------------------------------------------------------
llm = AzureChatOpenAI(
    openai_api_version=gpt_4o_config["api_version"],
    azure_endpoint=gpt_4o_config["api_base"],
    azure_deployment=gpt_4o_config["deployment"],
    model=gpt_4o_config["model"],
    validate_base_url=False,
)

# ------------------------------------------------------------------
# 3. Tools
# ------------------------------------------------------------------

@tool
def say_hello(name: str) -> str:
    """Say hello to a user."""
    return f"Hello {name}! 👋"

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

tools = [say_hello, add_numbers]

# ------------------------------------------------------------------
# 4. Create agent (legacy API)
# ------------------------------------------------------------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,  # IMPORTANT
    verbose=True
)

# ------------------------------------------------------------------
# 5. Run agent
# ------------------------------------------------------------------
if __name__ == "__main__":
    result = agent.invoke("Say hello to Bob and add 5 and 8")
    print("\nFINAL OUTPUT:")
    print(result)
