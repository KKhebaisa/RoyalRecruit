# 👑 RoyalRecruit

> Elite Discord recruitment management — tickets, applications, and customizable panels for your alliance.

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Dashboard Usage](#dashboard-usage)
- [Bot Commands](#bot-commands)
- [Development](#development)
- [Project Structure](#project-structure)

---

## Architecture

RoyalRecruit consists of **3 services** orchestrated with Docker Compose:

```
┌─────────────────┐     OAuth2      ┌─────────────────┐
│   Dashboard      │ ──────────────► │  Discord API     │
│  (Next.js :3000) │                 └─────────────────┘
└────────┬────────┘
         │ REST/JWT
         ▼
┌─────────────────┐     SQL         ┌─────────────────┐
│   Backend API    │ ──────────────► │   PostgreSQL     │
│  (FastAPI :8000) │                 └─────────────────┘
└────────▲────────┘
         │ REST/APIKey
┌────────┴────────┐
│   Discord Bot    │
│   (discord.py)   │
└─────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| **Ticket System** | Customizable ticket types with auto-named channels, serial numbers, staff access |
| **Application System** | Sequential Q&A flows, automated channel creation, staff review |
| **Panel System** | Deploy embed + button panels to any Discord channel |
| **Multi-server** | Manage multiple Discord servers from one dashboard |
| **Discord OAuth** | Secure login — only servers where you're admin are shown |
| **Audit Logs** | All events logged to database and configurable log channel |
| **Slash Commands** | `/close`, `/lock`, `/adduser`, `/removeuser`, `/transcript`, `/approve`, `/reject` |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- A Discord Application ([create one](https://discord.com/developers/applications))

### 1. Create a Discord Application

1. Go to https://discord.com/developers/applications
2. Create a **New Application**
3. Under **OAuth2 → General**, add redirect URL: `http://localhost:3000/api/auth/callback`
4. Under **Bot**, enable these **Privileged Gateway Intents**:
   - Server Members Intent
   - Message Content Intent
5. Copy the **Client ID**, **Client Secret**, and **Bot Token**

### 2. Configure Environment

```bash
git clone <this-repo>
cd royalrecruit
cp .env.example .env
```

Edit `.env` with your values:

```env
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_REDIRECT_URI=http://localhost:3000/api/auth/callback
POSTGRES_PASSWORD=your_db_password
JWT_SECRET_KEY=your_32char_random_string
API_SECRET_KEY=your_32char_random_string
```

### 3. Launch

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 4. Invite the Bot

Use this URL (replace `CLIENT_ID`):

```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=268438544&scope=bot%20applications.commands
```

Required permissions:
- Manage Channels
- Manage Roles
- Send Messages
- Read Message History
- Use Slash Commands

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DISCORD_CLIENT_ID` | Discord OAuth2 client ID | ✅ |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 client secret | ✅ |
| `DISCORD_BOT_TOKEN` | Discord bot token | ✅ |
| `DISCORD_REDIRECT_URI` | OAuth2 redirect URI | ✅ |
| `POSTGRES_PASSWORD` | PostgreSQL password | ✅ |
| `JWT_SECRET_KEY` | JWT signing secret (32+ chars) | ✅ |
| `API_SECRET_KEY` | Internal bot↔API secret | ✅ |

---

## Dashboard Usage

### 1. Login
Go to `http://localhost:3000` and click **Login with Discord**.

### 2. Select Server
You'll see all servers where you have **Administrator** permission.

### 3. Configure Ticket Types
- Navigate to **Tickets** → **New Type**
- Fill in: name, description, category channel ID, staff role ID, welcome message

### 4. Configure Application Types
- Navigate to **Applications** → **New Application**
- Add custom questions in any order

### 5. Create Panels
- Navigate to **Panels** → **New Panel**
- Select ticket or application types to include as buttons
- Note the Panel ID

### 6. Deploy Panel in Discord
In the Discord channel where you want the panel:
```
/sendpanel 1
```
(Replace `1` with your Panel ID)

---

## Bot Commands

### General
| Command | Description |
|---|---|
| `/sendpanel <id>` | Deploy a panel embed + buttons to current channel |
| `/listpanels` | List all configured panels |

### Ticket Commands (inside ticket channels)
| Command | Description |
|---|---|
| `/close` | Close the ticket (prompts confirmation) |
| `/lock` | Lock the channel (read-only) |
| `/adduser <@user>` | Add a user to the ticket |
| `/removeuser <@user>` | Remove a user from the ticket |
| `/transcript` | Generate a text transcript |

### Application Commands
| Command | Description |
|---|---|
| `/approve <id>` | Approve an application by ID |
| `/reject <id>` | Reject an application by ID |

---

## Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Bot

```bash
cd bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

---

## Project Structure

```
royalrecruit/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via pydantic-settings
│   ├── auth/
│   │   └── security.py      # JWT + Discord OAuth helpers
│   ├── database/
│   │   └── connection.py    # Async SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py        # All ORM models
│   └── routers/
│       ├── auth.py          # OAuth callback, /me, /guilds
│       ├── guilds.py        # Server upsert/settings
│       ├── tickets.py       # Ticket types + ticket instances
│       ├── applications.py  # Application types + instances
│       ├── panels.py        # Panel CRUD
│       └── logs.py          # Audit logs
│
├── bot/
│   ├── bot.py               # Bot entry point
│   ├── config/settings.py   # Bot config from env
│   ├── services/
│   │   └── api_client.py    # HTTP client for backend API
│   └── cogs/
│       ├── events.py        # Guild join/sync
│       ├── tickets.py       # Ticket buttons + slash commands
│       ├── applications.py  # Q&A flow + review
│       └── panels.py        # /sendpanel command
│
├── dashboard/
│   ├── pages/
│   │   ├── index.tsx        # Landing page
│   │   ├── servers.tsx      # Server selection
│   │   ├── api/auth/
│   │   │   └── callback.ts  # OAuth callback handler
│   │   └── dashboard/[guildId]/
│   │       ├── index.tsx    # Overview
│   │       ├── tickets.tsx  # Ticket type CRUD + list
│   │       ├── applications.tsx # App type CRUD + list
│   │       ├── panels.tsx   # Panel builder
│   │       └── settings.tsx # Guild settings
│   ├── components/dashboard/
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   ├── lib/
│   │   ├── api.ts           # Axios API client
│   │   └── store.ts         # Zustand auth store
│   └── styles/globals.css
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Security Notes

- All dashboard routes require a valid JWT (Discord OAuth)
- Bot→API communication uses a shared `API_SECRET_KEY`
- Users only see servers where they have the `ADMINISTRATOR` Discord permission
- Ticket channels are permission-locked to the opener + staff role
- Rate limiting should be added via a reverse proxy (nginx/Caddy) in production
- Rotate `JWT_SECRET_KEY` and `API_SECRET_KEY` in production
