from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from deepface import DeepFace
import sqlite3
import os
import uuid
import json
import base64
import binascii
from datetime import datetime
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "Images")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MIN_STUDENT_CAPTURES = 5

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-in-production"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_base64_image(data_url, output_path):
    if not data_url or "," not in data_url:
        raise ValueError("Image invalide")

    header, encoded = data_url.split(",", 1)
    if not header.startswith("data:image/"):
        raise ValueError("Format image invalide")

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise ValueError("Image corrompue") from exc

    with open(output_path, "wb") as image_file:
        image_file.write(image_bytes)


def login_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Acces non autorise", "error")
                return redirect(url_for("login"))
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('professor', 'student')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (professor_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
            marked_at TEXT NOT NULL,
            UNIQUE(session_id, student_id),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def get_active_session_id():
    conn = get_db_connection()
    row = conn.execute(
        "SELECT id FROM sessions WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def close_session_and_mark_absent(session_id):
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()

    students = conn.execute("SELECT id FROM users WHERE role = 'student'").fetchall()
    for student in students:
        exists = conn.execute(
            "SELECT 1 FROM attendance_records WHERE session_id = ? AND student_id = ?",
            (session_id, student["id"]),
        ).fetchone()
        if not exists:
            conn.execute(
                """
                INSERT INTO attendance_records (session_id, student_id, status, marked_at)
                VALUES (?, ?, 'absent', ?)
                """,
                (session_id, student["id"], now),
            )

    conn.execute(
        "UPDATE sessions SET is_active = 0, end_time = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def detect_student_from_image(temp_image_path):
    results = DeepFace.find(
        img_path=temp_image_path,
        db_path=UPLOAD_DIR,
        enforce_detection=False,
        detector_backend="opencv",
        silent=True,
    )

    if not results or len(results[0]) == 0:
        return None

    match = results[0].iloc[0]
    identity_path = match["identity"]
    filename = os.path.basename(identity_path)

    if "__" not in filename:
        return None

    student_id = filename.split("__", 1)[0]
    if not student_id.isdigit():
        return None

    return int(student_id)


@app.route("/")
def home():
    if "user_id" in session:
        if session.get("role") == "professor":
            return redirect(url_for("prof_dashboard"))
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        captures_raw = request.form.get("captures_json", "[]")

        if not all([first_name, last_name, email, password, role]):
            flash("Tous les champs sont obligatoires", "error")
            return redirect(url_for("register"))

        if role not in ["professor", "student"]:
            flash("Role invalide", "error")
            return redirect(url_for("register"))

        captures = []
        if role == "student":
            try:
                captures = json.loads(captures_raw)
            except json.JSONDecodeError:
                flash("Donnees camera invalides", "error")
                return redirect(url_for("register"))

            if not isinstance(captures, list):
                flash("Donnees camera invalides", "error")
                return redirect(url_for("register"))
            valid_captures = [
                c for c in captures if isinstance(c, dict) and c.get("data")
            ]
            if len(valid_captures) < MIN_STUDENT_CAPTURES:
                flash("Capturez au minimum 5 images", "error")
                return redirect(url_for("register"))
            captures = valid_captures

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("Cet email existe deja", "error")
            return redirect(url_for("register"))

        cursor = conn.execute(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first_name, last_name, email, generate_password_hash(password), role),
        )
        user_id = cursor.lastrowid

        if role == "student":
            saved_paths = []
            try:
                for index, capture in enumerate(captures, start=1):
                    if not isinstance(capture, dict):
                        continue

                    data_url = capture.get("data")
                    if not data_url:
                        continue

                    filename = f"{user_id}__cap{index}__{uuid.uuid4().hex}.jpg"
                    save_path = os.path.join(UPLOAD_DIR, filename)
                    save_base64_image(data_url, save_path)
                    saved_paths.append(save_path)

                    conn.execute(
                        "INSERT INTO student_images (user_id, image_path) VALUES (?, ?)",
                        (user_id, save_path),
                    )
            except ValueError:
                conn.rollback()
                conn.close()
                for path in saved_paths:
                    if os.path.exists(path):
                        os.remove(path)
                flash("Erreur lors de la sauvegarde des captures", "error")
                return redirect(url_for("register"))

        conn.commit()
        conn.close()
        flash("Compte cree avec succes", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email ou mot de passe invalide", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["name"] = f"{user['first_name']} {user['last_name']}"

        if user["role"] == "professor":
            return redirect(url_for("prof_dashboard"))
        return redirect(url_for("student_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/prof/dashboard")
@login_required(role="professor")
def prof_dashboard():
    active_session_id = get_active_session_id()

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT ar.status, ar.marked_at, u.first_name, u.last_name
        FROM attendance_records ar
        JOIN users u ON u.id = ar.student_id
        WHERE ar.session_id = ?
        ORDER BY ar.marked_at DESC
        """,
        (active_session_id,) if active_session_id else (-1,),
    ).fetchall()
    conn.close()

    return render_template(
        "prof_dashboard.html",
        active_session_id=active_session_id,
        records=rows,
    )


@app.route("/student/dashboard")
@login_required(role="student")
def student_dashboard():
    student_id = session["user_id"]

    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT ar.status, ar.marked_at, s.start_time, s.end_time
        FROM attendance_records ar
        JOIN sessions s ON s.id = ar.session_id
        WHERE ar.student_id = ?
        ORDER BY ar.id DESC
        LIMIT 1
        """,
        (student_id,),
    ).fetchone()
    conn.close()

    return render_template("student_dashboard.html", record=row)


@app.route("/prof/session/start", methods=["POST"])
@login_required(role="professor")
def start_session():
    active_session_id = get_active_session_id()
    if active_session_id:
        flash("Une seance est deja active", "error")
        return redirect(url_for("prof_dashboard"))

    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO sessions (professor_id, start_time, is_active) VALUES (?, ?, 1)",
        (session["user_id"], datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

    flash(f"Seance {cursor.lastrowid} demarree", "success")
    return redirect(url_for("prof_dashboard"))


@app.route("/prof/session/stop", methods=["POST"])
@login_required(role="professor")
def stop_session():
    active_session_id = get_active_session_id()
    if not active_session_id:
        flash("Aucune seance active", "error")
        return redirect(url_for("prof_dashboard"))

    close_session_and_mark_absent(active_session_id)
    flash("Seance terminee. Les absences ont ete marquees.", "success")
    return redirect(url_for("prof_dashboard"))


@app.route("/api/attendance/recognize", methods=["POST"])
@login_required(role="professor")
def recognize_attendance():
    active_session_id = get_active_session_id()
    if not active_session_id:
        return jsonify({"status": "error", "message": "Aucune seance active"}), 400

    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"status": "error", "message": "Image manquante"}), 400

    if not allowed_file(image.filename):
        return jsonify({"status": "error", "message": "Format image invalide"}), 400

    temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    image.save(temp_path)

    try:
        student_id = detect_student_from_image(temp_path)
    except Exception as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"status": "error", "message": f"Erreur reconnaissance: {exc}"}), 500

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if not student_id:
        return jsonify({"status": "error", "message": "Aucun etudiant reconnu"}), 200

    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    student = conn.execute(
        "SELECT id, first_name, last_name FROM users WHERE id = ? AND role = 'student'",
        (student_id,),
    ).fetchone()

    if not student:
        conn.close()
        return jsonify({"status": "error", "message": "Etudiant inconnu"}), 200

    existing = conn.execute(
        "SELECT id FROM attendance_records WHERE session_id = ? AND student_id = ?",
        (active_session_id, student_id),
    ).fetchone()

    if existing:
        conn.close()
        return jsonify(
            {
                "status": "success",
                "message": "Presence deja marquee",
                "student": f"{student['first_name']} {student['last_name']}",
            }
        )

    conn.execute(
        """
        INSERT INTO attendance_records (session_id, student_id, status, marked_at)
        VALUES (?, ?, 'present', ?)
        """,
        (active_session_id, student_id, now),
    )
    conn.commit()
    conn.close()

    return jsonify(
        {
            "status": "success",
            "message": "Presence marquee",
            "student": f"{student['first_name']} {student['last_name']}",
        }
    )


@app.route("/api/prof/records")
@login_required(role="professor")
def api_prof_records():
    active_session_id = get_active_session_id()
    if not active_session_id:
        return jsonify([])

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT u.first_name, u.last_name, ar.status, ar.marked_at
        FROM attendance_records ar
        JOIN users u ON u.id = ar.student_id
        WHERE ar.session_id = ?
        ORDER BY ar.marked_at DESC
        """,
        (active_session_id,),
    ).fetchall()
    conn.close()

    return jsonify(
        [
            {
                "student": f"{r['first_name']} {r['last_name']}",
                "status": r["status"],
                "marked_at": r["marked_at"],
            }
            for r in rows
        ]
    )


init_db()


if __name__ == "__main__":
    app.run(debug=True)

