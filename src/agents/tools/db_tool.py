from typing import Any

from agents import function_tool
from sqlalchemy import MetaData, String, Table, cast, func, or_, select

from src.lib.db_con import engine

TABLES: dict[str, dict[str, Any]] = {
    "users": {
        "columns": ["id", "email", "full_name", "created_at", "updated_at"],
        "search_columns": ["id", "email", "full_name"],
        "order_by": "created_at",
    },
    "products": {
        "columns": ["id", "name", "slug", "created_at", "updated_at", "created_by"],
        "search_columns": ["id", "name", "slug", "created_by"],
        "order_by": "created_at",
        "relations": {"created_by": "users.id"},
    },
}


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in row.items()
    }


def get_allowed_database_context() -> dict[str, Any]:
    """Return the database tables and fields this agent is allowed to expose."""
    return {
        table_name: {
            "columns": config["columns"],
            "search_columns": config["search_columns"],
            "relations": config.get("relations", {}),
        }
        for table_name, config in TABLES.items()
    }


@function_tool
def list_searchable_tables() -> dict[str, Any]:
    """List only the whitelisted database tables and fields available for read-only search."""
    return get_allowed_database_context()


def search_table_records(
    table_name: str, search: str = "", limit: int = 10
) -> dict[str, Any]:
    """Search a whitelisted database table using only whitelisted searchable fields."""
    table_config = TABLES.get(table_name)

    if table_config is None:
        return {
            "error": "Table is not allowed.",
            "allowed_tables": list(TABLES.keys()),
        }

    safe_limit = max(1, min(limit, 25))
    columns = table_config["columns"]
    order_by = table_config["order_by"]

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    query = select(*[table.c[column] for column in columns])

    if search.strip():
        search_term = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                *[
                    func.lower(cast(table.c[column], String)).like(search_term)
                    for column in table_config["search_columns"]
                ]
            )
        )

    query = query.order_by(table.c[order_by].desc()).limit(safe_limit)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return {
        "table": table_name,
        "allowed_fields": columns,
        "count": len(rows),
        "rows": [serialize_row(dict(row)) for row in rows],
    }


@function_tool
def search_table(table_name: str, search: str = "", limit: int = 10) -> dict[str, Any]:
    """Search a whitelisted database table using only whitelisted searchable fields."""
    return search_table_records(table_name, search, limit)
