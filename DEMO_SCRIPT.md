# AmpereNest — 90-Second Demonstration Script

Use this sequence during recruiter walkthroughs, portfolio reviews, or hackathon presentations.

---

### Step 1: Login & Workspace Overview (0:00 - 0:15)
- Open `http://127.0.0.1:8000/`.
- Log in with `demouser` / `demo1234`.
- **Key Talking Point**: "AmpereNest is a full-stack household electricity intelligence platform with a restrained, technical workspace interface tailored for commercial utility management."
- Highlight the **KPI Metrics Bar**: Cycle Consumption, Estimated Bill, Budget Remaining, and Daily Average.

---

### Step 2: Multi-Household & Sub-Meter Switching (0:15 - 0:30)
- Click the top household switcher dropdown and switch between **"Anna Nagar Residence"** and **"Madurai Family Villa"**.
- Point out how all readings, appliance inventories, and budgets immediately scope to the selected property with server-side authorization.
- Navigate to **Household &rarr; Meter Management** to show multi-meter tracking (Main 3-Phase Domestic meter vs Submersible motor line).

---

### Step 3: Verified Telescopic Tariff & Smart Bill Calculator (0:30 - 0:50)
- Navigate to **Billing &rarr; Tariff Settings &rarr; TANGEDCO Domestic LT-1A**.
- Show the telescopic slab schedule: 0-100 free units, 101-200 @ ₹4.50, 201-400 @ ₹6.00, 401-500 @ ₹8.00, >500 @ ₹11.00.
- Navigate to **Billing &rarr; Bill Calculator**:
  - Enter `350` units and click Calculate.
  - Show the transparent breakdown: slab allocations, 100-unit government subsidy deduction, 5% electricity tax, and net payable amount.

---

### Step 4: Appliance Intelligence & Savings Planner (0:50 - 1:15)
- Navigate to **Household &rarr; Appliance Insights** to reveal the energy distribution pie chart.
- Note how the 1.5T Inverter AC consumes ~42% of household energy.
- Open **Energy Control &rarr; Savings Planner**:
  - Select the Air Conditioner.
  - Reduce runtime from 6.0 to 4.0 hours/day.
  - Point out the simulated monthly savings: **90 kWh saved (~₹495.00/month)**.
  - Save the scenario to the database.

---

### Step 5: Rule-Based Alerts & Audit Reports (1:15 - 1:30)
- Navigate to **Energy Control &rarr; Alerts** to inspect active alerts (high daily usage, bill due dates).
- Open **Analytics &rarr; Reports** and click **Download CSV** or **Excel** to show instant export of the audit trail.
- Conclude: "AmpereNest bridges the gap between opaque utility bills and proactive everyday energy control."
