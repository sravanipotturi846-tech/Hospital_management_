import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from datetime import datetime, date

from .models import Doctor, Patient, Appointment, MedicalReport, TIME_SLOT_CHOICES, DEPARTMENT_CHOICES
from .forms import AppointmentBookingForm, AppointmentStatusUpdateForm, MedicalReportForm, DoctorForm


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def home(request):
    """Hospital landing page with statistics, departments, and featured doctors."""
    total_doctors = Doctor.objects.filter(is_active=True).count()
    departments = DEPARTMENT_CHOICES
    featured_doctors = Doctor.objects.filter(is_active=True)[:6]
    total_appointments = Appointment.objects.count()
    completed_appointments = Appointment.objects.filter(status='Completed').count()

    context = {
        'total_doctors': total_doctors,
        'departments': departments,
        'featured_doctors': featured_doctors,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
    }
    return render(request, 'hospital_app/home.html', context)


def doctor_list(request):
    """
    Doctor list with JavaScript and server-side filtering by department,
    search by name or specialization, and detail modals.
    """
    dept_filter = request.GET.get('department', '').strip()
    search_query = request.GET.get('q', '').strip()

    doctors = Doctor.objects.filter(is_active=True)

    if dept_filter and dept_filter.lower() != 'all':
        doctors = doctors.filter(department__iexact=dept_filter)

    if search_query:
        doctors = doctors.filter(
            Q(name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(qualification__icontains=search_query)
        )

    # Department counts for filter badges
    dept_counts = {
        dept[0]: Doctor.objects.filter(is_active=True, department=dept[0]).count()
        for dept in DEPARTMENT_CHOICES
    }

    context = {
        'doctors': doctors,
        'departments': DEPARTMENT_CHOICES,
        'dept_counts': dept_counts,
        'selected_dept': dept_filter,
        'search_query': search_query,
        'time_slots': [slot[0] for slot in TIME_SLOT_CHOICES],
    }
    return render(request, 'hospital_app/doctor_list.html', context)


def book_appointment(request):
    """
    Appointment booking view with dynamic slot selection,
    patient auto-creation/matching, and double booking prevention.
    """
    initial_doctor_id = request.GET.get('doctor')
    initial_doctor = None
    if initial_doctor_id:
        try:
            initial_doctor = Doctor.objects.get(id=initial_doctor_id, is_active=True)
        except Doctor.DoesNotExist:
            pass

    patient_instance = None
    # If logged in user has linked patient
    if request.user.is_authenticated:
        patient_instance = Patient.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            # Get or create Patient record
            email = form.cleaned_data['email'].strip().lower()
            phone = form.cleaned_data['phone'].strip()
            first_name = form.cleaned_data['first_name'].strip()
            last_name = form.cleaned_data['last_name'].strip()
            gender = form.cleaned_data['gender']
            blood_group = form.cleaned_data.get('blood_group')
            address = form.cleaned_data.get('address', '').strip()

            patient, _ = Patient.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'gender': gender,
                    'blood_group': blood_group,
                    'address': address,
                    'user': request.user if request.user.is_authenticated else None,
                }
            )
            # Update patient info if modified
            patient.first_name = first_name
            patient.last_name = last_name
            patient.phone = phone
            patient.gender = gender
            if blood_group:
                patient.blood_group = blood_group
            if address:
                patient.address = address
            if request.user.is_authenticated and not patient.user:
                patient.user = request.user
            patient.save()

            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = 'Pending'
            appointment.save()

            # Store appointment in session for easy lookup in patient portal
            booked_list = request.session.get('booked_appointments', [])
            if appointment.id not in booked_list:
                booked_list.append(appointment.id)
                request.session['booked_appointments'] = booked_list
            request.session['patient_email'] = patient.email

            messages.success(
                request,
                f"Appointment booked successfully! Reference ID: #{appointment.id}. Your appointment with {appointment.doctor.name} is currently Pending confirmation."
            )
            return redirect('appointment_detail', pk=appointment.id)
        else:
            messages.error(request, "Please correct the errors in the booking form.")
    else:
        initial_data = {}
        if initial_doctor:
            initial_data['doctor'] = initial_doctor
        form = AppointmentBookingForm(initial=initial_data, patient_instance=patient_instance)

    doctors = Doctor.objects.filter(is_active=True)
    all_slots = [slot[0] for slot in TIME_SLOT_CHOICES]

    context = {
        'form': form,
        'doctors': doctors,
        'all_slots': all_slots,
        'selected_doctor': initial_doctor,
        'today': timezone.now().date().isoformat(),
    }
    return render(request, 'hospital_app/book_appointment.html', context)


