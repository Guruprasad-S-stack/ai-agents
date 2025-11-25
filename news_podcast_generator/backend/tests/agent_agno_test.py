from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response
from utils.env_loader import load_backend_env

load_backend_env()
agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))
response: RunResponse = agent.run("Tell me a 5 second short story about a robot")
response_stream: Iterator[RunResponse] = agent.run("Tell me a 5 second short story about a lion", stream=True)
pprint_run_response(response, markdown=True)
pprint_run_response(response_stream, markdown=True)
