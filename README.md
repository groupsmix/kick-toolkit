# KickTools - Streamer Toolkit for Kick.com

A full-stack dashboard for Kick streamers with chat bot management, AI moderation, giveaway tools, tournament organization, and more.

## Features

- **Dashboard** — Real-time stats overview with quick actions
- **Chat Bot & AI Moderation** — Custom commands, auto-mod rules, AI-powered toxicity detection
- **Chat Logs** — Searchable, filterable chat history with user profiles and top chatters
- **Giveaway Roller** — Create giveaways with keyword entry, animated winner rolling, reroll support
- **Anti-Alt Detection (Premium)** — AI-powered alt account detection with risk scoring and auto-actions
- **Tournament Organizer** — Keyword-based registration, auto-bracket generation, match management
- **Stream Giveaway Ideas** — Categorized idea generator with save/bookmark functionality

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI (Python)
- **API:** Kick API (OAuth 2.1)

## Getting Started

### Backend

```bash
cd kick-backend
poetry install
poetry run fastapi dev app/main.py
```

Backend runs on http://localhost:8000

### Frontend

```bash
cd kick-frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

## Project Structure

```
kick-toolkit/
├── kick-backend/          # FastAPI backend
│   └── app/
│       ├── main.py        # App entry point & dashboard stats
│       ├── models/        # Pydantic schemas
│       ├── routers/       # API route handlers
│       │   ├── bot.py     # Bot commands & moderation
│       │   ├── chatlogs.py
│       │   ├── giveaway.py
│       │   ├── antialt.py
│       │   ├── tournament.py
│       │   └── ideas.py
│       └── services/      # Database & business logic
│           └── database.py
├── kick-frontend/         # React frontend
│   └── src/
│       ├── components/    # Layout & UI components
│       ├── pages/         # Feature pages
│       └── hooks/         # API hooks
└── README.md
```

## License

MIT
