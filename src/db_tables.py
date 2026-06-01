"""
Single file to configure which tables the DB agent can access.
Swap this file (or edit TABLES) to point the agent at a different schema.

Field reference per table entry:
  columns        list[str]   columns to SELECT and return
  search_columns list[str]   columns used in LIKE keyword filters
  order_by       str         default ORDER BY column (descending)
  primary_key    str         primary key column (default "id")
  parent_refs    dict        {col: (ref_table, ref_col)}  — FK to a parent row
  child_tables   dict        {child_table: {foreign_key, search_columns, columns}}
                             child rows are searched and their parent IDs are
                             resolved automatically in smart_search
"""

from typing import Any

TABLES: dict[str, dict[str, Any]] = {
    "users": {
        "columns": ["id", "email", "full_name", "created_at"],
        "search_columns": ["id", "email", "full_name"],
        "order_by": "created_at",
    },
    "products": {
        "columns": ["id", "name", "slug", "created_at", "created_by"],
        "search_columns": ["name", "slug"],
        "order_by": "created_at",
        "parent_refs": {"created_by": ("users", "id")},
        "child_tables": {
            "product_variants": {
                "foreign_key": "product_id",
                "search_columns": ["sku"],
                "columns": ["id", "sku"],
            }
        },
    },
    "product_variants": {
        "columns": ["id", "product_id", "sku", "created_at"],
        "search_columns": ["sku"],
        "order_by": "created_at",
        "parent_refs": {"product_id": ("products", "id")},
    },
}
