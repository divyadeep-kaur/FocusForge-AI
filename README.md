# FocusForge AI

FocusForge AI is a Flask and SQLite productivity app for students and professionals. It combines Pomodoro focus sessions, task planning, streaks, XP rewards, levels, a leaderboard, and a simple AI-style productivity coach.

## Features

- Session-based signup, login, and logout
- SQLite persistence for users, tasks, streaks, rewards, and friends
- Pomodoro timer with preset durations, custom duration, pause, reset, and fullscreen modal
- Notion-style task planner with dates and completion tracking
- XP and level system: Bronze, Silver, Gold, Sapphire
- Reward unlocks based on XP milestones
- Daily activity heatmap and streak stats
- Local AI coach chat endpoint for study planning and motivation
- Responsive dark glassmorphism UI

## Run Locally

```bash
cd FocusForge-AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 create_db.py
python3 app.py
```

Open `http://127.0.0.1:5000`.

## Project Structure

```text
FocusForge-AI/
  app.py
  create_db.py
  database.db
  models/database.py
  templates/
  static/css/style.css
  static/js/
```
