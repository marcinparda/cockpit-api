from typing import Any

from mcp.server.fastmcp import FastMCP


def register_task_tools(mcp: FastMCP) -> None:
    from src.services.vikunja.client import get_vikunja_token, make_vikunja_client
    import httpx

    def _get_redis():
        from src.services.mcp import server
        return server.redis_client

    @mcp.tool()
    async def vikunja_list_projects() -> Any:
        """List all Vikunja projects. Call to get project IDs for task operations."""
        token = await get_vikunja_token(_get_redis())
        async with make_vikunja_client(token) as c:
            resp = await c.get("/projects")
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def vikunja_get_tasks(
        project_id: int | None = None,
        filter: str | None = None,
        s: str | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> Any:
        """Get tasks with optional filters. Filter syntax: field comparator value, joined with &&.
        Examples: 'due_date<=2026-04-24&&done=false' (overdue open tasks), 'done=false' (all open).

        Args:
            project_id: Filter by project (omit = all projects)
            filter: Filter expression e.g. 'due_date<=2026-04-30&&done=false'
            s: Full-text search
            sort_by: 'due_date', 'created', 'priority', 'title'
            order_by: 'asc' or 'desc'
            page: Page number
            per_page: Results per page, max 500
        """
        token = await get_vikunja_token(_get_redis())
        params: dict[str, Any] = {}
        for key, val in [("filter", filter), ("s", s), ("sort_by", sort_by), ("order_by", order_by), ("page", page), ("per_page", per_page)]:
            if val is not None:
                params[key] = val

        async with make_vikunja_client(token) as c:
            try:
                if project_id is not None:
                    resp = await c.get(f"/projects/{project_id}/tasks", params=params)
                    resp.raise_for_status()
                    return resp.json()

                # Vikunja doesn't expose a global /tasks endpoint — collect across all projects
                projects_resp = await c.get("/projects")
                projects_resp.raise_for_status()
                projects = projects_resp.json()
                if not isinstance(projects, list):
                    projects = [projects]

                all_tasks: list[Any] = []
                for project in projects:
                    pid = project.get("id")
                    if not pid:
                        continue
                    try:
                        t_resp = await c.get(f"/projects/{pid}/tasks", params=params)
                        t_resp.raise_for_status()
                        tasks = t_resp.json()
                        if isinstance(tasks, list):
                            all_tasks.extend(tasks)
                    except httpx.HTTPStatusError:
                        continue
                return all_tasks
            except httpx.HTTPStatusError as e:
                return {"error": f"Vikunja API error {e.response.status_code}", "detail": str(e)}

    @mcp.tool()
    async def vikunja_create_task(
        project_id: int,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        priority: int | None = None,
        assignees: list[int] | None = None,
    ) -> Any:
        """Create a new task. Use vikunja_list_projects for project_id, vikunja_list_users for assignee IDs.

        Args:
            project_id: Project ID
            title: Task title
            description: Optional description
            due_date: ISO 8601 e.g. '2026-04-30T00:00:00Z'
            priority: 0=none, 1=low, 2=medium, 3=high, 4=urgent, 5=critical
            assignees: List of user IDs from vikunja_list_users
        """
        token = await get_vikunja_token(_get_redis())
        task: dict[str, Any] = {"title": title}
        if description:
            task["description"] = description
        if due_date:
            task["due_date"] = due_date
        if priority is not None:
            task["priority"] = priority
        if assignees:
            task["assignees"] = [{"id": uid} for uid in assignees]

        async with make_vikunja_client(token) as c:
            resp = await c.put(f"/projects/{project_id}/tasks", json=task)
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def vikunja_update_task(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        done: bool | None = None,
        due_date: str | None = None,
        priority: int | None = None,
    ) -> Any:
        """Update a task (mark done, change due date, title, description, priority).

        Args:
            task_id: Task ID to update
            title: New title
            description: New description
            done: Mark as done/undone
            due_date: New due date ISO 8601
            priority: 0-5
        """
        token = await get_vikunja_token(_get_redis())
        task: dict[str, Any] = {}
        for key, val in [("title", title), ("description", description), ("done", done), ("due_date", due_date), ("priority", priority)]:
            if val is not None:
                task[key] = val

        async with make_vikunja_client(token) as c:
            resp = await c.post(f"/tasks/{task_id}", json=task)
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def vikunja_delete_task(task_id: int) -> Any:
        """Permanently delete a task.

        Args:
            task_id: Task ID to delete
        """
        token = await get_vikunja_token(_get_redis())
        async with make_vikunja_client(token) as c:
            resp = await c.delete(f"/tasks/{task_id}")
            resp.raise_for_status()
            return {"success": True, "task_id": task_id}

    @mcp.tool()
    async def vikunja_list_users(s: str | None = None) -> Any:
        """Search users by name/username/email to find IDs for assignment.

        Args:
            s: Search query. Omit to list all.
        """
        token = await get_vikunja_token(_get_redis())
        params: dict[str, Any] = {}
        if s:
            params["s"] = s
        async with make_vikunja_client(token) as c:
            resp = await c.get("/users", params=params)
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def vikunja_assign_user_to_task(task_id: int, user_id: int) -> Any:
        """Assign a user to a task.

        Args:
            task_id: Task ID
            user_id: User ID from vikunja_list_users
        """
        token = await get_vikunja_token(_get_redis())
        async with make_vikunja_client(token) as c:
            resp = await c.put(f"/tasks/{task_id}/assignees", json={"user_id": user_id})
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def vikunja_remove_assignee(task_id: int, user_id: int) -> Any:
        """Remove a user assignment from a task.

        Args:
            task_id: Task ID
            user_id: User ID to remove
        """
        token = await get_vikunja_token(_get_redis())
        async with make_vikunja_client(token) as c:
            resp = await c.delete(f"/tasks/{task_id}/assignees/{user_id}")
            resp.raise_for_status()
            return {"success": True, "task_id": task_id, "user_id": user_id}
