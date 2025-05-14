from django.urls import path
from .views import (
    register_view, login_view, logout_view, dashboard_view,
    report_view, edit_report_view, delete_report,
    download_report  # Ensure this is imported
)
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', lambda request: redirect('login'), name='login'),  # 👈 add this line
    path('login/', login_view, name='login'),  # proper login route
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('report/', report_view, name='report'),
    path('report/delete/<int:pk>/', delete_report, name='delete_report'),
    #path('download-report-pdf/<int:pk>/', download_crime_report_pdf, name='download_crime_report_pdf'),
    #path('download_report/<int:pk>/', download_report, name='download_report'),
    path('download_report/<int:report_id>/', download_report, name='download_report'),
    path('report/edit/<int:report_id>/', edit_report_view, name='edit_report'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
