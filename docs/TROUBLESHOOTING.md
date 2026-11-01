# AmpereNest — Troubleshooting Guide

## 1. Port 8000 Already in Use
**Symptom**: `Error: That port is already in use.`
**Solution**:
Specify an alternate port when running:
```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8080
```

## 2. Inconsistent / Decreasing Dial Reading Warning
**Symptom**: A reading is marked with an "Inversion" badge and displays 0 kWh consumption.
**Cause**: The entered dial value is lower than the previous reading on that meter.
**Fixes**:
- If a typo occurred, click **Edit** and correct the numeric reading.
- If the electricity utility replaced or reset the physical meter dial, edit the reading and check **Meter Replacement or Rollover Reset**.

## 3. Insufficient Data in Forecasting Panel
**Symptom**: Forecasting displays "Insufficient readings recorded for current billing cycle".
**Explanation**: This is a deliberate data-quality safeguard. AmpereNest requires at least 2 readings in the current cycle or recorded history in the past 30 days to compute reliable moving averages. Log at least 2 daily readings to enable projections.

## 4. PostgreSQL Connection Errors
**Symptom**: `psycopg2.OperationalError: could not connect to server`
**Fix**:
If PostgreSQL is not running locally, simply remove or comment out `DATABASE_URL` and `POSTGRES_DB` in your `.env` file. AmpereNest will immediately fall back to the built-in SQLite3 engine without requiring service installation.
