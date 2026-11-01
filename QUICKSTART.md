# AmpereNest — Quick Start Guide

Get AmpereNest running locally on Windows in under 60 seconds.

## Automated Quick Start (Windows)
Double-click `setup.bat` (or execute from PowerShell):
```powershell
.\setup.bat
```
Then start the server:
```powershell
.\run.bat
```
Visit `http://127.0.0.1:8000/` and sign in:
- **Username**: `demouser`
- **Password**: `demo1234`

---

## Manual Step-by-Step Installation

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 (Recommended: Python 3.12 64-bit)
- Windows PowerShell

### 2. Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
copy .env.example .env
```
*(Default settings use SQLite3; set `DATABASE_URL` if connecting to PostgreSQL)*

### 5. Run Database Migrations
```powershell
python manage.py migrate
```

### 6. Load Demonstration Sample Data
```powershell
python manage.py load_sample_data
```

### 7. Run Test Suite
```powershell
python manage.py test tests
```

### 8. Start Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Open `http://127.0.0.1:8000/` in your browser.
