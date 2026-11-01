import io
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from .models import MeterReading, ImportHistory
from meters.models import ElectricityMeter


def get_household_consumption_stats(household, days=30):
    """
    Computes consumption statistics for a household over the specified lookback days.
    """
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days)

    meters = household.meters.filter(meter_status='Active')
    readings = MeterReading.objects.filter(
        meter__in=meters,
        reading_date__gte=start_date,
        reading_date__lte=end_date,
        is_flagged_inversion=False
    ).order_by('reading_date')

    total_kwh = sum(r.consumption_kwh for r in readings)
    num_days = max(1, (end_date - start_date).days + 1)
    daily_avg_kwh = (Decimal(str(total_kwh)) / Decimal(str(num_days))).quantize(Decimal('0.01'))

    return {
        'total_kwh': total_kwh,
        'daily_avg_kwh': daily_avg_kwh,
        'readings_count': readings.count(),
        'start_date': start_date,
        'end_date': end_date,
    }


def get_billing_cycle_boundaries(household, target_date=None):
    """
    Determines start and end dates of the current billing cycle for the household.
    Default cycle start day comes from household.billing_cycle_day.
    """
    if target_date is None:
        target_date = timezone.localdate()

    cycle_day = household.billing_cycle_day

    # If target_date day >= cycle_day, cycle started this month on cycle_day
    if target_date.day >= cycle_day:
        try:
            start_date = date(target_date.year, target_date.month, cycle_day)
        except ValueError:
            # Handle months with fewer days e.g. Feb 30
            start_date = date(target_date.year, target_date.month, 28)
    else:
        # Started previous month
        prev_month = target_date.month - 1 if target_date.month > 1 else 12
        prev_year = target_date.year if target_date.month > 1 else target_date.year - 1
        try:
            start_date = date(prev_year, prev_month, cycle_day)
        except ValueError:
            start_date = date(prev_year, prev_month, 28)

    # Next cycle starts 1 month or 2 months later (depending on meter billing frequency)
    # Default to 30 days or next month cycle day
    next_month = start_date.month + 1 if start_date.month < 12 else 1
    next_year = start_date.year if start_date.month < 12 else start_date.year + 1
    try:
        next_cycle_start = date(next_year, next_month, cycle_day)
    except ValueError:
        next_cycle_start = date(next_year, next_month, 28)

    end_date = next_cycle_start - timedelta(days=1)
    days_elapsed = max(1, (target_date - start_date).days + 1)
    total_cycle_days = max(1, (end_date - start_date).days + 1)
    days_remaining = max(0, total_cycle_days - days_elapsed)

    return {
        'cycle_start': start_date,
        'cycle_end': end_date,
        'days_elapsed': days_elapsed,
        'days_remaining': days_remaining,
        'total_cycle_days': total_cycle_days,
    }


def import_readings_from_file(file_obj, household, meter_id=None, user=None):
    """
    Safely imports meter readings from CSV or Excel file within an atomic database transaction.
    Expected CSV columns:
    reading_date, reading_value, [meter_number], [reading_type], [notes]
    """
    file_name = getattr(file_obj, 'name', 'uploaded_file.csv')
    is_excel = file_name.endswith('.xlsx') or file_name.endswith('.xls')

    rows_processed = 0
    rows_imported = 0
    rows_failed = 0
    errors = []

    rows = []
    if is_excel:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_obj, data_only=True)
            sheet = wb.active
            headers = [str(cell.value).strip().lower() if cell.value else '' for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                row_dict = {}
                for idx, val in enumerate(row):
                    if idx < len(headers) and headers[idx]:
                        row_dict[headers[idx]] = val
                rows.append(row_dict)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to parse Excel workbook: {str(e)}",
                'imported': 0
            }
    else:
        # CSV parsing
        try:
            content = file_obj.read().decode('utf-8-sig', errors='replace')
            reader = csv.DictReader(io.StringIO(content))
            # Normalize headers to lowercase
            normalized_fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
            for row in reader:
                norm_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                rows.append(norm_row)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to read CSV format: {str(e)}",
                'imported': 0
            }

    selected_meter = None
    if meter_id:
        selected_meter = household.meters.filter(pk=meter_id).first()

    with transaction.atomic():
        import_record = ImportHistory.objects.create(
            household=household,
            meter=selected_meter,
            file_name=file_name,
            imported_by=user,
            status='In Progress'
        )

        for row_num, row in enumerate(rows, start=2):
            rows_processed += 1

            # Match meter
            row_meter = selected_meter
            meter_num = row.get('meter_number') or row.get('meter') or row.get('meter_id')
            if not row_meter and meter_num:
                row_meter = household.meters.filter(meter_number__iexact=str(meter_num).strip()).first()
            if not row_meter:
                row_meter = household.meters.filter(meter_status='Active').first()

            if not row_meter:
                errors.append(f"Row {row_num}: No valid meter associated.")
                rows_failed += 1
                continue

            # Parse date
            raw_date = row.get('reading_date') or row.get('date')
            parsed_date = None
            if hasattr(raw_date, 'strftime'):
                parsed_date = raw_date if isinstance(raw_date, date) else raw_date.date()
            elif isinstance(raw_date, str):
                for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(raw_date.strip(), fmt).date()
                        break
                    except ValueError:
                        continue

            if not parsed_date:
                errors.append(f"Row {row_num}: Invalid or missing reading date '{raw_date}'.")
                rows_failed += 1
                continue

            # Parse value
            raw_val = row.get('reading_value') or row.get('reading') or row.get('value') or row.get('kwh')
            try:
                reading_val = Decimal(str(raw_val).replace(',', '').strip())
                if reading_val < 0:
                    raise ValueError("Negative value")
            except (InvalidOperation, ValueError, TypeError):
                errors.append(f"Row {row_num}: Invalid numeric reading value '{raw_val}'.")
                rows_failed += 1
                continue

            # Check for duplicate date on this meter
            existing = MeterReading.objects.filter(meter=row_meter, reading_date=parsed_date).first()
            if existing:
                errors.append(f"Row {row_num}: Reading already exists for meter {row_meter.meter_name} on {parsed_date}. Skipped.")
                rows_failed += 1
                continue

            # Reading type
            raw_type = str(row.get('reading_type') or 'cumulative').strip().lower()
            reading_type = 'direct' if 'direct' in raw_type else 'cumulative'
            notes = str(row.get('notes') or '').strip()

            reading = MeterReading(
                meter=row_meter,
                reading_date=parsed_date,
                reading_value=reading_val,
                reading_type=reading_type,
                reading_source='CSV/Excel Import',
                notes=notes,
                recorded_by=user
            )
            reading.save()
            rows_imported += 1

        import_record.rows_processed = rows_processed
        import_record.rows_imported = rows_imported
        import_record.rows_failed = rows_failed
        import_record.status = 'Success' if rows_failed == 0 else ('Partial' if rows_imported > 0 else 'Failed')
        import_record.error_summary = "\n".join(errors[:20])
        import_record.save()

    return {
        'success': rows_imported > 0 or rows_processed == 0,
        'processed': rows_processed,
        'imported': rows_imported,
        'failed': rows_failed,
        'errors': errors[:10]
    }
