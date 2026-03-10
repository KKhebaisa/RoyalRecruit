# RoyalRecruit

RoyalRecruit is a production-ready SaaS platform for Discord server administration. It combines a Discord bot, a FastAPI backend, and a Next.js dashboard to provide customizable ticket systems, application systems, and panel deployment.

## Architecture

- **dashboard** (Next.js + Tailwind): OAuth login, multi-server admin UI.
- **backend** (FastAPI + SQLAlchemy): Auth, server config, ticket/app/panel APIs, logging.
- **bot** (discord.py): Slash commands, ticket/application runtime behavior, Discord panel interactions.
- **postgres**: Persistent relational storage.

Flow:

1. Dashboard authenticates admins via Discord OAuth2 (`identify`, `guilds`).
2. Dashboard calls backend APIs to configure systems.
3. Bot reads configuration from backend and executes Discord workflows.
4. Backend persists state and audit logs in PostgreSQL.

## Features Implemented

- Discord OAuth callback and JWT issue.
- Multi-server persistence with per-server ticket serial counters.
- Ticket config + ticket open/close status API.
- Application types with customizable question sequences.
- Panel creation API and panel dispatch command in bot.
- Staff slash commands (`/close`, `/lock`, `/adduser`, `/removeuser`, `/transcript`, `/approve`, `/reject`).
- Logging endpoint for ticket/application events.
- In-memory rate limit middleware and CORS controls.
- Dockerized services with environment-based configuration.

## Project Structure

```
royalrecruit/
  backend/
  bot/
  dashboard/
  shared/
  docker/
```

## Quick Start

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill Discord and bot credentials.
3. Start all services:
   ```bash
   docker compose up --build
   ```
4. Open dashboard at `http://localhost:3000`.

## Required Discord Scopes and Permissions

### OAuth Scopes
- `identify`
- `guilds`

### Bot Permissions
- Manage Channels
- Send Messages
- Manage Roles
- Read Message History

Invite URL template:

```
https://discord.com/api/oauth2/authorize?client_id=<BOT_CLIENT_ID>&permissions=268446800&scope=bot%20applications.commands
```

## API Surface (High Level)

- `POST /auth/discord/callback`
- `POST /servers/sync`
- `GET /servers`
- `POST /tickets/config/{discord_server_id}`
- `GET /tickets/config/{discord_server_id}`
- `POST /tickets`
- `POST /applications/types/{discord_server_id}`
- `GET /applications/types/{discord_server_id}`
- `POST /applications/submit`
- `POST /panels/{discord_server_id}`
- `GET /panels/{discord_server_id}`
- `POST /logs`

## Security Notes

- JWT-based dashboard session token minting.
- Guild and server existence checks for mutable operations.
- Rate limiting middleware (IP-based window limiter).
- Environment variable based secret handling.

## Production Recommendations

- Replace `create_all` bootstrapping with Alembic migrations.
- Move rate limiting to Redis-backed strategy.
- Add robust RBAC by validating Discord guild admin permissions on each API call.
- Store encrypted transcripts in object storage.
- Add worker queue for expensive Discord tasks.
