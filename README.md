# AmpereNest — Smart Household Energy & Electricity Cost Intelligence Platform

> **Day 15 — 90 Days 90 Projects Challenge**  
> An enterprise-grade, full-stack household electricity management platform built with Python, Django 5.1, PostgreSQL/SQLite3, and Plotly analytics. Designed for everyday monitoring, telescopic utility slab calculations, appliance energy auditing, budget overruns prevention, and rule-based anomaly detection.

[![Python](https://img.shields.io/badge/Python-3.12-2375C8?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1.15-0C4B33?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite3-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Plotly](https://img.shields.io/badge/Analytics-Plotly.js-168A78?logo=plotly&logoColor=white)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed-10B981)](#15-testing-instructions-and-actual-test-status)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Project Title & Overview
**AmpereNest** is a technical energy intelligence platform built to bridge the information asymmetry between opaque utility billing cycles and everyday household consumers. Unlike static dashboard demos or toy CRUD apps, AmpereNest continuously tracks electricity consumption throughout the 30-to-60 day billing cycle, calculates non-linear telescopic utility tariffs (with pre-configured verified Tamil Nadu TANGEDCO/TNPDCL residential LT-1A schedules), estimates device-level appliance drain, forecasts cycle-end expenditures, and generates proactive rule-based alerts before budget overruns occur.

---

## 2. Problem Statement & Motivation
In residential power grids, consumer electricity bills are often a black box:
1. **Post-Facto Billing Shock**: Consumers discover their electricity bill 30 to 60 days after consumption has occurred, making mid-cycle corrective action impossible.
2. **Opaque Telescopic Slab Calculations**: Modern utility tariffs use complex tiered rate slabs (e.g., 0–100 free units, 101–200 @ ₹4.50, 201–400 @ ₹6.00, 401–500 @ ₹8.00, and >500 @ ₹11.00), making bill verification manually difficult.
3. **Appliance Attribution Blindness**: Households cannot distinguish what percentage of their bill comes from baseline refrigeration, seasonal air conditioning, water heaters, or standby vampire loads.
4. **Multi-Meter & Sub-Meter Blindness**: Utility portals aggregate entire consumer accounts without supporting distinct physical sub-meters (e.g. main 3-phase line vs borewell motor).

AmpereNest resolves these challenges through a localized, private, and automated platform.

---

## 3. Objectives & Target Audience
- **Target Users**: Individual homeowners, apartment residents, tenants, multi-property landlords, and cost-conscious families.
- **Primary Objectives**:
  - Enable accurate daily meter reading tracking via both cumulative dial values and direct kWh inputs.
  - Compute transparent, verifiable bills based on actual regional tariff revision schedules.
  - Attribute household energy usage to individual appliances with nameplate power and operating hours modeling.
  - Project end-of-cycle bills using moving-average statistical forecasting.
  - Proactively alert users when daily usage surges or monthly budgets reach 80%.

---

## 4. Key Features

### Module A — Authentication & Multi-Household Isolation
- Secure user registration, authentication, and profile management.
- Multi-household management: switch active workspace between multiple properties (e.g. "Anna Nagar Residence" vs "Madurai Family Villa") with instant context switching.
- Role-based household sharing: Owner, Admin, Member, and Viewer permissions.
- Server-side access control preventing cross-tenant URL manipulation.

### Module B — Electricity Meter Management
- Multi-meter support per household (e.g. Main 3-Phase Domestic, Ground Floor Sub-meter, Submersible Pump Meter).
- Physical serial number, service connection account, sanctioned load (kW), and dial rollover digit configuration.
- Assign distinct tariff plans to different meters in the same household.

### Module C — Daily Consumption Tracking
- **Method 1 (Cumulative Meter Dial)**: Enter current display value; system automatically computes interval consumption by diffing against the chronological predecessor.
- **Method 2 (Direct kWh Entry)**: Directly log units consumed from smart plugs or periodic sub-meter tallies.
- **Integrity Validations**: Duplicate date detection, decreasing dial warning (inversion detection), and meter rollover/replacement handling.

### Module D — Configurable Tariff Engine (Tamil Nadu Verified)
- Comprehensive tariff engine supporting tiered slabs, telescopic structures, flat/per-kW fixed charges, state government subsidies, and percentage electricity duties.
- Preconfigured with verified **Tamil Nadu Domestic LT-1A bimonthly residential tariff structure** (first 100 units free government subsidy, ₹4.50, ₹6.00, ₹8.00, ₹11.00 slabs, 5% electricity tax).
- Tariff revision history tracking effective dates so historical bills use historical rates without retroactively altering past calculations.

### Module E — Smart Bill Calculator
- Interactive bill simulator: enter consumption units and connected load to receive an itemized, transparent charge breakdown.
- Visual line items detailing slab allocations, free unit subsidies, and regulatory surcharges.
- Actual vs. estimated variance reporting to catch utility billing discrepancies.

### Module F — Appliance Management & Intelligence
- Device-level appliance inventory: category, brand, rated power (Watts), quantity, daily hours, days/month, standby power, and BEE star ratings.
- Device consumption formulas: daily kWh, monthly kWh, and estimated monthly cost in ₹.
- Explicit measurement disclosure distinguishing nameplate estimates from whole-house meter measurements.

### Module G — Bill & Expense Management
- Track official utility invoices, bill numbers, billing period boundaries, issue dates, and due dates.
- Automatic payment status management (`Pending`, `Paid`, `Overdue`) derived from real dates.
- Upload and attach original electricity bill PDF or image documents.

### Module H — Consumption Forecasting
- Statistical moving-average forecasting projecting end-of-cycle consumption and estimated bill amount.
- Confidence scoring based on cycle maturity and reading frequency.
- **Honest Data Safeguard**: Refuses to fabricate predictions when fewer than 2 readings exist, clearly prompting users to log additional data.

### Module I — Budget & Energy Goals
- Monthly budget thresholds in ₹, target consumption caps in kWh, and daily pacing limits.
- Real-time budget progress bar showing percentage of budget consumed and remaining buffer.
- Energy efficiency milestones and tracking (e.g. "Limit Summer AC to 5 hrs/day").

### Module J — Rule-Based Alert Engine
- Evaluates real conditions: High daily usage, unusual 7-day surge, 80% budget utilization, projected budget overruns, upcoming due dates, and decreasing reading anomalies.
- In-app alerts with severity indicators (`Info`, `Warning`, `Danger`) and dismiss/read toggles.

### Module K — Energy Insights & "What-If" Savings Planner
- Automated usage diagnostics flagging high-drain appliances and week-over-week trends.
- Interactive **"What-If" Savings Simulator**: adjust appliance runtime hours or power ratings to compute exact simulated kWh and ₹ monthly cost reductions.
- Save and archive efficiency scenarios.

### Module L — Analytics & Data Exports
- Interactive Plotly.js charts: 30-day daily consumption trend, 6-month historical totals, and appliance distribution donut chart.
- Structured data exports: Meter readings (.csv and .xlsx), Utility bills register (.xlsx), and Appliance audit sheet (.xlsx).
- Bulk CSV/Excel meter reading import with preview, column mapping, and atomic transaction safety.

---

## 5. Visual Interface & Screenshots

AmpereNest features a **Professional Energy Intelligence Workspace** design system: Inter typography, a restrained technical palette (`#172B45` navy, `#2375C8` technical blue, `#168A78` forest teal), 240px fixed left sidebar, asymmetric metric grids, and an optional technical charcoal dark theme.

| View | Screenshot | Description |
|------|------------|-------------|
| **Dashboard** | ![Dashboard](screenshots/dashboard.png) | High-level energy intelligence workspace with cycle metrics, trend charts, and active alerts |
| **Meter Readings** | ![Meter Readings](screenshots/readings.png) | Historical dial register, interval calculations, and cumulative validation badges |
| **Bill Calculator** | ![Bill Calculator](screenshots/bill_calculator.png) | Telescopic slab calculation engine showing transparent subsidy and duty breakdowns |
| **Appliance Inventory** | ![Appliances](screenshots/appliances.png) | Appliance energy audit inventory with nameplate wattages and monthly cost estimates |
| **Savings Planner** | ![Savings Planner](screenshots/savings_planner.png) | Interactive "What-If" simulator modeling appliance hour reductions and monthly ₹ savings |
| **Budget & Goals** | ![Budget & Goals](screenshots/budgets_goals.png) | Pacing bar, projected overrun warnings, and energy efficiency milestone tracking |
| **Alerts Engine** | ![Alerts](screenshots/alerts.png) | Proactive notification inbox with severity filtering and rule toggles |

---

## 6. Architecture & System Design

```mermaid
flowchart TD
    User([Household Resident]) -->|HTTP / Browser| WebApp[Django 5.1 Application Server]

    subgraph "Core Service Layer"
        Middleware[HouseholdContextMiddleware]
        TariffSvc[Tariff & Slab Engine]
        ConsSvc[Reading & Import Engine]
        AlertSvc[Rule-Based Alert Evaluator]
        AnlSvc[Statistical Forecasting & Trends]
        ReportSvc[Excel & CSV Report Generator]
    end

    WebApp --> Middleware
    Middleware --> TariffSvc
    Middleware --> ConsSvc
    Middleware --> AlertSvc
    Middleware --> AnlSvc
    Middleware --> ReportSvc

    subgraph "Database Persistence (PostgreSQL / SQLite3)"
        DB[(Normalized Relational Tables)]
    end

    TariffSvc --> DB
    ConsSvc --> DB
    AlertSvc --> DB
    AnlSvc --> DB
    ReportSvc --> DB
```

For complete database schema details, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 7. Technology Stack

| Layer | Technologies | Purpose |
|-------|--------------|---------|
| **Backend** | Python 3.12, Django 5.1.15 | Core MVC architecture, authentication, ORM, and forms |
| **Database** | PostgreSQL 15+ / SQLite3 | Dual-engine support via `psycopg2-binary` and `dj-database-url` |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla ES6) | Premium technical workspace UI without heavy framework bloat |
| **Analytics & Data** | Pandas 2.2, NumPy 2.5, Plotly.js 2.35 | Time-series aggregations, statistical forecasting, interactive charts |
| **File Handling** | OpenPyXL 3.1, Pillow 13.0, CSV | Excel spreadsheet generation, bulk data imports, document attachments |
| **Production Ready** | WhiteNoise 6.12, Python-Dotenv | Static asset streaming and environment secret injection |
| **Testing** | Django TestCase, Pytest | 28 automated unit, integration, and security test cases |

---

## 8. Project Directory Structure

```
90-days-90-projects-day-15-amperenest/
├── .env.example                # Sample environment variables
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Dependency manifest
├── setup.bat                   # One-click Windows setup script
├── run.bat                     # Windows server startup script
├── test.bat                    # Automated test runner script
├── manage.py                   # Django management executable
├── config/                     # Project configuration & settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                   # User profiles, auth, & theme preferences
├── households/                 # Multi-household management & permissions
├── meters/                     # Electricity meter inventory & dials
├── tariffs/                    # Tariff plans, slabs, & calculation service
├── consumption/                # Meter readings, validations, & CSV import
├── billing/                    # Utility bills & smart calculator
├── appliances/                 # Device audit & nameplate energy estimates
├── budgets/                    # Monthly budgets, caps, & efficiency goals
├── alerts/                     # Rule-based alert engine & notification inbox
├── analytics/                  # Statistical forecasting, trends, & planner
├── core/                       # Dashboard, context processors, & sample data
├── templates/                  # Modular HTML5 templates
├── static/                     # Custom technical CSS & JS
├── data/                       # Sample CSV files for import testing
├── screenshots/                # Real captured application screenshots
└── docs/                       # Technical architecture & user guides
```

---

## 9. Prerequisites
- **Operating System**: Windows 10 / Windows 11 (or Linux / macOS)
- **Runtime**: Python 3.10, 3.11, or 3.12 (Python 3.12 64-bit recommended)
- **Database**: PostgreSQL (optional; built-in SQLite3 is pre-configured out-of-the-box)

---

## 10. Step-by-Step Windows Installation

### Step 1: Open PowerShell
Navigate to the project root directory:
```powershell
cd "d:\90 days\90-days-90-projects-day-15-amperenest"
```

### Step 2: Automated Installation (Recommended)
Run the automated Windows setup script:
```powershell
.\setup.bat
```
*This script automatically creates a `.venv` virtual environment, installs dependencies, initializes the database, and loads the demonstration dataset.*

### Step 3: Manual Installation (Alternative)
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create local configuration
copy .env.example .env

# 4. Run database migrations
python manage.py migrate

# 5. Populate demonstration sample data
python manage.py load_sample_data
```

---

## 11. Quick Start Commands
Start the development server:
```powershell
.\run.bat
```
*(or manually: `python manage.py runserver 127.0.0.1:8000`)*

Open your browser at:
`http://127.0.0.1:8000/`

**Demonstration Credentials:**
- **Username**: `demouser`
- **Password**: `demo1234`

---

## 12. Environment Variables & PostgreSQL Setup

Edit `.env` to configure your database:

```ini
# Core Configuration
SECRET_KEY=your-production-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (Leave blank for default SQLite3)
# Option A: Full Connection String
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/amperenest_db

# Option B: Individual PostgreSQL parameters
# POSTGRES_DB=amperenest_db
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
```

---

## 13. Demonstration Dataset Setup
The project includes a built-in demonstration dataset generator:
```powershell
python manage.py load_sample_data
```
This populates:
- **2 Multi-tenant Households**: "Anna Nagar Residence" (Chennai, 5 kW load) and "Madurai Family Villa" (Madurai, 7.5 kW load).
- **2 Electricity Meters**: 3-Phase residential domestic meter + 1-Phase submersible motor meter.
- **90 Consecutive Daily Readings**: Realistic seasonal variances and weekend increases.
- **Historical Utility Bills**: Official bills with itemized slab breakdowns, subsidies, and payment states.
- **12 Registered Appliances**: Air conditioners, refrigerators, BLDC fans, water heaters, and home workstations.
- **Energy Budgets & Active Alerts**: Pacing alerts, due date notices, and savings scenarios.

---

## 14. Example Usage: Bill Calculator Walkthrough
To verify the telescopic calculation engine:
1. Navigate to **Billing &rarr; Bill Calculator**.
2. Input `250` units (kWh) consumed.
3. Select **TANGEDCO Domestic LT-1A (Verified Bimonthly)**.
4. Input `3.0` kW sanctioned load.
5. Click **Calculate Detailed Breakdown**:
   - **Slab 1 (0–100 kWh)**: 100 units @ ₹4.50 = ₹450.00
   - **Slab 2 (100–200 kWh)**: 100 units @ ₹4.50 = ₹450.00
   - **Slab 3 (200–250 kWh)**: 50 units @ ₹6.00 = ₹300.00
   - **Gross Energy Charges**: ₹1,200.00
   - **TN Govt Subsidy (First 100 units free)**: -₹450.00
   - **Net Energy Charges**: ₹750.00
   - **Electricity Duty (5%)**: +₹37.50
   - **FPPCA Fuel Surcharge (250 &times; ₹0.25)**: +₹62.50
   - **Net Payable Bill**: **₹850.00**

---

## 15. Testing Instructions and Actual Test Status

Run the automated test suite on Windows via:
```powershell
.\test.bat
```
*(or manually: `python manage.py test tests --verbosity=2`)*

### Actual Test Status: PASS (28 / 28 Tests Passed)
```
Creating test database for alias 'default'...
Found 28 test(s).
System check identified no issues (0 silenced).
test_high_daily_consumption_trigger (tests.test_alerts.AlertsEngineTestCase) ... ok
test_inconsistent_reading_trigger (tests.test_alerts.AlertsEngineTestCase) ... ok
test_bill_due_soon_trigger (tests.test_alerts.AlertsEngineTestCase) ... ok
test_forecast_safeguard_with_insufficient_data (tests.test_analytics_forecasting.AnalyticsAndForecastingTestCase) ... ok
test_forecast_projection_with_sufficient_data (tests.test_analytics_forecasting.AnalyticsAndForecastingTestCase) ... ok
test_dashboard_chart_data_structure (tests.test_analytics_forecasting.AnalyticsAndForecastingTestCase) ... ok
test_daily_consumption_calculation (tests.test_appliances.ApplianceIntelligenceTestCase) ... ok
test_monthly_consumption_calculation (tests.test_appliances.ApplianceIntelligenceTestCase) ... ok
test_monthly_cost_estimate (tests.test_appliances.ApplianceIntelligenceTestCase) ... ok
test_savings_simulator (tests.test_appliances.ApplianceIntelligenceTestCase) ... ok
test_consecutive_reading_consumption_calculation (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_decreasing_reading_inversion_flag (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_direct_consumption_entry (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_duplicate_reading_date_rejected (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_first_reading_baseline (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_meter_rollover_reset_calculation (tests.test_meters_readings.MeterReadingsTestCase) ... ok
test_csv_export (tests.test_reports_imports.ReportsAndImportsTestCase) ... ok
test_excel_export (tests.test_reports_imports.ReportsAndImportsTestCase) ... ok
test_csv_import_valid_rows (tests.test_reports_imports.ReportsAndImportsTestCase) ... ok
test_unauthenticated_redirect (tests.test_security_isolation.SecurityAndIsolationTestCase) ... ok
test_user_cannot_access_other_household (tests.test_security_isolation.SecurityAndIsolationTestCase) ... ok
test_user_cannot_edit_other_household (tests.test_security_isolation.SecurityAndIsolationTestCase) ... ok
test_user_cannot_view_other_meter (tests.test_security_isolation.SecurityAndIsolationTestCase) ... ok
test_bill_calculation_250_units (tests.test_tariffs_billing.TariffsAndBillingTestCase) ... ok
test_bill_calculation_under_100_units (tests.test_tariffs_billing.TariffsAndBillingTestCase) ... ok
test_bill_variance_calculation (tests.test_tariffs_billing.TariffsAndBillingTestCase) ... ok
test_historical_tariff_date_lookup (tests.test_tariffs_billing.TariffsAndBillingTestCase) ... ok
test_tamil_nadu_tariff_structure_integrity (tests.test_tariffs_billing.TariffsAndBillingTestCase) ... ok

----------------------------------------------------------------------
Ran 28 tests in 16.687s

OK
Destroying test database for alias 'default'...
```

---

## 16. Known Limitations
1. **Nameplate vs Real-Time Device Telemetry**: Appliance calculations rely on rated nameplate wattages and user-reported runtime hours. Real-time smart plug IoT telemetry (Zigbee/MQTT) is slated for future hardware integrations.
2. **Billing Cycle Variations**: While bimonthly, monthly, and quarterly schedules are fully supported, utility meter reader dispatch delays (e.g. reading taken on day 63 instead of day 60) must be accommodated by updating the period end date.

---

## 17. Troubleshooting Common Issues
- **Decreasing Reading Flagged**: If a reading shows an "Inversion" badge, the dial value entered was lower than the previous reading. If the utility replaced the meter, edit the reading and check **Meter Replacement or Rollover Reset**.
- **No Forecast Displayed**: The statistical forecasting model requires at least 2 readings in the current cycle or baseline data from the past 30 days. Enter today's reading to activate projections.
- **Port Conflict**: If port 8000 is occupied, execute `python manage.py runserver 127.0.0.1:8080`.

---

## 18. Security & Privacy
- **Zero Third-Party Data Leakage**: All consumption data, meter numbers, and cost analytics remain private and local. No external AI APIs or tracking services receive user telemetry.
- **CSRF & SQL Injection Protection**: Fully secured using Django's parameterized ORM and CSRF token verification on all POST endpoints.
- **File Upload Safeguards**: Attached bills and meter photos are validated for size (<5MB) and stored in dedicated media directories.

---

## 19. Future Enhancements
- Hardware Smart Meter integration via DLMS/COSEM and MQTT broker streams.
- Automated Bill OCR using local OpenCV and Tesseract OCR models.
- Solar Net-Metering dual-register support for rooftop PV generation tracking.
- WhatsApp / Telegram bot integration for daily meter reading logging.

---

## 20. Learning Outcomes
- Designing normalized relational architectures for non-linear telescopic utility tariffs and multi-tiered domestic subsidies.
- Enforcing strict multi-tenant authorization barriers in Django using context processors and middleware.
- Formulating boundary-constrained statistical forecasting algorithms with honest safeguards against sparse-data hallucinations.
- Building responsive, premium user interfaces adhering to strict enterprise design systems without relying on generic AI dashboard tropes.

---

## 21. Technical Skills & Resume Keywords
`Python 3.12` &bull; `Django 5.1` &bull; `PostgreSQL` &bull; `Django ORM` &bull; `Telescopic Tariff Calculation` &bull; `Time-Series Analytics` &bull; `Plotly.js` &bull; `Pandas` &bull; `OpenPyXL` &bull; `Energy Cost Modeling` &bull; `Statistical Forecasting` &bull; `Role-Based Access Control (RBAC)` &bull; `Enterprise UI/UX Design` &bull; `Unit & Integration Testing`

---

## 22. License & Attribution
Distributed under the **MIT License**. Created as part of the **90 Days – 90 Projects Challenge** by Ragu Ram P.
