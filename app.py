from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import get_db_connection, init_db, level_for_xp


app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-this-secret-key-for-production"

XP_PER_TASK = 35


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if current_user() is None:
            session.clear()
            flash("Your session expired. Please log in again.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    if "user_id" not in session:
        return None
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return date.today()


def streak_stats(user_id):
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT activity_date, completed_count FROM streaks WHERE user_id = ? ORDER BY activity_date DESC",
            (user_id,),
        ).fetchall()

    active_days = {parse_date(row["activity_date"]): row["completed_count"] for row in rows}
    cursor = date.today()
    current = 0
    while active_days.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    best = 0
    run = 0
    previous = None
    for day in sorted(active_days):
        if active_days[day] <= 0:
            continue
        if previous and day == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        best = max(best, run)
        previous = day

    return current, best


def calendar_days(user_id, span=35):
    start = date.today() - timedelta(days=span - 1)
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT activity_date, completed_count FROM streaks WHERE user_id = ? AND activity_date >= ?",
            (user_id, start.isoformat()),
        ).fetchall()
    counts = {row["activity_date"]: row["completed_count"] for row in rows}
    return [
        {
            "date": (start + timedelta(days=offset)).isoformat(),
            "label": (start + timedelta(days=offset)).strftime("%d"),
            "count": counts.get((start + timedelta(days=offset)).isoformat(), 0),
            "today": start + timedelta(days=offset) == date.today(),
        }
        for offset in range(span)
    ]


def dashboard_context():
    user = current_user()
    with get_db_connection() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY completed ASC, due_date ASC, created_at DESC",
            (user["id"],),
        ).fetchall()
        today_tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND due_date = ? ORDER BY completed ASC, created_at DESC",
            (user["id"], date.today().isoformat()),
        ).fetchall()
        rewards = conn.execute("SELECT * FROM rewards ORDER BY xp_required ASC").fetchall()
        leaderboard = conn.execute(
            "SELECT username, xp, level FROM users ORDER BY xp DESC, username ASC LIMIT 8"
        ).fetchall()

    completed = sum(1 for task in tasks if task["completed"])
    current_streak, best_streak = streak_stats(user["id"])
    next_reward = next((reward for reward in rewards if reward["xp_required"] > user["xp"]), None)
    level_floor = {"Bronze": 0, "Silver": 250, "Gold": 500, "Sapphire": 1000}[user["level"]]
    level_ceiling = {"Bronze": 250, "Silver": 500, "Gold": 1000, "Sapphire": max(user["xp"], 1200)}[user["level"]]
    level_progress = 100 if user["level"] == "Sapphire" else int(((user["xp"] - level_floor) / (level_ceiling - level_floor)) * 100)

    return {
        "user": user,
        "tasks": tasks,
        "today_tasks": today_tasks,
        "rewards": rewards,
        "leaderboard": leaderboard,
        "completed": completed,
        "pending": len(tasks) - completed,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "calendar_days": calendar_days(user["id"]),
        "next_reward": next_reward,
        "level_progress": level_progress,
    }


@app.route("/")
def index():
    if "user_id" in session and current_user() is not None:
        return redirect(url_for("dashboard"))
    if "user_id" in session:
        session.clear()
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6 or "@" not in email:
            flash("Use a valid email, 3+ character username, and 6+ character password.")
            return render_template("signup.html")

        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password, method="pbkdf2:sha256")),
                )
                conn.commit()
                session["user_id"] = cursor.lastrowid
            return redirect(url_for("dashboard"))
        except Exception:
            flash("That username or email is already in use.")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE lower(username) = ? OR lower(email) = ?",
                (identifier, identifier),
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid login. Check your credentials and try again.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", **dashboard_context())


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date") or date.today().isoformat()
        if title:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO tasks (user_id, title, description, due_date) VALUES (?, ?, ?, ?)",
                    (user["id"], title, description, due_date),
                )
                conn.commit()
            flash("Task added to your forge.")
        return redirect(url_for("tasks"))
    return render_template("tasks.html", **dashboard_context())


@app.route("/task/<int:task_id>/complete", methods=["POST"])
@login_required
def complete_task(task_id):
    user = current_user()
    today = date.today().isoformat()
    with get_db_connection() as conn:
        task = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"])
        ).fetchone()
        if not task:
            return jsonify({"ok": False, "error": "Task not found"}), 404

        if task["completed"]:
            conn.execute("UPDATE tasks SET completed = 0, completed_at = NULL WHERE id = ?", (task_id,))
            conn.execute(
                "UPDATE streaks SET completed_count = MAX(completed_count - 1, 0) WHERE user_id = ? AND activity_date = ?",
                (user["id"], today),
            )
            xp = max(user["xp"] - XP_PER_TASK, 0)
        else:
            conn.execute(
                "UPDATE tasks SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,),
            )
            conn.execute(
                """
                INSERT INTO streaks (user_id, activity_date, completed_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, activity_date)
                DO UPDATE SET completed_count = completed_count + 1
                """,
                (user["id"], today),
            )
            xp = user["xp"] + XP_PER_TASK

        conn.execute("UPDATE users SET xp = ?, level = ? WHERE id = ?", (xp, level_for_xp(xp), user["id"]))
        conn.commit()

    return jsonify({"ok": True, "xp": xp, "level": level_for_xp(xp)})


@app.route("/task/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    user = current_user()
    with get_db_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
        conn.commit()
    return redirect(url_for("tasks"))


@app.route("/rewards")
@login_required
def rewards():
    return render_template("rewards.html", **dashboard_context())


@app.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html", **dashboard_context())


@app.route("/focusroom")
@login_required
def focusroom():
    return render_template("focusroom.html", **dashboard_context())


@app.route("/api/coach", methods=["POST"])
@login_required
def coach():
    user = current_user()
    message = (request.json or {}).get("message", "").lower()
    current_streak, _ = streak_stats(user["id"])

    if "tired" in message or "burn" in message:
        reply = "Take a short break, drink water, and restart with a 10 minute task. Consistency beats intensity today."
    elif "plan" in message or "schedule" in message:
        reply = "Pick three outcomes: one deep work block, one admin task, and one recovery break. Put the hardest task first."
    elif "focus" in message or "distract" in message:
        reply = "Use one 25 minute forge sprint. Silence notifications, write the next action, and only measure starting."
    else:
        reply = f"You are on a {current_streak} day streak. Choose one task, start the timer, and earn the next {XP_PER_TASK} XP."

    return jsonify({"reply": reply})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
