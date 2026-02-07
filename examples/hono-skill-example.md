<!--
  This is an example of what /learn hono would generate.
  Actual output depends on what docs are available at the time of generation.
-->

---
name: hono
description: Hono ultrafast web framework for Cloudflare Workers, Deno, Bun, and Node.js. Use when building APIs, defining routes, handling HTTP requests, adding middleware like CORS or auth, validating input, serving static files, rendering JSX, or deploying edge-first web applications.
version: "4.7.4"
generated: "2026-02-07"
language: typescript
type: framework
tags: [web-framework, api, cloudflare-workers, deno, bun, edge, middleware, routing]
---

# Hono Skill

## When to Use This Skill

Use this skill when the user needs to:
- Create a new Hono web application or API
- Define routes and handle HTTP methods (GET, POST, PUT, DELETE)
- Add middleware (CORS, auth, logging, rate limiting)
- Deploy to Cloudflare Workers, Deno, Bun, or Node.js
- Handle request/response objects with the Context API
- Validate request data with Hono's validator
- Serve static files
- Render HTML or JSX templates
- Group routes and compose sub-applications
- Handle errors globally with custom error handlers

## Overview

Hono is an ultrafast, lightweight web framework that runs on any JavaScript runtime — Cloudflare Workers, Deno, Bun, Fastly, AWS Lambda, and Node.js. It has zero dependencies, first-class TypeScript support, and a familiar Express-like API with significantly better performance.

**Key links:**
- Docs: https://hono.dev
- GitHub: https://github.com/honojs/hono
- Package: https://www.npmjs.com/package/hono

## Prerequisites

- Runtime: Node.js >= 18, Deno >= 1.28, Bun >= 0.3, or Cloudflare Workers
- No peer dependencies
- Related skills: `cloudflare-workers`, `drizzle-orm` (for DB layer)

## Quick Reference

| Method | Example | Description |
|--------|---------|-------------|
| GET | `app.get('/users', (c) => c.json(users))` | Handle GET requests |
| POST | `app.post('/users', async (c) => { const body = await c.req.json(); ... })` | Handle POST with body |
| PUT | `app.put('/users/:id', (c) => ...)` | Handle PUT (update) |
| DELETE | `app.delete('/users/:id', (c) => ...)` | Handle DELETE |
| ALL | `app.all('/api/*', handler)` | Match all HTTP methods |
| Middleware | `app.use('/*', cors())` | Apply middleware globally |
| Group | `const api = app.route('/api')` | Group routes under prefix |
| Static | `app.use('/static/*', serveStatic({ root: './' }))` | Serve static files |
| Websocket | `app.get('/ws', upgradeWebSocket(handler))` | Upgrade to WebSocket |

## Installation & Setup

```bash
# Create new project (interactive — picks runtime adapter)
npm create hono@latest my-app

# Or add to existing project
npm install hono
```

**Minimal app:**
```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Hono!'))

export default app
```

**With specific runtime adapter (Node.js):**
```typescript
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()
app.get('/', (c) => c.text('Hello Hono!'))

serve({ fetch: app.fetch, port: 3000 })
```

## Core Concepts

- **Context (`c`)** — every handler receives a Context object. Use `c.req` for the request and `c.json()`, `c.text()`, `c.html()` to send responses. Never use raw `new Response()` unless you need to.
- **Routing** — Express-style with path params (`:id`), optional params (`:id?`), wildcards (`*`), and regex constraints. Routes are matched in registration order.
- **Middleware** — `app.use(path, ...middlewares)`. Middlewares run in order. Call `await next()` to pass control to the next handler. Built-in: CORS, Bearer Auth, JWT, Logger, ETag, Compress, and more.
- **Multi-runtime** — same code runs everywhere. Import from `hono` for the core. Import adapters like `@hono/node-server` or `hono/cloudflare-workers` for runtime-specific features.
- **Type safety** — routes, params, query strings, and request bodies are fully typed. Use `app.get<{...}>()` or Zod validation for end-to-end type safety.

## API Reference

### Routing

| Pattern | Example | Description |
|---------|---------|-------------|
| Static | `/about` | Exact match |
| Param | `/users/:id` | `c.req.param('id')` — always a string |
| Optional | `/users/:id?` | Optional param |
| Wildcard | `/files/*` | Match anything after prefix |
| Regex | `/post/:date{[0-9]+}` | Param with validation pattern |
| Chained | `/api/v1/users/:id/posts/:postId` | Multiple params |

**Returns:** `Hono` instance (chainable)

**Example:**
```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/users/:id', (c) => {
  const id = c.req.param('id')
  return c.json({ id })
})

// Multiple params
app.get('/orgs/:orgId/members/:memberId', (c) => {
  const { orgId, memberId } = c.req.param()
  return c.json({ orgId, memberId })
})
```

**Gotcha:** Path params are always strings. Cast with `Number()` for numeric IDs.

