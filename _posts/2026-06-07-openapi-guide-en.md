---
layout: post
title: "What is OpenAPI? — Making API Specs Readable by Humans and Machines Alike"
subtitle: From its relationship with Swagger to writing YAML, code generation, and Postman integration
categories: Development
tags: ["OpenAPI", "Swagger", "API", "REST", "Backend", "Documentation"]
lang: en
ref: openapi-guide
---

Anyone who has worked on API development has run into these situations:

- "The parameter name doesn't match" or "the response shape changed" keeps happening between frontend and backend
- Manually keeping Postman collections up to date is exhausting
- API specs were written in a doc, but have drifted from the actual code
- You want to expose an API to another team or external partners

These are fundamentally the same problem: **there's no single place where the API spec lives**.

OpenAPI is the mechanism for creating that single place.

---

## The Short Answer

OpenAPI is a **standard format for describing REST APIs in YAML or JSON**.

```yaml
# Minimal openapi.yaml example
openapi: "3.1.0"
info:
  title: My API
  version: "1.0.0"
paths:
  /users/{id}:
    get:
      summary: Retrieve a single user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Success
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

From this single YAML file, you can automatically:

- Generate **Swagger UI** — a browser-based interactive API explorer
- Generate **client code** for TypeScript, Python, Go, and more
- Import into **Postman** or **Insomnia** and immediately test endpoints
- **Validate** that requests and responses conform to the schema

---

## OpenAPI vs. Swagger: What's the Difference?

These are often confused. Here's the breakdown:

| Name | What it is |
| :--- | :--- |
| **Swagger** | The original API spec format, developed by SmartBear |
| **OpenAPI** | The official name after Swagger 2.0 was donated to the Linux Foundation |
| **Swagger UI / Editor** | Tools for visualizing and editing OpenAPI files (still use the "Swagger" name) |

In short, "Swagger spec" and "OpenAPI spec" are nearly synonymous, but the official name is **OpenAPI**. The tooling called "Swagger" still exists separately.

The current version is **OpenAPI 3.1** (released 2021). Older codebases may still use 2.0.

---

## Why OpenAPI Matters

### The Problem: Docs and Code Live Separate Lives

"The API docs are in Confluence but haven't been updated in six months."
"The frontend hit the endpoint and the response key names were wrong."

This is common. The root cause: every time the code changes, someone has to manually update the docs too.

### The Fix: Manage the Spec File in the Same Repo as the Code

Putting the OpenAPI file in version control changes things:

- Code changes and spec changes land in the same PR
- CI can automatically verify that the spec matches the implementation
- Client code is generated directly from the spec — no hand-written type definitions

---

## Understanding the Structure of an OpenAPI File

An OpenAPI file has four main sections.

### 1. Metadata (`info`)

```yaml
openapi: "3.1.0"
info:
  title: Logging API
  description: API for an AI-native log management service
  version: "2.0.0"
  contact:
    email: support@example.com
```

### 2. Endpoint Definitions (`paths`)

```yaml
paths:
  /logs:
    get:
      operationId: listLogs
      summary: Retrieve a list of logs
      tags: [logs]
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        "200":
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Log"
    post:
      operationId: createLog
      summary: Record a log entry
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateLogInput"
      responses:
        "201":
          description: Created
```

### 3. Schema Definitions (`components/schemas`)

Type definitions go here and are referenced via `$ref` — the mechanism for avoiding repetition.

```yaml
components:
  schemas:
    Log:
      type: object
      required: [id, message, level, createdAt]
      properties:
        id:
          type: string
          format: uuid
        message:
          type: string
        level:
          type: string
          enum: [debug, info, warn, error]
        createdAt:
          type: string
          format: date-time

    CreateLogInput:
      type: object
      required: [message, level]
      properties:
        message:
          type: string
        level:
          type: string
          enum: [debug, info, warn, error]
```

### 4. Auth Definitions (`components/securitySchemes`)

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

---

## How to Actually Use It

### Pattern 1: Design-First (write the spec first)

1. Write `openapi.yaml` first
2. Generate client SDKs and server stubs from it
3. Build the server implementation

This works well in team settings where frontend and backend are developed simultaneously — the frontend can start coding before the backend is finished.

### Pattern 2: Code-First (generate from code)

1. Annotate your backend code with OpenAPI information
2. Auto-generate `openapi.yaml` at build time

**FastAPI** (Python) supports this out of the box.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{id}", response_model=User)
def get_user(id: int):
    return {"id": id, "name": "Kaito", "email": "kaito@example.com"}
```

Start the server and Swagger UI is automatically available at `/docs`. The raw spec is at `/openapi.json`.

---

## Common Tools

| Tool | Purpose |
| :--- | :--- |
| **Swagger Editor** | Edit YAML in the browser with a live preview |
| **Swagger UI** | Generate HTML documentation from an OpenAPI file |
| **Redoc** | Cleaner-looking alternative to Swagger UI for docs |
| **openapi-generator** | Generate client/server code for 50+ languages |
| **Prism** | Spin up a mock server instantly from an OpenAPI file |
| **Stoplight Studio** | GUI editor for designing OpenAPI specs visually |

### Generating a client with openapi-generator

```bash
# Generate a TypeScript/axios client
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o src/generated/api
```

Generated code includes full type information, which greatly reduces type mismatch errors on the frontend.

---

## Using OpenAPI in CI

You can automatically validate the OpenAPI spec in GitHub Actions.

```yaml
# .github/workflows/openapi-lint.yml
name: OpenAPI Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate OpenAPI spec
        uses: openapi-generators/openapitools-generator-action@v1
        with:
          generator: openapi
          openapi-file: openapi.yaml
          command-args: validate
```

**Spectral** (by Stoplight) lets you define and enforce your own team rules — naming conventions, required fields, and more — as a lint step.

---

## Summary

OpenAPI is a standard format for managing API specs in YAML, in one place.

- **Docs are auto-generated** — no more hand-writing in Confluence
- **Client code is auto-generated** — no more type mismatches
- **Mock servers can be spun up instantly** — frontend development doesn't block on the backend
- **CI validation** — spec drift is caught early

If you're using **FastAPI**, the OpenAPI document is generated automatically just by writing code — the onboarding cost is basically zero. The fastest way to experience OpenAPI in practice is to spin up a FastAPI server and visit `/docs`.
