from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.budget_dashboard, name='dashboard'),
    path('edit/', views.budget_edit, name='edit'),
    path('goals/add/', views.goal_create, name='goal_create'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),
]
