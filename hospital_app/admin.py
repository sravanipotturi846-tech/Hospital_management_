from django.contrib import admin
from .models import Doctor, Patient, Appointment, MedicalReport


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'specialization', 'consultation_fee', 'available_days', 'is_active', 'experience_years')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'specialization', 'qualification', 'email')
    list_editable = ('is_active', 'consultation_fee')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'gender', 'blood_group', 'created_at')
    list_filter = ('gender', 'blood_group')
    search_fields = ('first_name', 'last_name', 'email', 'phone')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'time_slot', 'status', 'created_at')
    list_filter = ('status', 'doctor__department', 'date')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'doctor__name')
    list_editable = ('status',)
    date_hierarchy = 'date'


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'report_date', 'diagnosis', 'created_at')
    list_filter = ('report_date', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 'diagnosis', 'prescription')
