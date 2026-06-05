from typing import Any

from agents import function_tool
from sqlalchemy import MetaData, String, Table, cast, func, or_, select, text

from src.db_tables import ANALYTICS, TABLES
from src.lib.db_con import engine


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in row.items()}


def get_allowed_context() -> dict[str, Any]:
    """Compact schema summary sent to the agent — only what it needs."""
    return {
        name: {
            "columns": cfg["columns"],
            "search_columns": cfg["search_columns"],
            **({"parent_refs": cfg["parent_refs"]} if cfg.get("parent_refs") else {}),
            **(
                {
                    "child_tables": {
                        child: {
                            "foreign_key": c["foreign_key"],
                            "search_columns": c["search_columns"],
                        }
                        for child, c in cfg["child_tables"].items()
                    }
                }
                if cfg.get("child_tables")
                else {}
            ),
        }
        for name, cfg in TABLES.items()
    }


def get_analytics_context() -> dict[str, str]:
    """Returns {query_name: description} for all analytics queries."""
    return {name: cfg["description"] for name, cfg in ANALYTICS.items()}


@function_tool
def list_tables() -> dict[str, Any]:
    """List available tables, their columns, and searchable fields."""
    return get_allowed_context()


@function_tool
def list_analytics() -> dict[str, str]:
    """List all available analytics query names and what each one returns."""
    return get_analytics_context()


@function_tool
def run_analytics(query_name: str, limit: int = 25) -> dict[str, Any]:
    """
    Run a predefined analytics/aggregation query by name.
    Use for questions about rankings, totals, averages, and comparisons —
    e.g. most common car, which dealership redeems most, average days to pay.
    Call list_analytics first if you are unsure which query_name to use.
    """
    cfg = ANALYTICS.get(query_name)
    if cfg is None:
        return {
            "error": f"Analytics query '{query_name}' not found.",
            "available": get_analytics_context(),
        }

    safe_limit = max(1, min(limit, 100))
    sql = f"{cfg['sql'].strip()} LIMIT {safe_limit}"

    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()

    return {
        "query": query_name,
        "description": cfg["description"],
        "count": len(rows),
        "rows": [serialize_row(dict(r)) for r in rows],
    }


@function_tool
def smart_search(
    table_name: str, keywords: list[str], limit: int = 10
) -> dict[str, Any]:
    """
    Search a table using multiple keywords extracted from a natural language query.
    Automatically searches child tables (e.g. contractcoupon when table is tbl_contract)
    and returns merged, deduplicated results.

    Use for record lookups — e.g. find a dealer by name, look up a contract ID.
    For aggregate/ranking questions use run_analytics instead.
    """
    cfg = TABLES.get(table_name)
    if cfg is None:
        return {
            "error": f"Table '{table_name}' not found.",
            "available": list(TABLES.keys()),
        }

    safe_limit = max(1, min(limit, 25))
    clean = [k.strip().lower() for k in keywords if k.strip()]
    if not clean:
        return {"error": "Provide at least one keyword."}

    pk = cfg.get("primary_key", "id")
    meta = MetaData()
    tbl = Table(table_name, meta, autoload_with=engine)
    col_objs = [tbl.c[c] for c in cfg["columns"]]

    def like_conds(t: Table, search_cols: list[str]) -> list:
        return [
            func.lower(cast(t.c[col], String)).like(f"%{kw}%")
            for kw in clean
            for col in search_cols
        ]

    results: dict[Any, dict] = {}

    with engine.connect() as conn:
        # --- child table search: collect parent IDs ---
        child_ids: set = set()
        for child_name, child_cfg in cfg.get("child_tables", {}).items():
            child_tbl = Table(child_name, meta, autoload_with=engine)
            conds = like_conds(child_tbl, child_cfg["search_columns"])
            if conds:
                fk = child_cfg["foreign_key"]
                for row in conn.execute(
                    select(child_tbl.c[fk]).where(or_(*conds)).distinct()
                ):
                    child_ids.add(row[0])

        # --- primary table keyword search ---
        primary_conds = like_conds(tbl, cfg["search_columns"])
        if primary_conds:
            q = (
                select(*col_objs)
                .where(or_(*primary_conds))
                .order_by(tbl.c[cfg["order_by"]].desc())
                .limit(safe_limit)
            )
            for row in conn.execute(q).mappings():
                d = serialize_row(dict(row))
                results[d[pk]] = d

        # --- fetch parent rows matched only via child search ---
        missing = [i for i in child_ids if i not in results]
        if missing:
            remaining = safe_limit - len(results)
            if remaining > 0:
                q = (
                    select(*col_objs)
                    .where(tbl.c[pk].in_(missing[:remaining]))
                    .order_by(tbl.c[cfg["order_by"]].desc())
                )
                for row in conn.execute(q).mappings():
                    d = serialize_row(dict(row))
                    results[d[pk]] = d

    rows = list(results.values())[:safe_limit]
    return {"table": table_name, "keywords": clean, "count": len(rows), "rows": rows}
