# AmpereNest — Project Overview

## 1. Executive Summary
**AmpereNest** is an everyday-use household energy and electricity cost intelligence platform engineered for homeowners, tenants, and multi-property managers. Unlike static dashboards or basic CRUD demonstrations, AmpereNest actively monitors daily electricity consumption throughout the billing cycle, calculates progressive telescopic slab-based utility tariffs (including verified Tamil Nadu TANGEDCO/TNPDCL residential schedules), manages individual appliance power drain estimates, projects cycle-end bill overruns, and evaluates rule-based alerts.

## 2. Problem Statement & Motivation
Household electricity bills in India and global emerging markets are notorious for:
1. **Billing Shock**: Users only find out their electricity cost when the official utility bill arrives 30 to 60 days later, making mid-cycle behavioral correction impossible.
2. **Complex Telescopic Tariffs**: Utility tariffs use non-linear slab tiers (e.g., 0-100 free units, ₹4.50 for 101-200, ₹6.00 for 201-400, ₹11.00 for >500 units), making manual estimation difficult and opaque.
3. **Appliance Attribution Blindness**: Households have difficulty estimating whether high bills stem from air conditioning, water pumps, refrigerators, or standby loads.
4. **Multi-Property & Sub-Meter Gaps**: Standard utility portals only display aggregate service numbers without supporting independent sub-meters (e.g. ground floor vs motor lines).

## 3. Core Objectives
- **Daily Consumption Tracking**: Enable both cumulative physical meter dial logging and direct period consumption entries.
- **Accurate Tariff Engine**: Build a fully configurable tariff calculator supporting multi-tier slabs, fixed connected-load charges, subsidies, and electricity duties.
- **Appliance Intelligence**: Maintain a device inventory with nameplate wattages and daily runtime modeling.
- **Cycle Forecasting**: Employ linear moving-average statistical forecasting with explicit safeguards against fabricating predictions on sparse data.
- **Proactive Cost Protection**: Trigger alerts for unusual consumption surges, 80% budget utilization, upcoming bill due dates, and meter dial inversions.
- **Security & Data Isolation**: Strictly enforce server-side ownership and role-based household sharing permissions.

## 4. MVP Boundaries
- Core functionality operates 100% locally without external paid APIs.
- Supports both PostgreSQL and SQLite3 out-of-the-box.
- Preconfigured with the verified Tamil Nadu Domestic LT-1A bimonthly residential tariff structure.
