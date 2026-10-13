from django import forms
from django.utils import timezone
from .models import Doctor, Patient, Appointment, MedicalReport, TIME_SLOT_CHOICES, GENDER_CHOICES, BLOOD_GROUP_CHOICES


class AppointmentBookingForm(forms.ModelForm):
    # Patient fields to allow instant booking without separate prior registration
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. John'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Doe'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 000-1234'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    blood_group = forms.ChoiceField(
        choices=[('', 'Select Blood Group (Optional)')] + BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'}),
        required=False
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time_slot', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select', 'id': 'id_time_slot'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your symptoms or reason for visit...'}),
        }

    def __init__(self, *args, **kwargs):
        patient_instance = kwargs.pop('patient_instance', None)
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)

        # Prepopulate patient fields if patient instance passed
        if patient_instance:
            self.fields['first_name'].initial = patient_instance.first_name
            self.fields['last_name'].initial = patient_instance.last_name
            self.fields['email'].initial = patient_instance.email
            self.fields['phone'].initial = patient_instance.phone
            self.fields['gender'].initial = patient_instance.gender
            self.fields['blood_group'].initial = patient_instance.blood_group
            self.fields['address'].initial = patient_instance.address

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time_slot = cleaned_data.get('time_slot')

        if doctor and date:
            day_name = date.strftime('%A')
            if not doctor.is_available_on_day(day_name):
                self.add_error(
                    'date',
                    f"{doctor.name} is not available on {day_name}s. Available days: {doctor.available_days}"
                )

        if doctor and date and time_slot:
            # Check for double booking
            existing = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time_slot=time_slot
            ).exclude(status='Cancelled')

            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                self.add_error(
                    'time_slot',
                    f"Dr. {doctor.name} is already booked for {time_slot} on {date}. Please pick an available slot."
                )

        return cleaned_data


class AppointmentStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'cancellation_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'cancellation_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Specify reason if cancelling...'
            }),
        }


class MedicalReportForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ['diagnosis', 'symptoms', 'prescription', 'doctor_notes', 'follow_up_date']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Primary diagnosis'}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reported patient symptoms'}),
            'prescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Medication names, dosage, duration, frequency'}),
            'doctor_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Doctor advice, diet, physical activity limitations'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            'name', 'department', 'specialization', 'consultation_fee',
            'available_days', 'qualification', 'experience_years',
            'email', 'phone', 'bio', 'profile_image', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monday, Tuesday, Thursday'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_image': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
