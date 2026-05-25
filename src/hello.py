import config

from agents import Agent, Runner

agent = Agent(
    name="Hello Agent",
    instructions="You are a agent always say hello to the user with their name",
)

result = Runner.run_sync(agent, "Hey! My name is Usama bin ladin")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
