from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('api/doctor-slots/', views.api_doctor_slots, name='api_doctor_slots'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/appointments/<int:pk>/status/', views.update_appointment_status, name='update_appointment_status'),
    path('staff/appointments/<int:appointment_id>/report/', views.create_or_edit_report, name='create_or_edit_report'),
    path('reports/<int:pk>/', views.view_report, name='view_report'),
    path('staff/doctors/', views.manage_doctors, name='manage_doctors'),
    path('login/', views.staff_login, name='login'),
    path('logout/', views.staff_logout, name='logout'),
]
