from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('trends/', views.consumption_trends, name='trends'),
    path('costs/', views.cost_analysis, name='costs'),
    path('forecasting/', views.forecasting_view, name='forecasting'),
    path('savings-planner/', views.savings_planner, name='savings_planner'),
    path('savings-planner/save/', views.savings_scenario_save, name='savings_save'),
    path('reports/', views.reports_hub, name='reports'),
    path('reports/readings/csv/', views.export_readings_csv_action, name='export_readings_csv'),
    path('reports/readings/excel/', views.export_readings_excel_action, name='export_readings_excel'),
    path('reports/bills/excel/', views.export_bills_excel_action, name='export_bills_excel'),
    path('reports/appliances/excel/', views.export_appliances_excel_action, name='export_appliances_excel'),
]
