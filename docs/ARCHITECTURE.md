# AmpereNest — System Architecture & Data Model

## 1. High-Level Architectural Flow

```mermaid
flowchart TD
    User([Household User / Resident]) -->|HTTP Requests| WebServer[Django Application Server]
    
    subgraph "Core App Modules"
        Auth[accounts: Profile & Preferences]
        HH[households: Household & Permissions]
        Mtr[meters: Electricity Meters]
        Cons[consumption: Meter Readings & Import]
        Tar[tariffs: Tariff Plans, Slabs & Charges]
        Bill[billing: Invoices & Bill Calculator]
        App[appliances: Inventory & Energy Audit]
        Budg[budgets: Budget Limits & Goals]
        Alrt[alerts: Rule-Based Alert Engine]
        Anl[analytics: Forecasting, Trends & Reports]
    end

    WebServer --> Auth
    WebServer --> HH
    WebServer --> Mtr
    WebServer --> Cons
    WebServer --> Tar
    WebServer --> Bill
    WebServer --> App
    WebServer --> Budg
    WebServer --> Alrt
    WebServer --> Anl

    Cons -->|Triggers Evaluation| Alrt
    Tar -->|Calculates Slabs| Bill
    Tar -->|Estimates Cost| App
    Cons -->|Moving Average Data| Anl
    Budg -->|Budget vs Actual| Alrt

    subgraph "Database Layer (PostgreSQL / SQLite3)"
        DB[(Normalized Relational Models)]
    end

    Auth --> DB
    HH --> DB
    Mtr --> DB
    Cons --> DB
    Tar --> DB
    Bill --> DB
    App --> DB
    Budg --> DB
    Alrt --> DB
    Anl --> DB
```

## 2. Database Entity-Relationship (ER) Model

```mermaid
erDiagram
    User ||--o| UserProfile : has
    User ||--o{ Household : creates
    Household ||--o{ HouseholdMember : shares
    Household ||--o{ ElectricityMeter : owns
    ElectricityMeter ||--o{ MeterReading : logs
    ElectricityMeter ||--o{ ElectricityBill : bills
    TariffPlan ||--o{ TariffSlab : defines
    TariffPlan ||--o{ TariffCharge : includes
    TariffPlan ||--o{ ElectricityMeter : assigns
    ElectricityBill ||--o{ BillLineItem : breaks_down
    Household ||--o{ Appliance : contains
    Household ||--o{ EnergyBudget : caps
    Household ||--o{ EnergyGoal : tracks
    Household ||--o{ EnergyAlertRule : configures
    Household ||--o{ EnergyAlert : generates
    Household ||--o{ ForecastRecord : archives
    Household ||--o{ SavingsScenario : models

    Household {
        int id PK
        string name
        string property_type
        int occupants
        decimal sanctioned_load_kw
        decimal monthly_budget_amount
        int billing_cycle_day
    }

    ElectricityMeter {
        int id PK
        string meter_name
        string meter_number
        string provider
        string connection_type
        decimal sanctioned_load_kw
        int dial_digits
    }

    MeterReading {
        int id PK
        date reading_date
        time reading_time
        decimal reading_value
        decimal consumption_kwh
        string reading_type
        boolean is_flagged_inversion
        boolean is_meter_reset_or_replacement
    }

    TariffPlan {
        int id PK
        string name
        string provider
        string billing_frequency
        date effective_from
        int free_units_per_cycle
        decimal electricity_duty_pct
    }

    ElectricityBill {
        int id PK
        string bill_number
        date billing_period_start
        date billing_period_end
        date due_date
        date payment_date
        decimal total_units_kwh
        decimal total_bill_amount
        string payment_status
    }

    Appliance {
        int id PK
        string name
        string category
        int rated_power_watts
        int quantity
        decimal daily_operating_hours
        int days_used_per_month
        decimal standby_power_watts
    }
```

## 3. Key Architectural Principles
- **Idempotent Cumulative Meter Calculation**: On every cumulative reading entry, the system looks up the chronological predecessor and re-evaluates the successor reading to prevent data cascading drift.
- **Telescopic Slab Calculation Algorithm**: Progressively tiers consumed units across slabs with support for government subsidies (e.g. Tamil Nadu 100 free units) and duty percentages.
- **Data Isolation**: All view queries strictly filter against `accessible_households` populated by `HouseholdContextMiddleware`.