### Context Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `c.req.json()` | `Promise<T>` | Parse JSON body (async) |
| `c.req.text()` | `Promise<string>` | Parse body as text |
| `c.req.formData()` | `Promise<FormData>` | Parse multipart/form body |
| `c.req.param('name')` | `string` | Get single path parameter |
| `c.req.param()` | `Record<string, string>` | Get all path parameters |
| `c.req.query('key')` | `string \| undefined` | Get single query parameter |
| `c.req.queries('key')` | `string[]` | Get array query param (`?tag=a&tag=b`) |
| `c.req.header('name')` | `string \| undefined` | Get request header |
| `c.json(data, status?)` | `Response` | Return JSON response |
| `c.text(str, status?)` | `Response` | Return plain text |
| `c.html(str)` | `Response` | Return HTML |
| `c.redirect(url, status?)` | `Response` | Redirect (default 302) |
| `c.notFound()` | `Response` | Return 404 |
| `c.set('key', value)` | `void` | Set variable for downstream handlers |
| `c.get('key')` | `T` | Get variable set by upstream middleware |
| `c.var` | `object` | Access all context variables |

**Returns:** `Response` for response methods, various for request methods

**Example:**
```typescript
import { Hono } from 'hono'

const app = new Hono()

app.post('/users', async (c) => {
  const body = await c.req.json<{ name: string; email: string }>()
  const page = c.req.query('page')
  const authHeader = c.req.header('Authorization')

  return c.json({ created: true, name: body.name }, 201)
})
```

**Gotcha:** `c.req.json()` is async — always `await` it. Forgetting `await` is the #1 Hono mistake.

### Built-in Middleware

| Middleware | Import | Usage |
|-----------|--------|-------|
| CORS | `hono/cors` | `app.use('/*', cors())` |
| Bearer Auth | `hono/bearer-auth` | `app.use('/api/*', bearerAuth({ token: 'secret' }))` |
| JWT | `hono/jwt` | `app.use('/api/*', jwt({ secret: 'key' }))` |
| Logger | `hono/logger` | `app.use('/*', logger())` |
| ETag | `hono/etag` | `app.use('/*', etag())` |
| Compress | `hono/compress` | `app.use('/*', compress())` |
| Pretty JSON | `hono/pretty-json` | `app.use('/*', prettyJSON())` |
| Secure Headers | `hono/secure-headers` | `app.use('/*', secureHeaders())` |

**Example:**
```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { bearerAuth } from 'hono/bearer-auth'

const app = new Hono()

// Global middleware
app.use('/*', logger())
app.use('/*', cors({ origin: 'https://example.com' }))

// Route-specific middleware
app.use('/api/*', bearerAuth({ token: process.env.API_TOKEN ?? '' }))

app.get('/api/data', (c) => c.json({ secret: 'stuff' }))
```

**Gotcha:** Middleware order matters — `app.use()` must come BEFORE the routes it applies to.

## Common Patterns

### REST API with CRUD
```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'

interface User {
  id: number
  name: string
  email: string
}

const app = new Hono()
app.use('/*', cors())

let users: User[] = [{ id: 1, name: 'Alice', email: 'alice@example.com' }]
let nextId = 2

app.get('/users', (c) => c.json(users))

app.get('/users/:id', (c) => {
  const user = users.find((u) => u.id === Number(c.req.param('id')))
  if (!user) return c.json({ error: 'User not found' }, 404)
  return c.json(user)
})

app.post('/users', async (c) => {
  const body = await c.req.json<Omit<User, 'id'>>()
  const user: User = { id: nextId++, ...body }
  users.push(user)
  return c.json(user, 201)
})

app.put('/users/:id', async (c) => {
  const id = Number(c.req.param('id'))
  const body = await c.req.json<Partial<Omit<User, 'id'>>>()
  const index = users.findIndex((u) => u.id === id)
  if (index === -1) return c.json({ error: 'User not found' }, 404)
  users[index] = { ...users[index], ...body }
  return c.json(users[index])
})

app.delete('/users/:id', (c) => {
  const id = Number(c.req.param('id'))
  users = users.filter((u) => u.id !== id)
  return c.json({ ok: true })
})

export default app
```

### Grouped Routes with Shared Middleware
```typescript
import { Hono } from 'hono'
import { bearerAuth } from 'hono/bearer-auth'

const app = new Hono()

// Public routes
app.get('/health', (c) => c.json({ status: 'ok' }))

// Protected API group
const api = new Hono()
api.use('/*', bearerAuth({ token: process.env.API_TOKEN ?? '' }))
api.get('/me', (c) => c.json({ user: 'authenticated' }))
api.get('/settings', (c) => c.json({ theme: 'dark' }))

app.route('/api', api)

export default app
```

