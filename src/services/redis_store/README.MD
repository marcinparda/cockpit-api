# Redis Store Service

A generic key-value store backed by Redis (using RedisJSON). It provides a structured way to store arbitrary JSON data with metadata, organized by a three-part key hierarchy: `prefix`, `category`, and `key`.

## Key Structure

Every entry is stored in Redis under a compound key:

```
{prefix}:{category}:{key}
```

- **prefix** — identifies the tenant, environment, or override layer (e.g. `base`, `prod`, `user-123`)
- **category** — groups related entries (e.g. `settings`, `feature-flags`)
- **key** — the specific entry name (e.g. `theme`, `max-items`)

## Data Envelope

All responses wrap data in a `StoreEnvelope`:

```json
{
  "meta": {
    "key": "base:settings:theme",
    "type": "string",
    "version": 1,
    "created_at": "2026-03-22T10:00:00Z",
    "updated_at": "2026-03-22T10:00:00Z",
    "tags": []
  },
  "data": "dark"
}
```

The `version` field increments automatically on every write.

## Authentication & Permissions

All endpoints require the `REDIS_STORE` feature permission:

- `READ` — GET and resolve endpoints
- `UPDATE` — PUT and PATCH endpoints
- `DELETE` — DELETE endpoint

---

## Endpoints

Base path: `/api/v1/store`

---

### GET `/{prefix}/{category}/{key}` — Get a key

Retrieves a stored entry by its full key path.

**Example:**

```http
GET /api/v1/store/base/settings/theme
```

**Response `200 OK`:**

```json
{
  "meta": {
    "key": "base:settings:theme",
    "type": "string",
    "version": 1,
    "created_at": "2026-03-22T10:00:00Z",
    "updated_at": "2026-03-22T10:00:00Z",
    "tags": ["ui"]
  },
  "data": "dark"
}
```

Returns `404` if the key does not exist.

---

### GET `/{prefix}/{category}` — List keys

Returns a list of all Redis key names matching `{prefix}:{category}:*`.

**Example:**

```http
GET /api/v1/store/base/settings
```

**Response `200 OK`:**

```json
[
  "base:settings:theme",
  "base:settings:language",
  "base:settings:max-items"
]
```

---

### GET `/resolve/{prefix}/{category}/{key}` — Resolve a key with base fallback

The resolve endpoint implements a two-layer override system:

1. It always fetches the `base:{category}:{key}` entry as the foundation.
2. If `prefix` is not `"base"`, it also fetches `{prefix}:{category}:{key}` as an override layer.
3. The two are shallow-merged: if both `data` values are dicts, override keys win. Otherwise the override `data` fully replaces the base.

This is useful for per-tenant or per-environment configuration where you want sensible defaults from `base` that can be selectively overridden.

**Example — base has a dict, tenant overrides one field:**

```http
GET /api/v1/store/tenant-42/settings/limits
```

`base:settings:limits`:
```json
{ "max_items": 100, "max_size_mb": 10, "allow_export": false }
```

`tenant-42:settings:limits`:
```json
{ "max_items": 500 }
```

**Response `200 OK`** (merged result):
```json
{
  "meta": { "key": "base:settings:limits", ... },
  "data": { "max_items": 500, "max_size_mb": 10, "allow_export": false }
}
```

Returns `404` if the `base` entry does not exist.

---

### PUT `/{prefix}/{category}/{key}` — Create or replace a key

Creates the entry if it does not exist, or fully replaces it if it does. The `version` is incremented and `created_at` is preserved on updates.

**Request body:**

```json
{
  "type": "string",
  "tags": ["ui"],
  "data": "dark"
}
```

| Field  | Required | Description                                   |
|--------|----------|-----------------------------------------------|
| `type` | yes      | A label describing the data type (free-form)  |
| `tags` | no       | Optional list of string tags                  |
| `data` | yes      | Any JSON value (object, array, string, etc.)  |

**Example:**

```http
PUT /api/v1/store/base/settings/theme

{
  "type": "string",
  "tags": ["ui"],
  "data": "dark"
}
```

**Response `200 OK`:**

```json
{
  "meta": {
    "key": "base:settings:theme",
    "type": "string",
    "version": 1,
    "created_at": "2026-03-22T10:00:00Z",
    "updated_at": "2026-03-22T10:00:00Z",
    "tags": ["ui"]
  },
  "data": "dark"
}
```

---

### PATCH `/{prefix}/{category}/{key}` — Partially update a key

Shallow-merges the provided `data` dict into the existing entry's `data`. Only works when the stored `data` is a JSON object — otherwise the patch `data` fully replaces the stored value.

**Request body:**

```json
{
  "data": { "allow_export": true }
}
```

**Example:**

```http
PATCH /api/v1/store/base/settings/limits

{
  "data": { "allow_export": true }
}
```

Assuming existing data is `{ "max_items": 100, "allow_export": false }`:

**Response `200 OK`:**

```json
{
  "meta": {
    "key": "base:settings:limits",
    "type": "object",
    "version": 2,
    "created_at": "2026-03-22T10:00:00Z",
    "updated_at": "2026-03-22T10:05:00Z",
    "tags": []
  },
  "data": { "max_items": 100, "allow_export": true }
}
```

Returns `404` if the key does not exist.

---

### DELETE `/{prefix}/{category}/{key}` — Delete a key

Deletes the entry. Returns `204 No Content` on success.

**Example:**

```http
DELETE /api/v1/store/base/settings/theme
```

**Response `204 No Content`**

Returns `404` if the key does not exist.
