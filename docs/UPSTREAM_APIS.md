# Upstream API Documentation

Full OpenAPI specs are in this directory. Use them to identify endpoints to proxy.

- `actual-budget.openapi.json` — Actual HTTP API v26.4.0 (OpenAPI 3.1.0)
- `vikunja.openapi.json` — Vikunja (Swagger 2.0)

To refresh specs: `./docs/update-upstream-docs.sh`
(Vikunja fetched from GitHub main branch; Actual Budget fetched live from raspberry via SSH.)

---

## Actual Budget HTTP API — 43 paths

Auth: `x-api-key` header. All budget endpoints prefixed `/v1/budgets/{budgetSyncId}/`.

| Method | Path | Summary |
|--------|------|---------|
| GET | /actualhttpapiversion | Actual HTTP API version |
| GET | /budgets | List all budget files |
| GET | /budgets/{budgetSyncId}/accounts | List accounts |
| POST | /budgets/{budgetSyncId}/accounts | Create account |
| GET | /budgets/{budgetSyncId}/accounts/{accountId} | Get account |
| PATCH | /budgets/{budgetSyncId}/accounts/{accountId} | Update account |
| DELETE | /budgets/{budgetSyncId}/accounts/{accountId} | Delete account |
| GET | /budgets/{budgetSyncId}/accounts/{accountId}/balance | Get balance |
| GET | /budgets/{budgetSyncId}/accounts/{accountId}/balancehistory | Get balance history |
| PUT | /budgets/{budgetSyncId}/accounts/{accountId}/close | Close account |
| PUT | /budgets/{budgetSyncId}/accounts/{accountId}/reopen | Reopen account |
| POST | /budgets/{budgetSyncId}/accounts/{accountId}/banksync | Bank sync (single account) |
| POST | /budgets/{budgetSyncId}/accounts/banksync | Bank sync (all accounts) |
| GET | /budgets/{budgetSyncId}/accounts/{accountId}/transactions | List transactions |
| POST | /budgets/{budgetSyncId}/accounts/{accountId}/transactions | Create transaction |
| POST | /budgets/{budgetSyncId}/accounts/{accountId}/transactions/batch | Bulk create transactions |
| POST | /budgets/{budgetSyncId}/accounts/{accountId}/transactions/import | Import transactions |
| PATCH | /budgets/{budgetSyncId}/transactions/{transactionId} | Update transaction |
| DELETE | /budgets/{budgetSyncId}/transactions/{transactionId} | Delete transaction |
| DELETE | /budgets/{budgetSyncId}/transactions/batch | Bulk delete transactions |
| GET | /budgets/{budgetSyncId}/categories | List categories |
| POST | /budgets/{budgetSyncId}/categories | Create category |
| GET | /budgets/{budgetSyncId}/categories/{categoryId} | Get category |
| PATCH | /budgets/{budgetSyncId}/categories/{categoryId} | Update category |
| DELETE | /budgets/{budgetSyncId}/categories/{categoryId} | Delete category |
| GET | /budgets/{budgetSyncId}/categorygroups | List category groups |
| POST | /budgets/{budgetSyncId}/categorygroups | Create category group |
| PATCH | /budgets/{budgetSyncId}/categorygroups/{categoryGroupId} | Update category group |
| DELETE | /budgets/{budgetSyncId}/categorygroups/{categoryGroupId} | Delete category group |
| GET | /budgets/{budgetSyncId}/months | List budget months |
| GET | /budgets/{budgetSyncId}/months/{month} | Get budget month |
| GET | /budgets/{budgetSyncId}/months/{month}/categories | List categories for month |
| GET | /budgets/{budgetSyncId}/months/{month}/categories/{categoryId} | Get category for month |
| PATCH | /budgets/{budgetSyncId}/months/{month}/categories/{categoryId} | Update category for month |
| GET | /budgets/{budgetSyncId}/months/{month}/categorygroups | List category groups for month |
| GET | /budgets/{budgetSyncId}/months/{month}/categorygroups/{categoryGroupId} | Get category group for month |
| POST | /budgets/{budgetSyncId}/months/{month}/categorytransfers | Create category transfer |
| POST | /budgets/{budgetSyncId}/months/{month}/nextmonthbudgethold | Set next month budget hold |
| DELETE | /budgets/{budgetSyncId}/months/{month}/nextmonthbudgethold | Reset next month budget hold |
| GET | /budgets/{budgetSyncId}/payees | List payees |
| POST | /budgets/{budgetSyncId}/payees | Create payee |
| GET | /budgets/{budgetSyncId}/payees/{payeeId} | Get payee |
| PATCH | /budgets/{budgetSyncId}/payees/{payeeId} | Update payee |
| DELETE | /budgets/{budgetSyncId}/payees/{payeeId} | Delete payee |
| GET | /budgets/{budgetSyncId}/payees/{payeeId}/rules | List rules for payee |
| POST | /budgets/{budgetSyncId}/payees/merge | Merge payees |
| GET | /budgets/{budgetSyncId}/rules | List rules |
| POST | /budgets/{budgetSyncId}/rules | Create rule |
| GET | /budgets/{budgetSyncId}/rules/{ruleId} | Get rule |
| PATCH | /budgets/{budgetSyncId}/rules/{ruleId} | Update rule |
| DELETE | /budgets/{budgetSyncId}/rules/{ruleId} | Delete rule |
| GET | /budgets/{budgetSyncId}/schedules | List schedules |
| POST | /budgets/{budgetSyncId}/schedules | Create schedule |
| GET | /budgets/{budgetSyncId}/schedules/{scheduleId} | Get schedule |
| PATCH | /budgets/{budgetSyncId}/schedules/{scheduleId} | Update schedule |
| DELETE | /budgets/{budgetSyncId}/schedules/{scheduleId} | Delete schedule |
| GET | /budgets/{budgetSyncId}/tags | List tags |
| POST | /budgets/{budgetSyncId}/tags | Create tag |
| GET | /budgets/{budgetSyncId}/tags/{tagId} | Get tag |
| PATCH | /budgets/{budgetSyncId}/tags/{tagId} | Update tag |
| DELETE | /budgets/{budgetSyncId}/tags/{tagId} | Delete tag |
| GET | /budgets/{budgetSyncId}/notes/category/{categoryId} | Get notes for category |
| GET | /budgets/{budgetSyncId}/notes/account/{accountId} | Get notes for account |
| GET | /budgets/{budgetSyncId}/notes/budgetmonth/{budgetMonth} | Get notes for budget month |
| GET | /budgets/{budgetSyncId}/export | Export budget as zip |
| GET | /budgets/{budgetSyncId}/actualserverversion | Actual server version |
| POST | /budgets/{budgetSyncId}/run-query | Run arbitrary ActualQL query |

