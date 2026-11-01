# AmpereNest — User Guide

## 1. Getting Started & Logging In
1. Start the server using `run.bat` or `python manage.py runserver`.
2. Open your browser and navigate to `http://127.0.0.1:8000/`.
3. Sign in using the pre-seeded demonstration credentials:
   - **Username**: `demouser`
   - **Password**: `demo1234`
4. Or register a new account via `/accounts/register/`.

## 2. Managing Households & Switching Context
- Navigate to **Household &rarr; Household Management** to view your registered properties.
- Use the **Household Switcher Dropdown** in the top navigation bar to instantaneously shift the entire platform's context between multiple residences (e.g. "Anna Nagar Residence" vs "Madurai Family Villa").

## 3. Recording Meter Readings
- Navigate to **Consumption &rarr; Meter Readings &rarr; New Dial Reading**.
- **Method 1 (Cumulative Dial)**: Enter the physical whole dial reading (kWh) shown on your electric meter. The system calculates the net interval consumption automatically.
- **Method 2 (Direct kWh)**: If you use a smart plug, sub-meter, or want to log daily consumption directly, switch to "Direct kWh Entry".
- **Meter Replacements**: If your electricity board installed a new zeroed meter, check "Meter Replacement or Rollover Reset" to avoid negative inversion flags.

## 4. Using the Smart Bill Calculator
- Navigate to **Billing &rarr; Bill Calculator**.
- Enter your total consumed units (e.g. 250 kWh), select your tariff schedule, and input your sanctioned connected load (e.g. 3.0 kW).
- Click **Calculate Detailed Breakdown** to see:
  - Step-by-step telescopic slab charges.
  - Subsidized free units deductions (e.g. TN Govt 100 Free Units).
  - Electricity duty / tax calculations.
  - Transparent net payable estimate.

## 5. Appliance Inventory & "What-If" Savings Planner
- Navigate to **Household &rarr; Appliances** to audit device-level loads.
- Navigate to **Energy Control &rarr; Savings Planner**:
  1. Select an appliance (e.g. "Master Bedroom Split AC 1.5T").
  2. Reduce assumed daily operating hours from 6.0 to 4.0.
  3. Review the simulated monthly kWh and ₹ cost savings.
  4. Save the scenario for future tracking.

## 6. Exporting Reports
- Navigate to **Analytics &rarr; Reports** to download:
  - Meter Readings Log (.csv or .xlsx)
  - Official Utility Bills Register (.xlsx)
  - Appliance Audit Inventory (.xlsx)
