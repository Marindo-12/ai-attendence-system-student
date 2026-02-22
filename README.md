# Face Recognition Attendance System (Flask + DeepFace + SQLite)

A role-based attendance platform using facial recognition:
- `Professor dashboard`: start/stop session, camera capture, attendance tracking.
- `Student dashboard`: view attendance status (`present` / `absent`).

The system stores users and attendance in a real database (`SQLite`), and uses `DeepFace` to identify students from webcam frames.

## Acknowledgment
This project is based on and inspired by the original repository:
- https://github.com/BIKRAMADITTYA/face-recognition-attendance-system

Thank you to the original author for the foundational work.

## Features
- Authentication system (register/login/logout).
- Roles:
  - `professor`
  - `student`
- Registration form fields:
  - `first name`
  - `last name`
  - `email`
  - `password`
  - `role`
  - `images` (students: **1 to 5 images**)
- Live attendance flow:
  - Professor starts a session.
  - Browser captures camera frames and sends them to backend.
  - Recognized students are marked `present`.
  - When session is stopped, unmarked students are auto-marked `absent`.
- Student dashboard shows latest attendance record.

## Tech Stack
- `Python`
- `Flask`
- `DeepFace`
- `OpenCV`
- `SQLite` (file: `attendance.db`)
- `HTML/Jinja` + `CSS`

## Project Structure
```text
Face-recognition-attendance-system/
├── app.py
├── requirements.txt
├── attendance.db                  # auto-created at first run
├── Images/                        # student reference images used by DeepFace
├── temp/                          # temporary recognition files
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── prof_dashboard.html
│   └── student_dashboard.html
└── static/
    └── style.css
```

## Database Schema
Tables created automatically by `app.py`:
- `users`
  - basic identity + hashed password + role
- `student_images`
  - stores each student image path
- `sessions`
  - attendance sessions started by professor
- `attendance_records`
  - one row per student per session with status (`present`/`absent`)

## Prerequisites
- Python `3.10+` (3.11 recommended)
- Webcam access in browser
- Windows/Linux/macOS

## Installation
### Windows (PowerShell)
```powershell
cd c:\Users\hp\Face-recognition-attendance-system
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/macOS
```bash
cd /path/to/Face-recognition-attendance-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the App
### Default run
```powershell
python app.py
```

Open in browser:
- `http://127.0.0.1:5000/register`
- `http://127.0.0.1:5000/login`

### If port `5000` is blocked
```powershell
python -c "from app import app; app.run(host='127.0.0.1', port=5055, debug=True)"
```
Then open:
- `http://127.0.0.1:5055/login`

## How to Use
1. Register a `professor` account.
2. Register one or more `student` accounts with 1 to 5 clear face images each.
3. Login as professor.
4. Click `Demarrer la seance`.
5. Allow camera permission in browser.
6. Students pass in front of camera to be recognized.
7. Click `Arreter la seance` to finalize attendance and mark absences.
8. Login as student to view personal status.

## API Endpoints (Current)
- `POST /prof/session/start`
- `POST /prof/session/stop`
- `POST /api/attendance/recognize`
- `GET /api/prof/records`

## Accessing the Database
The SQLite file is:
- `attendance.db`

### Quick read with Python
```powershell
python -c "import sqlite3; c=sqlite3.connect('attendance.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()); c.close()"
```

### If `sqlite3` CLI is installed
```powershell
sqlite3 attendance.db
.tables
SELECT * FROM users;
SELECT * FROM attendance_records;
.quit
```

## Common Troubleshooting
### 1) `An attempt was made to access a socket...`
Port conflict or permission issue.
- Check process using 5000:
```powershell
netstat -ano | findstr :5000
```
- Run on another port (`5055`) as shown above.

### 2) DeepFace/TensorFlow warnings in terminal
Informational warnings are common and often non-blocking if Flask server starts.

### 3) Camera not starting in browser
- Verify browser camera permission.
- Ensure webcam is not used by another app (Zoom/Teams/etc.).

### 4) Recognition is poor
- Use high-quality, front-facing student images.
- Improve lighting conditions.
- Upload multiple varied images per student (up to 5).

## Security Notes
- Change `SECRET_KEY` in `app.py` before production use.
- Use environment variables for secrets and configuration.
- Add HTTPS and proper session hardening in production.

## Recommended Next Improvements
- Migrate from SQLite to PostgreSQL/MySQL.
- Add audit logs and detailed attendance history screens.
- Add CSRF protection and stricter validation.
- Add face embedding cache for better performance at scale.

## License
Add your preferred license (`MIT`, `Apache-2.0`, etc.) in a `LICENSE` file.
