from typing import Any

from mcp.server.fastmcp import FastMCP


def register_budget_tools(mcp: FastMCP) -> None:
    from src.services.actual_budget.client import make_actual_client
    from src.core.config import settings

    def _budget_path(path: str) -> str:
        return f"/v1/budgets/{settings.ACTUAL_BUDGET_SYNC_ID}{path}"

    @mcp.tool()
    async def actual_list_accounts() -> Any:
        """List all Actual Budget accounts. Call first to get account IDs needed for transaction operations."""
        async with make_actual_client() as c:
            resp = await c.get(_budget_path("/accounts"))
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_create_account(name: str, offbudget: bool) -> Any:
        """Create a new budget account.

        Args:
            name: Account name
            offbudget: True = off-budget tracking account, false = regular budget account
        """
        async with make_actual_client() as c:
            resp = await c.post(
                _budget_path("/accounts"),
                json={"account": {"name": name, "offbudget": offbudget}},
            )
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_list_categories() -> Any:
        """List all budget categories and groups. Call to get category IDs for transactions."""
        async with make_actual_client() as c:
            resp = await c.get(_budget_path("/categories"))
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_list_payees() -> Any:
        """List all payees (merchants/vendors). Check before creating transactions to reuse existing IDs."""
        async with make_actual_client() as c:
            resp = await c.get(_budget_path("/payees"))
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_search_transactions(
        account_id: str,
        since_date: str,
        until_date: str | None = None,
    ) -> Any:
        """Search transactions in an account within a date range.

        Args:
            account_id: Account ID from actual_list_accounts
            since_date: Start date YYYY-MM-DD
            until_date: End date YYYY-MM-DD (optional)
        """
        import asyncio

        params: dict[str, Any] = {"since_date": since_date}
        if until_date:
            params["until_date"] = until_date

        async with make_actual_client() as c:
            txn_resp, cat_resp = await asyncio.gather(
                c.get(_budget_path(f"/accounts/{account_id}/transactions"), params=params),
                c.get(_budget_path("/categories")),
            )
            txn_resp.raise_for_status()
            cat_resp.raise_for_status()

        txn_data = txn_resp.json()
        cat_data = cat_resp.json()
        category_map: dict[str, str] = {cat["id"]: cat["name"] for cat in cat_data.get("data", [])}

        transactions = txn_data.get("data", txn_data)
        for txn in transactions:
            cid = txn.get("category")
            if cid and cid in category_map:
                txn["category"] = category_map[cid]

        if isinstance(txn_data, dict):
            txn_data["data"] = transactions
            return txn_data
        return transactions

    @mcp.tool()
    async def actual_create_transaction(
        account_id: str,
        date: str,
        amount: int,
        payee_name: str | None = None,
        category_id: str | None = None,
        notes: str | None = None,
        cleared: bool = False,
    ) -> Any:
        """Create a single transaction. Amount in milliunits: 1000 = $1.00, negative = expense (-10500 = -$10.50).

        Args:
            account_id: Account ID
            date: YYYY-MM-DD
            amount: Milliunits. Negative = expense, positive = income.
            payee_name: Merchant name (creates payee if new)
            category_id: Category ID (optional)
            notes: Optional notes
            cleared: Cleared status
        """
        transaction: dict[str, Any] = {"date": date, "amount": amount}
        if payee_name:
            transaction["payee_name"] = payee_name
        if category_id:
            transaction["category"] = category_id
        if notes:
            transaction["notes"] = notes
        transaction["cleared"] = cleared

        async with make_actual_client() as c:
            resp = await c.post(
                _budget_path(f"/accounts/{account_id}/transactions"),
                json={"transaction": transaction},
            )
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_batch_create_transactions(
        account_id: str,
        transactions: list[dict[str, Any]],
        learn_categories: bool = True,
    ) -> Any:
        """Create multiple transactions at once. Use for bank statement imports. Amount in milliunits, negative = expense.

        Args:
            account_id: Account ID for all transactions
            transactions: List of transactions, each with date (YYYY-MM-DD), amount (milliunits), optional payee_name, category_id, notes
            learn_categories: Let Actual learn from payee patterns
        """
        txns = []
        for t in transactions:
            tx: dict[str, Any] = {"date": t["date"], "amount": t["amount"]}
            if t.get("payee_name"):
                tx["payee_name"] = t["payee_name"]
            if t.get("category_id"):
                tx["category"] = t["category_id"]
            if t.get("notes"):
                tx["notes"] = t["notes"]
            txns.append(tx)

        async with make_actual_client() as c:
            resp = await c.post(
                _budget_path(f"/accounts/{account_id}/transactions/batch"),
                json={"transactions": txns, "learnCategories": learn_categories},
            )
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_update_transaction(
        transaction_id: str,
        category_id: str | None = None,
        payee_name: str | None = None,
        notes: str | None = None,
        cleared: bool | None = None,
        date: str | None = None,
        amount: int | None = None,
    ) -> Any:
        """Update a transaction (assign category, fix payee, update notes, mark cleared).

        Args:
            transaction_id: Transaction ID to update
            category_id: New category ID
            payee_name: New payee name
            notes: New notes
            cleared: New cleared status
            date: New date YYYY-MM-DD
            amount: New amount in milliunits
        """
        transaction: dict[str, Any] = {}
        if category_id is not None:
            transaction["category"] = category_id
        if payee_name is not None:
            transaction["payee_name"] = payee_name
        if notes is not None:
            transaction["notes"] = notes
        if cleared is not None:
            transaction["cleared"] = cleared
        if date is not None:
            transaction["date"] = date
        if amount is not None:
            transaction["amount"] = amount

        async with make_actual_client() as c:
            resp = await c.patch(
                _budget_path(f"/transactions/{transaction_id}"),
                json={"transaction": transaction},
            )
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def actual_delete_transaction(transaction_id: str) -> Any:
        """Delete a transaction by ID.

        Args:
            transaction_id: Transaction ID to delete
        """
        async with make_actual_client() as c:
            resp = await c.delete(_budget_path(f"/transactions/{transaction_id}"))
            resp.raise_for_status()
            return {"success": True, "transaction_id": transaction_id}
