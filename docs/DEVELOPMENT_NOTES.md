# AmpereNest — Development Notes & Engineering Decisions

## 1. Technical Decisions & Trade-offs

### Telescopic Slab Architecture vs Flat Per-Unit Rates
Many electricity tracking applications assume a single flat rate per unit (e.g. ₹6.00/kWh). In real-world utility frameworks—such as Tamil Nadu's TANGEDCO LT-1A—tariffs are telescopic. A domestic consumer consuming 400 kWh pays across multiple tiers (100 subsidized units, 101-200 @ ₹4.50, 201-400 @ ₹6.00). 
- **Implementation**: We implemented a dedicated `calculate_bill()` engine inside `TariffPlan` that computes the exact slab allocations, deductions, fixed charges, and percentage electricity duties dynamically.

### Dual-Method Meter Reading Engine
Households record readings in two distinct formats:
1. Cumulative physical meter dial values (e.g. 14,250.5 kWh).
2. Direct period consumption (e.g. smart plug reading of 12 kWh).
- **Implementation**: The `MeterReading` model distinguishes between `cumulative` and `direct` modes. In cumulative mode, save hooks automatically query the previous chronological record to calculate `consumption_kwh` and re-evaluate the successor record to prevent calculation drift.

### Safeguarded Statistical Forecasting vs Unsubstantiated AI
Instead of fabricating fake "AI predictions" on sparse data:
- **Decision**: We enforced a strict data-quality gate: if fewer than 2 readings exist in the current cycle and no baseline exists in the past 30 days, the forecasting engine halts and informs the user honestly. When sufficient data exists, it applies a boundary-constrained moving average projection across the remaining cycle days.

### Database Portability: Dual PostgreSQL & SQLite3 Engine
- For local development on Windows machines without active background services, AmpereNest defaults cleanly to SQLite3.
- When `DATABASE_URL` or `POSTGRES_DB` is specified in `.env`, it automatically switches to PostgreSQL via `psycopg2-binary`.
