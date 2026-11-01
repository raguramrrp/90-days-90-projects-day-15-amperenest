# AmpereNest — Quality Assurance & Testing Report

## 1. Test Execution Command
Execute the automated test suite on Windows via:
```powershell
.\.venv\Scripts\python.exe manage.py test tests --verbosity=2
```
or run:
```cmd
test.bat
```

## 2. Test Results Summary
- **Total Tests Run**: 28
- **Passing**: 28 (100%)
- **Failures**: 0
- **Errors**: 0
- **Execution Time**: ~16.6 seconds

## 3. Module Test Coverage Breakdown

| Test Module | Coverage Scope | Status |
|-------------|----------------|--------|
| `test_meters_readings.py` | Baseline setup, consecutive cumulative diffing, inversion flagging, meter rollover calculation, duplicate date rejection | **PASS** |
| `test_tariffs_billing.py` | Tamil Nadu verified LT-1A structure, free units deduction, multi-slab calculation, historical date lookup, bill variance | **PASS** |
| `test_appliances.py` | Daily kWh formula, monthly kWh formula, monthly cost estimation, "What-If" savings simulator | **PASS** |
| `test_analytics_forecasting.py` | Insufficient data safeguard, boundary-constrained cycle projection, chart dictionary structure | **PASS** |
| `test_alerts.py` | High daily usage trigger, bill due soon trigger, inconsistent reading trigger, default rule initialization | **PASS** |
| `test_security_isolation.py` | Unauthenticated redirect, cross-household 403 access denial, cross-meter 403 access denial | **PASS** |
| `test_reports_imports.py` | CSV export response & headers, Excel workbook export, CSV bulk import parsing & atomic transactions | **PASS** |
