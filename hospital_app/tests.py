from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

from .models import Doctor, Patient, Appointment, MedicalReport


class HospitalPortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test doctor
        self.doctor = Doctor.objects.create(
            name="Dr. Testing Specialist",
            department="Cardiology",
            specialization="Interventional Cardiology",
            consultation_fee=100.00,
            available_days="Monday, Tuesday, Wednesday, Thursday, Friday",
            qualification="MBBS, MD",
            experience_years=8,
            email="testdoc@example.com",
            phone="+1 555-010-0101"
        )
        # Create test patient
        self.patient = Patient.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="+1 555-010-0102",
            gender="Female",
            blood_group="O+"
        )
        # Staff user
        self.staff_user = User.objects.create_user(
            username='stafftest',
            password='password123',
            is_staff=True
        )

    def test_home_page_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AuraCare")
        self.assertContains(response, "Cardiology")

    def test_doctor_list_view(self):
        response = self.client.get(reverse('doctor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Testing Specialist")

    def test_doctor_filter_by_department(self):
        response = self.client.get(reverse('doctor_list') + '?department=Cardiology')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Testing Specialist")

        response_neuro = self.client.get(reverse('doctor_list') + '?department=Neurology')
        self.assertEqual(response_neuro.status_code, 200)
        self.assertNotContains(response_neuro, "Dr. Testing Specialist")

    def test_api_doctor_slots(self):
        # Pick a valid weekday for the doctor
        test_date = timezone.now().date() + datetime.timedelta(days=1)
        while not self.doctor.is_available_on_day(test_date.strftime('%A')):
            test_date += datetime.timedelta(days=1)

        url = f"{reverse('api_doctor_slots')}?doctor_id={self.doctor.id}&date={test_date.isoformat()}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['doctor_name'], "Dr. Testing Specialist")
        self.assertTrue(data['is_available_day'])
        self.assertIn("09:00 AM - 09:30 AM", data['all_slots'])
        self.assertEqual(len(data['booked_slots']), 0)

    def test_prevent_double_booking(self):
        # Pick a valid weekday
        test_date = timezone.now().date() + datetime.timedelta(days=2)
        while not self.doctor.is_available_on_day(test_date.strftime('%A')):
            test_date += datetime.timedelta(days=1)

        slot = "10:00 AM - 10:30 AM"

        # Book first appointment
        apt1 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=test_date,
            time_slot=slot,
            reason="Initial consultation",
            status="Pending"
        )
        self.assertIsNotNone(apt1.id)

        # Attempt to book duplicate appointment via model save
        apt2 = Appointment(
            patient=self.patient,
            doctor=self.doctor,
            date=test_date,
            time_slot=slot,
            reason="Duplicate slot attempt",
            status="Pending"
        )
        with self.assertRaises(Exception):
            apt2.save()

    def test_booking_form_submission(self):
        test_date = timezone.now().date() + datetime.timedelta(days=3)
        while not self.doctor.is_available_on_day(test_date.strftime('%A')):
            test_date += datetime.timedelta(days=1)

        slot = "02:00 PM - 02:30 PM"
        form_data = {
            'doctor': self.doctor.id,
            'date': test_date.isoformat(),
            'time_slot': slot,
            'reason': "Follow-up checkup",
            'first_name': "Samuel",
            'last_name': "Jackson",
            'email': "samuel.j@example.com",
            'phone': "+1 555-999-8888",
            'gender': "Male",
            'blood_group': "A+",
            'address': "101 Boulevard",
        }
        response = self.client.post(reverse('book_appointment'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify appointment was created
        apt = Appointment.objects.filter(patient__email="samuel.j@example.com").first()
        self.assertIsNotNone(apt)
        self.assertEqual(apt.status, "Pending")
        self.assertEqual(apt.time_slot, slot)

    def test_staff_dashboard_and_status_update(self):
        test_date = timezone.now().date() + datetime.timedelta(days=4)
        while not self.doctor.is_available_on_day(test_date.strftime('%A')):
            test_date += datetime.timedelta(days=1)

        apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=test_date,
            time_slot="04:00 PM - 04:30 PM",
            reason="Checkup",
            status="Pending"
        )

        self.client.login(username='stafftest', password='password123')
        dash_response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(dash_response.status_code, 200)

        # Update status to Confirmed
        update_response = self.client.post(
            reverse('update_appointment_status', args=[apt.id]),
            data={'status': 'Confirmed'},
            follow=True
        )
        self.assertEqual(update_response.status_code, 200)
        apt.refresh_from_db()
        self.assertEqual(apt.status, "Confirmed")
