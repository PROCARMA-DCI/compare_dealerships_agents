import re
from typing import Any

from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
from agents.exceptions import InputGuardrailTripwireTriggered

from src.agents.tools.db_tool import (
    get_allowed_database_context,
    list_searchable_tables,
    search_table,
)
from src.lib.chat_session import get_or_create_chat_session


WRITE_ACTION_PATTERN = re.compile(
    r"\b("
    r"create\s+(a|an|new|record|row|user|product)|"
    r"insert|"
    r"add\s+(a|an|new|record|row|user|product)|"
    r"update|edit|patch|delete|remove|drop|truncate|alter"
    r")\b",
    re.IGNORECASE,
)
@input_guardrail(name="read_only_database_input_guardrail", run_in_parallel=False)
def read_only_database_input_guardrail(
    context: Any,
    agent: Agent,
    user_input: str | list[Any],
) -> GuardrailFunctionOutput:
    input_text = str(user_input)

    if WRITE_ACTION_PATTERN.search(input_text):
        return GuardrailFunctionOutput(
            output_info="Only read-only search requests are allowed.",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="Request is read-only and within allowed database access.",
        tripwire_triggered=False,
    )


database_agent = Agent(
    name="Read Only Database Search Assistant",
    instructions=f"""
    You help users search database records using only the provided tools.

    Rules:
    - Read-only search only.
    - Never create, update, edit, patch, delete, remove, drop, truncate, or alter data.
    - Never ask the user for extra database fields.
    - Only use these configured tables and fields:
      {get_allowed_database_context()}
    - If the user asks for a field outside this allowlist, do not block the whole answer.
      Explain that the field is not available, then answer using the configured fields.
    - Products.created_by references users.id. When asked who created a product, first search
      products, then search users by the created_by id.
    - If the request is missing a table, call list_searchable_tables and explain the allowed tables.
    - Use search_table for database lookups.
    - Return concise Markdown with the matching rows.
    """,
    tools=[
        list_searchable_tables,
        search_table,
    ],
    input_guardrails=[
        read_only_database_input_guardrail,
    ],
)


async def run_database_agent(message: str, session_id: str | None = None):
    session = await get_or_create_chat_session(session_id)

    try:
        result = await Runner.run(
            database_agent,
            message,
            session=session,
        )
    except InputGuardrailTripwireTriggered as exc:
        return {
            "session_id": session.session_id,
            "blocked": True,
            "reason": exc.guardrail_result.output.output_info,
        }

    return {
        "session_id": session.session_id,
        "blocked": False,
        "result": result.final_output,
    }
