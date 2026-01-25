# Pixel Perfect Admin - API Documentation

## Overview

This document lists the API endpoints that are currently implemented in the FastAPI service. Endpoints are grouped by router and include their request/response shapes as returned by the API.

### Base URL
```
http://localhost:8000
```

### Authentication
Protected endpoints require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

---

## Table of Contents

1. [Health & Public](#1-health--public)
2. [Authentication](#2-authentication)
3. [Magic Link Sign-in](#3-magic-link-sign-in)
4. [Current User](#4-current-user)
5. [Team Members](#5-team-members)
6. [Notifications](#6-notifications)

---

## 1. Health & Public

### GET /ping
Simple health check for the API.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

### GET /public/ping
Public ping endpoint.

**Response (200 OK):**
```json
{
  "message": "pong"
}
```

---

### GET /
Root endpoint returning a welcome message.

**Response (200 OK):**
```json
{
  "message": "Welcome to <app_name>"
}
```

---

## 2. Authentication

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "super-secure-password"
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "is_active": true
}
```

---

### POST /auth/token
Authenticate a user and return a JWT access token.

**Request (form data):**
```
username=user@example.com
password=super-secure-password
```

**Response (200 OK):**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "is_active": true
  }
}
```

---

## 3. Magic Link Sign-in

### POST /v1.0/signin
Send a magic link for passwordless sign-in.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (201 Created):**
```json
{
  "token": "<magic_token>",
  "expires_at": "2024-02-01T12:00:00Z"
}
```

---

### POST /v1.0/signin/confirm
Confirm a magic link and return a JWT access token.

**Request:**
```json
{
  "email": "user@example.com",
  "token": "<magic_token>"
}
```

**Response (200 OK):**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "First",
    "team_member_status": "accepted"
  }
}
```

---

## 4. Current User

### GET /protected/me
Return the authenticated user from the auth dependency.

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "is_active": true
}
```

---

### GET /v1.0/users/me
Get the current user's profile details.

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "default_account_id": "account_uuid"
}
```

---

### PATCH /v1.0/users/me
Update the current user's profile.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Doe"
}
```

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "default_account_id": "account_uuid"
}
```

---

## 5. Team Members

### POST /v1.0/team_members/invite
Invite a user to the current user's default account.

**Request:**
```json
{
  "email": "invitee@example.com",
  "role": "admin"
}
```

**Response (201 Created):**
```json
{
  "message": "Invitation sent successfully",
  "email": "invitee@example.com",
  "user_exists": true,
  "status": "invited"
}
```

---

### GET /v1.0/team_members
List team members for the default account.

**Query Parameters:**
- `statuses` (optional, repeatable): `invited`, `accepted`, `rejected`
- `limit` (optional): max 100, default 20
- `cursor` (optional): pagination cursor

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "member_uuid",
      "role": "admin",
      "user_id": "user_uuid",
      "status": "accepted",
      "name": "Jane Doe",
      "first_name": "Jane",
      "last_name": "Doe",
      "joined_at": "2024-02-01T12:00:00Z"
    }
  ],
  "next_cursor": "cursor_token"
}
```

---

### GET /v1.0/team_members/{member_id}
Get a specific team member by ID.

**Response (200 OK):**
```json
{
  "id": "member_uuid",
  "role": "admin",
  "user_id": "user_uuid",
  "status": "accepted",
  "name": "Jane Doe",
  "first_name": "Jane",
  "last_name": "Doe",
  "joined_at": "2024-02-01T12:00:00Z"
}
```

---

### PATCH /v1.0/team_members/{member_id}
Update a team member's role or status.

**Request:**
```json
{
  "role": "guest",
  "status": "accepted"
}
```

**Response (200 OK):**
```json
{
  "message": "Team member updated successfully",
  "id": "member_uuid",
  "role": "guest",
  "status": "accepted"
}
```

---

### DELETE /v1.0/team_members/{member_id}
Soft delete a team member.

**Response (200 OK):**
```json
{
  "message": "Team member removed successfully",
  "id": "member_uuid"
}
```

---

## 6. Notifications

### GET /v1.0/notifications
List notifications for the current user.

**Query Parameters:**
- `is_read` (optional): filter by read status
- `limit` (optional): max 100, default 20
- `cursor` (optional): pagination cursor

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "notification_uuid",
      "user_id": "user_uuid",
      "subject": "Welcome",
      "body": "Thanks for joining...",
      "type": "welcome",
      "details": "Thanks for joining...",
      "cta": null,
      "is_read": false,
      "read_at": null,
      "created_at": "2024-02-01T12:00:00Z"
    }
  ],
  "next_cursor": "cursor_token"
}
```

---

### GET /v1.0/notifications/count
Return the total number of notifications for the current user.

**Query Parameters:**
- `is_read` (optional): filter by read status

**Response (200 OK):**
```json
{
  "count": 12
}
```

---

### GET /v1.0/notifications/{notification_id}
Fetch a single notification.

**Response (200 OK):**
```json
{
  "id": "notification_uuid",
  "user_id": "user_uuid",
  "subject": "Welcome",
  "body": "Thanks for joining...",
  "type": "welcome",
  "details": "Thanks for joining...",
  "cta": null,
  "is_read": false,
  "read_at": null,
  "created_at": "2024-02-01T12:00:00Z"
}
```

---

### POST /v1.0/notifications/read
Mark all notifications as read.

**Response (200 OK):**
```json
[
  {
    "id": "notification_uuid",
    "user_id": "user_uuid",
    "subject": "Welcome",
    "body": "Thanks for joining...",
    "type": "welcome",
    "details": "Thanks for joining...",
    "cta": null,
    "is_read": true,
    "read_at": "2024-02-01T12:10:00Z",
    "created_at": "2024-02-01T12:00:00Z"
  }
]
```

---

### POST /v1.0/notifications/{notification_id}/read
Mark a single notification as read.

**Response (200 OK):**
```json
{
  "id": "notification_uuid",
  "user_id": "user_uuid",
  "subject": "Welcome",
  "body": "Thanks for joining...",
  "type": "welcome",
  "details": "Thanks for joining...",
  "cta": null,
  "is_read": true,
  "read_at": "2024-02-01T12:10:00Z",
  "created_at": "2024-02-01T12:00:00Z"
}
```
