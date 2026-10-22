# API Contract — Login

## Endpoint
`POST /api/login`

## Purpose
Authenticate a user and return a JWT token.

## Request Body (JSON)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| password | string | Yes | User's plain password |

**Example:**
```json
{
  "email": "student@cst.edu.bt",
  "password": "password123"
}
