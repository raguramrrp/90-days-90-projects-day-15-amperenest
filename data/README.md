# AmpereNest Sample Datasets

This folder provides sample data files for testing bulk meter reading import and demonstration features.

## Files

1. `sample_meter_readings.csv`:
   - Sample CSV file formatted for direct import via `/consumption/import/`.
   - Contains cumulative dial readings across a standard 30-day billing period.
   - Associated with meter number `04-201-008-1422` (created via `python manage.py load_sample_data`).

## CSV Format Specification

| Header Name | Type | Description | Required |
|-------------|------|-------------|----------|
| `reading_date` | YYYY-MM-DD | Date of observation | Yes |
| `reading_value` | Decimal | Cumulative dial value in kWh | Yes |
| `meter_number` | String | Unique physical meter identifier | Optional (if meter selected in form) |
| `reading_type` | String | `cumulative` or `direct` | Optional (default: cumulative) |
| `notes` | String | Observations / Weather context | Optional |