### Custom Middleware with Context Variables
```typescript
import { Hono } from 'hono'

type Env = {
  Variables: {
    requestId: string
    startTime: number
  }
}

const app = new Hono<Env>()

// Timing middleware
app.use('/*', async (c, next) => {
  c.set('requestId', crypto.randomUUID())
  c.set('startTime', Date.now())
  await next()
  const duration = Date.now() - c.get('startTime')
  c.header('X-Request-Id', c.get('requestId'))
  c.header('X-Response-Time', `${duration}ms`)
})

app.get('/', (c) => {
  return c.json({ requestId: c.get('requestId') })
})

export default app
```

### Input Validation with Zod
```typescript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).optional(),
})

app.post(
  '/users',
  zValidator('json', createUserSchema),
  (c) => {
    const user = c.req.valid('json') // fully typed: { name: string, email: string, age?: number }
    return c.json({ created: true, user }, 201)
  }
)

export default app
```

### Global Error Handler
```typescript
import { Hono } from 'hono'
import { HTTPException } from 'hono/http-exception'

const app = new Hono()

// Global error handler
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return c.json({ error: err.message }, err.status)
  }
  console.error('Unhandled error:', err)
  return c.json({ error: 'Internal Server Error' }, 500)
})

// Global 404 handler
app.notFound((c) => {
  return c.json({ error: 'Not Found', path: c.req.path }, 404)
})

// Throw typed HTTP errors
app.get('/admin', (c) => {
  throw new HTTPException(403, { message: 'Forbidden' })
})

export default app
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: c.req.json is not a function` | Using `c.req.json` without `await` or on GET request | Use `await c.req.json()` — it's async |
| `404 Not Found` on valid route | Middleware registered after route, or wrong HTTP method | Ensure `app.use()` comes before routes; check method matches |
| `TypeError: Cannot read property of undefined` | Accessing `c.req.param('x')` for non-existent param | Check route pattern has `:x` defined |
| CORS errors in browser | Missing CORS middleware or wrong origin | Add `cors({ origin: 'https://your-domain.com' })` before routes |
| `413 Payload Too Large` | Body exceeds runtime limit | Configure body size limit in runtime (not Hono-specific) |
| Empty response body | Returning `c.text()` or `c.json()` without data | Ensure response methods receive content: `c.json({ ok: true })` |
| `HTTPException` not caught | Missing `app.onError()` handler | Add global error handler (see Common Patterns above) |

## TypeScript Integration

Hono is fully typed. Key patterns:

```typescript
import { Hono } from 'hono'
import type { Context } from 'hono'

// Type context variables
type AppEnv = {
  Bindings: {
    DB: D1Database       // Cloudflare bindings
    KV: KVNamespace
  }
  Variables: {
    userId: string       // custom context vars
    isAdmin: boolean
  }
}

const app = new Hono<AppEnv>()

// c.env.DB and c.var.userId are now typed
app.get('/', (c) => {
  const db = c.env.DB         // typed as D1Database
  const userId = c.get('userId') // typed as string
  return c.json({ userId })
})

// Type request params
app.get('/users/:id', (c) => {
  const id = c.req.param('id') // typed as string
  return c.json({ id })
})
```

**Key types to know:**
| Type | Import | Purpose |
|------|--------|---------|
| `Hono<Env>` | `hono` | App instance with typed env |
| `Context<Env>` | `hono` | Handler context type |
| `Next` | `hono` | Middleware `next()` function type |
| `MiddlewareHandler` | `hono` | Middleware function signature |
| `HTTPException` | `hono/http-exception` | Typed HTTP errors |

## Testing

Use the built-in `app.request()` method — no HTTP server needed:

```typescript
import { describe, it, expect } from 'vitest'
import app from './index'

describe('API', () => {
  it('GET / returns hello', async () => {
    const res = await app.request('/')
    expect(res.status).toBe(200)
    expect(await res.text()).toBe('Hello Hono!')
  })

  it('POST /users creates a user', async () => {
    const res = await app.request('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Bob', email: 'bob@test.com' }),
    })
    expect(res.status).toBe(201)
    const data = await res.json()
    expect(data.name).toBe('Bob')
  })

  it('GET /users/:id returns 404 for missing user', async () => {
    const res = await app.request('/users/999')
    expect(res.status).toBe(404)
  })
})
```

**Gotcha:** `app.request()` does NOT start a server. It calls the fetch handler directly — fast and isolated.

## Important Rules

1. **Always `export default app`** — required for Cloudflare Workers, Bun, and Deno Deploy
2. **`c.req.json()` is async** — always `await` it. This is the single most common Hono bug.
3. **Middleware order matters** — `app.use()` must come BEFORE the routes it applies to. Middleware registered after a route won't run for that route.
4. **Path params are strings** — cast with `Number()` for numeric IDs, never assume they're numbers
5. **Use `HTTPException` for typed errors** — import from `hono/http-exception`. Don't throw raw Error objects.
6. **Route specificity** — more specific routes should come first. `/users/me` before `/users/:id`, otherwise `:id` catches "me"
7. **Don't use `new Response()` directly** — use `c.json()`, `c.text()`, `c.html()` instead. They handle content-type headers automatically.
8. **Middleware must call `await next()`** — forgetting this stops the chain and returns no response
