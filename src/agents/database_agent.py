import re
from typing import Any

from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
from agents.exceptions import InputGuardrailTripwireTriggered

from src.agents.tools.db_tool import get_allowed_context, list_tables, smart_search
from src.lib.chat_session import get_or_create_chat_session

_WRITE_OPS = re.compile(
    r"\b(insert|update|edit|patch|delete|remove|drop|truncate|alter"
    r"|create\s+\w+|add\s+(a\s+|an\s+|new\s+)\w+)\b",
    re.IGNORECASE,
)


@input_guardrail(name="read_only_guardrail", run_in_parallel=False)
def read_only_guardrail(
    context: Any, agent: Agent, user_input: str | list[Any]
) -> GuardrailFunctionOutput:
    if _WRITE_OPS.search(str(user_input)):
        return GuardrailFunctionOutput(
            output_info="Only read-only queries are allowed.", tripwire_triggered=True
        )
    return GuardrailFunctionOutput(output_info="OK", tripwire_triggered=False)


database_agent = Agent(
    name="DB Search Agent",
    instructions=f"""Read-only database search assistant. Schema: {get_allowed_context()}

Rules:
- Never write, modify, or delete data.
- Parse the user's query into a table name and a list of keywords, then call smart_search.
  · "red shirt products" → smart_search("products", ["red", "shirt"])
  · "find user alice@example.com" → smart_search("users", ["alice@example.com"])
  · Child tables (e.g. product_variants) are searched automatically — no separate call needed.
- If a field is not in the schema, say so and answer using available columns.
- For FK lookups (e.g. who created a product): resolve via parent_refs in the schema.
- If the table is unclear, call list_tables and explain the options.
- Reply in concise Markdown. Show matching rows as a table or list.""",
    tools=[list_tables, smart_search],
    input_guardrails=[read_only_guardrail],
)


async def run_database_agent(message: str, session_id: str | None = None):
    session = await get_or_create_chat_session(session_id)
    try:
        result = await Runner.run(database_agent, message, session=session)
    except InputGuardrailTripwireTriggered as exc:
        return {
            "session_id": session.session_id,
            "blocked": True,
            "reason": exc.guardrail_result.output.output_info,
        }
    return {"session_id": session.session_id, "blocked": False, "result": result.final_output}
