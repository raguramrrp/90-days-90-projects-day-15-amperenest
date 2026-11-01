import csv
from django.http import HttpResponse
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def export_readings_csv(readings, filename="meter_readings.csv"):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Meter Name', 'Meter Number', 'Reading Date', 'Reading Time', 'Reading Value (kWh)', 'Interval Consumption (kWh)', 'Reading Type', 'Source', 'Notes'])

    for r in readings:
        writer.writerow([
            r.meter.meter_name,
            r.meter.meter_number,
            r.reading_date.strftime('%Y-%m-%d'),
            r.reading_time.strftime('%H:%M') if r.reading_time else '',
            f"{r.reading_value:.2f}",
            f"{r.consumption_kwh:.2f}",
            r.get_reading_type_display(),
            r.reading_source,
            r.notes
        ])

    return response


def export_readings_excel(readings, filename="meter_readings.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Meter Readings"

    # Header style: technical navy surface
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="172B45", end_color="172B45", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    headers = ['Meter Name', 'Meter Number', 'Reading Date', 'Reading Time', 'Reading (kWh)', 'Consumed (kWh)', 'Type', 'Source', 'Notes']
    ws.append(headers)

    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    for r in readings:
        ws.append([
            r.meter.meter_name,
            r.meter.meter_number,
            r.reading_date.strftime('%Y-%m-%d'),
            r.reading_time.strftime('%H:%M') if r.reading_time else '',
            float(r.reading_value),
            float(r.consumption_kwh),
            r.get_reading_type_display(),
            r.reading_source,
            r.notes
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


def export_bills_excel(bills, filename="electricity_bills.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bills & Expenses"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="172B45", end_color="172B45", fill_type="solid")

    headers = ['Bill #', 'Meter', 'Period Start', 'Period End', 'Units (kWh)', 'Energy Charges (₹)', 'Fixed Charges (₹)', 'Taxes/Duty (₹)', 'Total Bill (₹)', 'Actual (₹)', 'Status', 'Due Date', 'Paid Date']
    ws.append(headers)

    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for b in bills:
        ws.append([
            b.bill_number or str(b.id),
            b.meter.meter_name,
            b.billing_period_start.strftime('%Y-%m-%d'),
            b.billing_period_end.strftime('%Y-%m-%d'),
            float(b.total_units_kwh),
            float(b.energy_charges),
            float(b.fixed_charges),
            float(b.duty_and_taxes),
            float(b.total_bill_amount),
            float(b.actual_bill_amount) if b.actual_bill_amount else '',
            b.get_payment_status_display(),
            b.due_date.strftime('%Y-%m-%d') if b.due_date else '',
            b.payment_date.strftime('%Y-%m-%d') if b.payment_date else '',
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 13)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


def export_appliances_excel(appliances, filename="appliance_inventory.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Appliance Energy Audit"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="172B45", end_color="172B45", fill_type="solid")

    headers = ['Appliance Name', 'Category', 'Brand', 'Rated Power (W)', 'Qty', 'Daily Hours', 'Days/Mo', 'Standby (W)', 'Daily Est. (kWh)', 'Monthly Est. (kWh)', 'Est. Cost (₹/mo)', 'Star Rating', 'Status']
    ws.append(headers)

    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for a in appliances:
        ws.append([
            a.name,
            a.get_category_display(),
            a.brand or '',
            a.rated_power_watts,
            a.quantity,
            float(a.daily_operating_hours),
            a.days_used_per_month,
            float(a.standby_power_watts),
            float(a.daily_consumption_kwh),
            float(a.monthly_consumption_kwh),
            float(a.estimate_monthly_cost()),
            f"{a.energy_star_rating} Star" if a.energy_star_rating else 'Unrated',
            'Active' if a.is_active else 'Inactive'
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 13)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
