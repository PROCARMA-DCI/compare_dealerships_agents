"""
Single file to configure which tables and analytics queries the DB agent can access.
Add new tables to TABLES and new aggregate queries to ANALYTICS.

TABLES field reference per entry:
  columns        list[str]   columns to SELECT and return
  search_columns list[str]   columns used in LIKE keyword filters
  order_by       str         default ORDER BY column (descending)
  primary_key    str         primary key column (default "id")
  parent_refs    dict        {col: (ref_table, ref_col)}  — FK to a parent row
  child_tables   dict        {child_table: {foreign_key, search_columns, columns}}

ANALYTICS field reference per entry:
  description    str         plain-English description shown to the agent
  sql            str         read-only SELECT with GROUP BY / aggregations
                             (LIMIT :limit is appended automatically)
"""

from typing import Any

TABLES: dict[str, dict[str, Any]] = {
    "tbl_contract": {
        "columns": ["ContractID", "DealerID", "MakeID", "ModelID", "SaleDate"],
        "search_columns": ["ContractID"],
        "order_by": "ContractID",
        "primary_key": "ContractID",
        "parent_refs": {
            "DealerID": ("tbl_dealer", "DealerID"),
            "MakeID": ("tbl_make", "MakeID"),
            "ModelID": ("tbl_model", "ModelID"),
        },
        "child_tables": {
            "contractcoupon": {
                "foreign_key": "ContractID",
                "search_columns": ["ContractID"],
                "columns": ["ContractID", "IsRedeem", "PostedDate"],
            }
        },
    },
    "tbl_dealer": {
        "columns": ["DealerID", "DealerTitle"],
        "search_columns": ["DealerTitle"],
        "order_by": "DealerID",
        "primary_key": "DealerID",
    },
    "tbl_make": {
        "columns": ["MakeID", "Make"],
        "search_columns": ["Make"],
        "order_by": "MakeID",
        "primary_key": "MakeID",
    },
    "tbl_model": {
        "columns": ["ModelID", "Model"],
        "search_columns": ["Model"],
        "order_by": "ModelID",
        "primary_key": "ModelID",
    },
    "contractcoupon": {
        "columns": ["ContractID", "IsRedeem", "PostedDate"],
        "search_columns": ["ContractID"],
        "order_by": "ContractID",
        "primary_key": "ContractID",
        "parent_refs": {
            "ContractID": ("tbl_contract", "ContractID"),
        },
    },
}

# ── Analytics queries ────────────────────────────────────────────────────────
# Add new aggregate / ranking / comparison queries here.
# Each entry is identified by a snake_case name the agent passes to run_analytics.
# Keep sql read-only (SELECT only). LIMIT is appended automatically.

ANALYTICS: dict[str, dict[str, Any]] = {
    "services_redeemed_by_dealer": {
        "description": (
            "Total sold plans vs redeemed services per dealership, ranked by most redeemed. "
            "Use for: which dealer redeems the most, redemption rates, plans vs redemptions."
        ),
        "sql": """
            SELECT
                td.DealerTitle,
                COUNT(DISTINCT tc.ContractID)                        AS TotalSoldPlans,
                COUNT(CASE WHEN cc.IsRedeem = 1 THEN 1 END)         AS TotalRedeemed
            FROM tbl_contract tc
            INNER JOIN tbl_dealer td
                ON tc.DealerID = td.DealerID
            LEFT JOIN contractcoupon cc
                ON cc.ContractID = tc.ContractID
            GROUP BY td.DealerTitle
            ORDER BY TotalRedeemed DESC
        """,
    },
    "most_common_cars": {
        "description": (
            "Most common car make/model combinations ranked by contract count. "
            "Use for: most popular car, top models, which car appears most."
        ),
        "sql": """
            SELECT
                tm.Make       AS CarMake,
                tmo.Model     AS CarModel,
                COUNT(tc.ContractID) AS TotalContracts
            FROM tbl_contract tc
            INNER JOIN tbl_make tm
                ON tc.MakeID = tm.MakeID
            INNER JOIN tbl_model tmo
                ON tc.ModelID = tmo.ModelID
            GROUP BY tm.Make, tmo.Model
            ORDER BY TotalContracts DESC
        """,
    },
    "avg_days_to_pay_by_dealer": {
        "description": (
            "Average days from sale date to payment posting per dealership (fastest payers first). "
            "Use for: which dealer pays fastest/slowest, payment timing, days to pay."
        ),
        "sql": """
            SELECT
                td.DealerTitle,
                ROUND(
                    AVG(
                        DATEDIFF(cc.PostedDate, FROM_UNIXTIME(tc.SaleDate))
                    ),
                    2
                ) AS AvgDaysToPay
            FROM tbl_contract tc
            INNER JOIN tbl_dealer td
                ON tc.DealerID = td.DealerID
            INNER JOIN contractcoupon cc
                ON cc.ContractID = tc.ContractID
            WHERE cc.PostedDate IS NOT NULL
            GROUP BY td.DealerTitle
            ORDER BY AvgDaysToPay ASC
        """,
    },
}
