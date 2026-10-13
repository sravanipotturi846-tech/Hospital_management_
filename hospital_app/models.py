from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


DEPARTMENT_CHOICES = [
    ('Cardiology', 'Cardiology'),
    ('Pediatrics', 'Pediatrics'),
    ('Orthopedics', 'Orthopedics'),
    ('Neurology', 'Neurology'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Confirmed', 'Confirmed'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
]

TIME_SLOT_CHOICES = [
    ('09:00 AM - 09:30 AM', '09:00 AM - 09:30 AM'),
    ('09:30 AM - 10:00 AM', '09:30 AM - 10:00 AM'),
    ('10:00 AM - 10:30 AM', '10:00 AM - 10:30 AM'),
    ('10:30 AM - 11:00 AM', '10:30 AM - 11:00 AM'),
    ('11:00 AM - 11:30 AM', '11:00 AM - 11:30 AM'),
    ('11:30 AM - 12:00 PM', '11:30 AM - 12:00 PM'),
    ('02:00 PM - 02:30 PM', '02:00 PM - 02:30 PM'),
    ('02:30 PM - 03:00 PM', '02:30 PM - 03:00 PM'),
    ('03:00 PM - 03:30 PM', '03:00 PM - 03:30 PM'),
    ('03:30 PM - 04:00 PM', '03:30 PM - 04:00 PM'),
    ('04:00 PM - 04:30 PM', '04:00 PM - 04:30 PM'),
    ('04:30 PM - 05:00 PM', '04:30 PM - 05:00 PM'),
]


class Doctor(models.Model):
    name = models.CharField(max_length=150, help_text="Full doctor name, e.g., Dr. Sarah Jenkins")
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(max_length=200, help_text="Detailed specialization e.g., Interventional Cardiology")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    available_days = models.CharField(
        max_length=255,
        default="Monday, Tuesday, Wednesday, Thursday, Friday",
        help_text="Comma-separated days, e.g. Monday, Tuesday, Wednesday"
    )
    is_active = models.BooleanField(default=True, help_text="Designates whether this doctor is currently active.")
    qualification = models.CharField(max_length=150, default="MBBS, MD", help_text="Degrees & certifications")
    experience_years = models.PositiveIntegerField(default=5, help_text="Years of clinical experience")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, help_text="Professional summary and background")
    profile_image = models.URLField(
        blank=True,
        null=True,
        help_text="Direct URL to doctor's portrait or avatar"
    )

    class Meta:
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.name} ({self.department})"

    def get_available_days_list(self):
        return [d.strip() for d in self.available_days.split(',') if d.strip()]

    def is_available_on_day(self, day_name):
        available_days = [d.lower() for d in self.get_available_days_list()]
        return day_name.lower() in available_days


class Patient(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_profiles')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time_slot = models.CharField(max_length=50, choices=TIME_SLOT_CHOICES)
    reason = models.TextField(help_text="Chief complaint or consultation reason")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    cancellation_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'time_slot']
        # Database constraint to guarantee no two active appointments share doctor, date and time slot
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'date', 'time_slot'],
                condition=~models.Q(status='Cancelled'),
                name='unique_active_doctor_appointment_slot'
            )
        ]

    def __str__(self):
        return f"Apt #{self.id}: {self.patient.full_name} with {self.doctor.name} on {self.date} [{self.status}]"

    def clean(self):
        super().clean()
        # 1. Prevent booking for past dates on new appointments
        if not self.pk and self.date and self.date < timezone.now().date() and self.status not in ['Completed', 'Cancelled']:
            raise ValidationError({'date': "Appointment date cannot be in the past."})

        # 2. Check doctor availability on the chosen day of week
        if self.doctor and self.date:
            day_name = self.date.strftime('%A')
            if not self.doctor.is_available_on_day(day_name):
                raise ValidationError({
                    'date': f"{self.doctor.name} is not available on {day_name}s. Available days: {self.doctor.available_days}"
                })

        # 3. Prevent double booking for the same doctor, date and time slot
        if self.doctor and self.date and self.time_slot and self.status != 'Cancelled':
            existing = Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time_slot=self.time_slot
            ).exclude(status='Cancelled')

            if self.pk:
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError(
                    f"This time slot ({self.time_slot}) is already booked for {self.doctor.name} on {self.date}. Please select an alternative slot."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def status_badge_class(self):
        mapping = {
            'Pending': 'bg-warning text-dark',
            'Confirmed': 'bg-primary text-white',
            'Completed': 'bg-success text-white',
            'Cancelled': 'bg-danger text-white',
        }
        return mapping.get(self.status, 'bg-secondary text-white')


class MedicalReport(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_reports')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='report')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    diagnosis = models.TextField(help_text="Primary medical diagnosis")
    symptoms = models.TextField(blank=True, help_text="Observed symptoms or notes")
    prescription = models.TextField(help_text="Medications, dosage, and intake instructions")
    doctor_notes = models.TextField(blank=True, help_text="Additional doctor advice / lifestyle guidelines")
    report_date = models.DateField(default=datetime.date.today)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date', '-created_at']

    def __str__(self):
        return f"Report #{self.id} for {self.patient.full_name} ({self.report_date})"