---

## Vikunja API — 126 paths

Auth: JWT Bearer token (obtain via `POST /api/v1/login`).

| Method | Path | Summary |
|--------|------|---------|
| POST | /login | Login, returns JWT |
| POST | /auth/openid/{provider}/callback | OpenID Connect auth |
| GET | /info | Instance info (version, settings) |
| GET | /projects | List all projects |
| PUT | /projects | Create project |
| GET | /projects/{id} | Get project |
| POST | /projects/{id} | Update project |
| DELETE | /projects/{id} | Delete project |
| GET | /projects/{id}/background | Get project background |
| DELETE | /projects/{id}/background | Remove project background |
| POST | /projects/{id}/backgrounds/unsplash | Set unsplash background |
| PUT | /projects/{id}/backgrounds/upload | Upload background |
| GET | /projects/{id}/projectusers | List project users |
| GET | /projects/{id}/shares | List project shares |
| PUT | /projects/{id}/tasks | Create task in project |
| GET | /projects/{id}/tasks | List tasks in project |
| GET | /tasks/{id} | Get task |
| POST | /tasks/{id} | Update task |
| DELETE | /tasks/{id} | Delete task |
| PUT | /tasks/{id}/assignees | Add task assignees |
| DELETE | /tasks/{id}/assignees/{userId} | Remove task assignee |
| POST | /tasks/{id}/labels | Add labels to task |
| DELETE | /tasks/{id}/labels/{labelId} | Remove label from task |
| GET | /labels | List all labels |
| PUT | /labels | Create label |
| GET | /labels/{id} | Get label |
| PUT | /labels/{id} | Update label |
| DELETE | /labels/{id} | Delete label |
| GET | /teams | List teams |
| PUT | /teams | Create team |
| POST | /teams/{id} | Update team |
| DELETE | /teams/{id} | Delete team |
| PUT | /filters | Create saved filter |
| GET | /filters/{id} | Get saved filter |
| POST | /filters/{id} | Update saved filter |
| DELETE | /filters/{id} | Delete saved filter |
| GET | /notifications | List notifications |
| POST | /notifications | Mark all notifications read |
| POST | /notifications/{id} | Mark notification read/unread |
| GET | /admin/overview | Instance stats (admin) |
| GET | /admin/projects | List all projects (admin) |
| PATCH | /admin/projects/{id}/owner | Reassign project owner (admin) |
| GET | /admin/users | List all users (admin) |
| POST | /admin/users | Create user (admin) |
| DELETE | /admin/users/{id} | Delete user (admin) |
| PATCH | /admin/users/{id}/admin | Toggle admin status |
| PATCH | /admin/users/{id}/status | Set user status |
| GET | /migration/csv/status | CSV migration status |
| PUT | /migration/csv/detect | Detect CSV structure |
| PUT | /migration/csv/preview | Preview CSV import |
| PUT | /migration/csv/migrate | Import from CSV |
| GET | /migration/todoist/auth | Todoist auth URL |
| POST | /migration/todoist/migrate | Import from Todoist |
| GET | /migration/todoist/status | Todoist migration status |
| GET | /migration/trello/auth | Trello auth URL |
| POST | /migration/trello/migrate | Import from Trello |
| GET | /migration/trello/status | Trello migration status |
| GET | /migration/microsoft-todo/auth | Microsoft Todo auth URL |
| POST | /migration/microsoft-todo/migrate | Import from Microsoft Todo |
| GET | /migration/microsoft-todo/status | Microsoft Todo migration status |
| PUT | /migration/ticktick/migrate | Import from TickTick |
| GET | /migration/ticktick/status | TickTick migration status |
| POST | /migration/vikunja-file/migrate | Import from Vikunja export |
| GET | /migration/vikunja-file/status | Vikunja file migration status |
| PUT | /migration/wekan/migrate | Import from WeKan |
| GET | /migration/wekan/status | WeKan migration status |
| GET | /backgrounds/unsplash/search | Search Unsplash backgrounds |
| GET | /backgrounds/unsplash/image/{image} | Get Unsplash image |
| GET | /backgrounds/unsplash/image/{image}/thumb | Get Unsplash thumbnail |