def api_doctor_slots(request):
    """
    JSON API endpoint returning booked vs available slots
    for a given doctor and date.
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing doctor_id or date'}, status=400)

    try:
        doctor = Doctor.objects.get(id=doctor_id, is_active=True)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Check if date is in past
    is_past = selected_date < timezone.now().date()

    # Check doctor availability for this day of week
    day_name = selected_date.strftime('%A')
    is_available_day = doctor.is_available_on_day(day_name)

    # Get booked slots for active appointments (exclude Cancelled)
    booked_slots = list(
        Appointment.objects.filter(
            doctor=doctor,
            date=selected_date
        ).exclude(status='Cancelled').values_list('time_slot', flat=True)
    )

    all_slots = [slot[0] for slot in TIME_SLOT_CHOICES]

    return JsonResponse({
        'doctor_name': doctor.name,
        'department': doctor.department,
        'fee': float(doctor.consultation_fee),
        'available_days': doctor.available_days,
        'day_name': day_name,
        'is_available_day': is_available_day,
        'is_past': is_past,
        'booked_slots': booked_slots,
        'all_slots': all_slots,
    })


def appointment_detail(request, pk):
    """Displays detailed confirmation slip for an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    report = getattr(appointment, 'report', None)

    context = {
        'appointment': appointment,
        'report': report,
    }
    return render(request, 'hospital_app/appointment_detail.html', context)


def patient_dashboard(request):
    """
    Patient dashboard showing upcoming and past appointments,
    status badges, report view, and cancellation workflow.
    """
    email_query = request.GET.get('email', '').strip().lower()
    session_email = request.session.get('patient_email', '')
    filter_status = request.GET.get('status', 'all')

    lookup_email = email_query or session_email

    appointments = Appointment.objects.none()
    patient = None

    if request.user.is_authenticated and not lookup_email:
        # Check user's patient profile
        patient = Patient.objects.filter(user=request.user).first()
        if patient:
            lookup_email = patient.email

    if lookup_email:
        patient = Patient.objects.filter(email=lookup_email).first()
        appointments = Appointment.objects.filter(patient__email=lookup_email)
        request.session['patient_email'] = lookup_email
    elif request.session.get('booked_appointments'):
        # Fall back to session stored appointment IDs
        appointments = Appointment.objects.filter(id__in=request.session.get('booked_appointments', []))

    # Apply status filter if specified
    today = timezone.now().date()
    if filter_status == 'upcoming':
        appointments = appointments.filter(date__gte=today).exclude(status__in=['Completed', 'Cancelled'])
    elif filter_status == 'past':
        appointments = appointments.filter(Q(date__lt=today) | Q(status='Completed'))
    elif filter_status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
        appointments = appointments.filter(status=filter_status)

    appointments = appointments.select_related('doctor', 'patient').order_by('-date', '-created_at')

    # Status counts for badge tabs
    all_patient_appointments = Appointment.objects.filter(patient__email=lookup_email) if lookup_email else appointments
    counts = {
        'all': all_patient_appointments.count(),
        'Pending': all_patient_appointments.filter(status='Pending').count(),
        'Confirmed': all_patient_appointments.filter(status='Confirmed').count(),
        'Completed': all_patient_appointments.filter(status='Completed').count(),
        'Cancelled': all_patient_appointments.filter(status='Cancelled').count(),
    }

    context = {
        'appointments': appointments,
        'patient': patient,
        'lookup_email': lookup_email,
        'filter_status': filter_status,
        'counts': counts,
    }
    return render(request, 'hospital_app/patient_dashboard.html', context)


