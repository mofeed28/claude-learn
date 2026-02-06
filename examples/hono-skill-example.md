<!--
  This is an example of what /learn hono would generate.
  Actual output depends on what docs are available at the time of generation.
-->

---
name: hono
description: Hono web framework for Cloudflare Workers, Deno, Bun, and Node.js. Use when building APIs, routing HTTP requests, handling middleware, or deploying edge-first web applications with Hono.
---

# Hono Skill

## When to Use This Skill

Use this skill when the user needs to:
- Create a new Hono web application
- Define routes and handle HTTP methods
- Add middleware (CORS, auth, logging)
- Deploy to Cloudflare Workers, Deno, Bun, or Node.js
- Handle request/response objects in Hono
- Validate request data with Hono's validator
- Serve static files or build APIs
- Use Hono's JSX/HTML helpers

## Overview

Hono is an ultrafast, lightweight web framework that runs on any JavaScript runtime — Cloudflare Workers, Deno, Bun, Fastly, AWS Lambda, and Node.js. It has zero dependencies, first-class TypeScript support, and a familiar Express-like API.

**Key links:**
- Docs: https://hono.dev
- GitHub: https://github.com/honojs/hono
- Package: https://www.npmjs.com/package/hono

## Quick Reference

| Method | Example |
|--------|---------|
| GET | `app.get('/users', (c) => c.json(users))` |
| POST | `app.post('/users', async (c) => { const body = await c.req.json(); ... })` |
| PUT | `app.put('/users/:id', (c) => ...)` |
| DELETE | `app.delete('/users/:id', (c) => ...)` |
| Middleware | `app.use('/*', cors())` |
| Group | `const api = app.route('/api')` |
| Static | `app.use('/static/*', serveStatic({ root: './' }))` |

## Installation & Setup

```bash
# Create new project
npm create hono@latest my-app

# Or add to existing project
npm install hono
```

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Hono!'))

export default app
```

## Core Concepts

- **Context (`c`)** — every handler receives a Context object with `c.req`, `c.res`, `c.json()`, `c.text()`, `c.html()`
- **Routing** — Express-style with path params (`:id`), wildcards (`*`), and regex
- **Middleware** — `app.use()` with built-in CORS, Bearer Auth, Logger, ETag, etc.
- **Multi-runtime** — same code runs on Workers, Deno, Bun, Node with adapter imports

## API Reference

### Routing

| Pattern | Example | Description |
|---------|---------|-------------|
| Static | `/about` | Exact match |
| Param | `/users/:id` | `c.req.param('id')` |
| Optional | `/users/:id?` | Optional param |
| Wildcard | `/files/*` | Match anything after |
| Regex | `/post/:date{[0-9]+}` | With validation |

**Example:**
```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/users/:id', (c) => {
  const id = c.req.param('id')
  return c.json({ id })
})

app.get('/posts/:slug', (c) => {
  const slug = c.req.param('slug')
  return c.json({ slug })
})
```

### Context Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `c.req.json()` | `Promise<any>` | Parse JSON body |
| `c.req.param('name')` | `string` | Get path parameter |
| `c.req.query('key')` | `string` | Get query parameter |
| `c.req.header('name')` | `string` | Get request header |
| `c.json(data, status?)` | `Response` | Return JSON |
| `c.text(str, status?)` | `Response` | Return plain text |
| `c.html(str)` | `Response` | Return HTML |
| `c.redirect(url, status?)` | `Response` | Redirect |
| `c.set('key', value)` | `void` | Set context variable |
| `c.get('key')` | `any` | Get context variable |

## Common Patterns

### REST API with CRUD
```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

app.use('/*', cors())

let users = [{ id: 1, name: 'Alice' }]

app.get('/users', (c) => c.json(users))

app.get('/users/:id', (c) => {
  const user = users.find(u => u.id === Number(c.req.param('id')))
  return user ? c.json(user) : c.json({ error: 'Not found' }, 404)
})

app.post('/users', async (c) => {
  const body = await c.req.json()
  const user = { id: users.length + 1, ...body }
  users.push(user)
  return c.json(user, 201)
})

app.delete('/users/:id', (c) => {
  users = users.filter(u => u.id !== Number(c.req.param('id')))
  return c.json({ ok: true })
})

export default app
```

## Important Rules

1. **Always `export default app`** — required for Cloudflare Workers and Bun
2. **`c.req.json()` is async** — always `await` it
3. **Middleware order matters** — `app.use()` must come before the routes it applies to
4. **Path params are strings** — cast to `Number()` when needed for IDs
