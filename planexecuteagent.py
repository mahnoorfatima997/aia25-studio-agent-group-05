import operator
from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph, START
import requests
import llm_calls
from server.keys import TAVILY_API_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_KEY

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

tools = [TavilySearch(tavily_api_key=TAVILY_API_KEY, max_results=1)]

class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

PLANNER_SYSTEM_PROMPT = """For the given objective, come up with a simple step by step plan.
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps."""

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", PLANNER_SYSTEM_PROMPT),
    ("placeholder", "{messages}"),
])

from langchain_core.messages import AIMessage

CLOUDFLARE_MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct"  # or another supported model

def call_cloudflare_workers_ai(messages):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["result"]["response"]

async def plan_step(state: PlanExecute):
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": state["input"]}
    ]
    response = call_cloudflare_workers_ai(messages)
    steps = [line.strip() for line in response.split('\n') if line.strip()]
    return {"plan": steps}

class Response(BaseModel):
    """Response to user."""
    response: str

class Act(BaseModel):
    """Action to perform."""
    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan.
    This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
    The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

    Your objective was this:
    {input}

    Your original plan was this:
    {plan}

    You have currently done the follow steps:
    {past_steps}

    Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)

async def replan_step(state: PlanExecute):
    messages = [
        {"role": "system", "content": replanner_prompt.format(
            input=state['input'],
            plan=state['plan'],
            past_steps=state['past_steps']
        )},
        {"role": "user", "content": ""}
    ]
    response = call_cloudflare_workers_ai(messages)
    # You may need to parse response to extract steps or final answer
    if "Final Answer:" in response:
        return {"response": response.split("Final Answer:")[-1].strip()}
    else:
        steps = [line.strip() for line in response.split('\n') if line.strip()]
        return {"plan": steps}

async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step 1, {task}."""
    messages = [
        {"role": "system", "content": "You are executing a step of a plan."},
        {"role": "user", "content": task_formatted}
    ]
    response = call_cloudflare_workers_ai(messages)
    concept = llm_calls.generate_concept(state["input"])
    imageprompt = llm_calls.generate_prompt(concept)
    attributes = llm_calls.extract_attributes(concept)
    weights = llm_calls.generate_weights(concept)
    locations = llm_calls.generate_locations(concept)
    return {
        "concept": concept,
        "imageprompt": imageprompt,
        "attributes": attributes,
        "weights": weights,
        "locations": locations,
        "past_steps": [(task, response)],
    }

def should_end(state: PlanExecute):
    # Stop if response is set
    if "response" in state and state["response"]:
        return END
    # Stop if plan is empty or only contains a final answer
    plan = state.get("plan", [])
    if not plan or any("final answer" in step.lower() for step in plan):
        return END
    return "agent"

workflow = StateGraph(PlanExecute)
workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges(
    "replan",
    should_end,
    ["agent", END],
)

app = workflow.compile()

# Save the workflow graph as a PNG file (now works!)
with open("workflow_graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())
print("Workflow graph saved as workflow_graph.png")

async def run_agent_with_input(user_input: str, config: dict = None):
    if config is None:
        config = {"recursion_limit": 10}
    inputs = {"input": user_input}
    results = []
    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                results.append(v)
    return results

def run_agent_with_input_sync(user_input: str, config: dict = None):
    import asyncio
    return asyncio.run(run_agent_with_input(user_input, config))

async def main(user_input="Design me a small courtyard garden for a warm climate"):
    config = {"recursion_limit": 10}
    inputs = {"input": user_input}
    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)

if __name__ == "__main__":
    import sys
    user_input = sys.argv[1] if len(sys.argv) > 1 else "Design me a small courtyard garden for a warm climate"
    import asyncio
    asyncio.run(main(user_input))