def cancel_appointment(request, pk):
    """Allows patient or staff to cancel an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', 'Cancelled by patient').strip()
        appointment.status = 'Cancelled'
        appointment.cancellation_reason = reason
        appointment.save()
        messages.warning(request, f"Appointment #{appointment.id} has been cancelled.")

        # Redirect back to appropriate view
        if request.user.is_staff:
            return redirect('staff_dashboard')
        return redirect('patient_dashboard')

    return redirect('appointment_detail', pk=pk)


@login_required
def staff_dashboard(request):
    """
    Staff/Admin portal for managing appointments, updating statuses,
    filtering by department/doctor/date, and writing medical reports.
    """
    status_filter = request.GET.get('status', 'all')
    dept_filter = request.GET.get('department', 'all')
    doctor_filter = request.GET.get('doctor', 'all')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('q', '').strip()

    appointments = Appointment.objects.select_related('doctor', 'patient', 'report').all()

    # Statistics
    stats = {
        'total': Appointment.objects.count(),
        'pending': Appointment.objects.filter(status='Pending').count(),
        'confirmed': Appointment.objects.filter(status='Confirmed').count(),
        'completed': Appointment.objects.filter(status='Completed').count(),
        'cancelled': Appointment.objects.filter(status='Cancelled').count(),
        'today': Appointment.objects.filter(date=timezone.now().date()).count(),
    }

    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)

    if dept_filter != 'all':
        appointments = appointments.filter(doctor__department=dept_filter)

    if doctor_filter != 'all':
        appointments = appointments.filter(doctor_id=doctor_filter)

    if date_filter:
        appointments = appointments.filter(date=date_filter)

    if search_query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__email__icontains=search_query) |
            Q(doctor__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    appointments = appointments.order_by('-date', 'time_slot')

    doctors = Doctor.objects.all()

    context = {
        'appointments': appointments,
        'stats': stats,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'doctor_filter': doctor_filter,
        'date_filter': date_filter,
        'search_query': search_query,
        'departments': DEPARTMENT_CHOICES,
        'doctors': doctors,
        'statuses': ['Pending', 'Confirmed', 'Completed', 'Cancelled'],
    }
    return render(request, 'hospital_app/staff_dashboard.html', context)


@login_required
def update_appointment_status(request, pk):
    """Staff action to update appointment status via POST or modal."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        cancellation_reason = request.POST.get('cancellation_reason', '')

        if new_status in dict(Appointment._meta.get_field('status').choices):
            appointment.status = new_status
            if new_status == 'Cancelled' and cancellation_reason:
                appointment.cancellation_reason = cancellation_reason
            appointment.save()
            messages.success(request, f"Appointment #{appointment.id} updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status choice.")

    return redirect('staff_dashboard')


@login_required
def create_or_edit_report(request, appointment_id):
    """Staff/Doctor creates or edits consultation report for an appointment."""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    report, created = MedicalReport.objects.get_or_create(
        appointment=appointment,
        defaults={
            'patient': appointment.patient,
            'doctor': appointment.doctor,
            'report_date': timezone.now().date(),
        }
    )

    if request.method == 'POST':
        form = MedicalReportForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = appointment.patient
            report.doctor = appointment.doctor
            report.save()

            # Automatically set appointment to Completed if not already
            if appointment.status != 'Completed':
                appointment.status = 'Completed'
                appointment.save()

            messages.success(request, f"Medical Report for Appointment #{appointment.id} saved successfully!")
            return redirect('staff_dashboard')
        else:
            messages.error(request, "Please fix the errors in the report form.")
    else:
        form = MedicalReportForm(instance=report)

    context = {
        'form': form,
        'appointment': appointment,
        'report': report,
    }
    return render(request, 'hospital_app/medical_report_form.html', context)


def view_report(request, pk):
    """View and print medical report."""
    report = get_object_or_404(MedicalReport, pk=pk)
    context = {
        'report': report,
        'appointment': report.appointment,
    }
    return render(request, 'hospital_app/medical_report_detail.html', context)


def staff_login(request):
    """Dedicated login view with demo account pre-fill helper."""
    if request.user.is_authenticated:
        return redirect('staff_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'staff_dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'hospital_app/login.html', {'form': form})


def staff_logout(request):
    """Logout view."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def manage_doctors(request):
    """Admin view to view and add doctors."""
    doctors = Doctor.objects.all().order_by('department', 'name')
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f"Doctor {doctor.name} added successfully.")
            return redirect('manage_doctors')
    else:
        form = DoctorForm()

    context = {
        'doctors': doctors,
        'form': form,
    }
    return render(request, 'hospital_app/manage_doctors.html', context)
