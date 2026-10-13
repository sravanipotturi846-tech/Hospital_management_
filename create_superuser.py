import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_core.settings')
django.setup()

from django.contrib.auth.models import User
from hospital_app.models import Doctor, Patient, Appointment, MedicalReport
import datetime
from django.utils import timezone


def get_valid_date_for_doctor(doctor, offset_days=1, forward=True):
    step = 1 if forward else -1
    d = timezone.now().date() + datetime.timedelta(days=offset_days)
    for _ in range(14):
        if doctor.is_available_on_day(d.strftime('%A')):
            return d
        d += datetime.timedelta(days=step)
    return d


def create_superuser_and_seed():
    # 1. Create or update Superuser
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@auracarehealth.org')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully.")
    else:
        print(f"Superuser '{username}' already exists.")

    # 2. Seed realistic Doctors across all 4 departments if none exist
    if Doctor.objects.count() == 0:
        print("Seeding initial doctors and departments...")
        doctors_data = [
            # Cardiology
            {
                "name": "Dr. Sarah Jenkins",
                "department": "Cardiology",
                "specialization": "Interventional Cardiology & Valvular Heart Disease",
                "consultation_fee": 120.00,
                "available_days": "Monday, Tuesday, Wednesday, Thursday, Friday",
                "qualification": "MBBS, MD (Cardiology), FACC",
                "experience_years": 14,
                "email": "sarah.jenkins@auracarehealth.org",
                "phone": "+1 (555) 234-5678",
                "bio": "Senior Interventional Cardiologist specializing in coronary interventions, structural heart diseases, and preventive cardiology.",
                "profile_image": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },
            {
                "name": "Dr. Marcus Vance",
                "department": "Cardiology",
                "specialization": "Clinical Electrophysiology & Heart Failure",
                "consultation_fee": 110.00,
                "available_days": "Monday, Wednesday, Friday, Saturday",
                "qualification": "MBBS, DM (Cardiology)",
                "experience_years": 11,
                "email": "marcus.vance@auracarehealth.org",
                "phone": "+1 (555) 234-5679",
                "bio": "Pioneer in cardiac electrophysiology, arrhythmias management, cardiac pacemakers, and comprehensive heart failure clinics.",
                "profile_image": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },

            # Pediatrics
            {
                "name": "Dr. Elena Rostova",
                "department": "Pediatrics",
                "specialization": "General Pediatrics & Neonatal Intensive Care",
                "consultation_fee": 90.00,
                "available_days": "Monday, Tuesday, Wednesday, Thursday, Saturday",
                "qualification": "MBBS, MD (Pediatrics), FAAP",
                "experience_years": 10,
                "email": "elena.rostova@auracarehealth.org",
                "phone": "+1 (555) 345-6789",
                "bio": "Compassionate pediatrician committed to newborn care, child development milestones, vaccinations, and pediatric emergency management.",
                "profile_image": "https://images.unsplash.com/photo-1594824813576-96b613c2c7f5?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },
            {
                "name": "Dr. David Kim",
                "department": "Pediatrics",
                "specialization": "Pediatric Pulmonology & Allergy Immunology",
                "consultation_fee": 95.00,
                "available_days": "Tuesday, Wednesday, Thursday, Friday",
                "qualification": "MBBS, DCH, Fellowship in Pediatric Pulmonology",
                "experience_years": 8,
                "email": "david.kim@auracarehealth.org",
                "phone": "+1 (555) 345-6790",
                "bio": "Expert in childhood asthma, respiratory tract infections, allergic rhinitis, and long-term pulmonary rehabilitation.",
                "profile_image": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },

            # Orthopedics
            {
                "name": "Dr. Robert Sterling",
                "department": "Orthopedics",
                "specialization": "Joint Reconstruction & Arthroscopic Surgery",
                "consultation_fee": 130.00,
                "available_days": "Monday, Tuesday, Thursday, Friday",
                "qualification": "MBBS, MS (Orthopedics), MCh",
                "experience_years": 16,
                "email": "robert.sterling@auracarehealth.org",
                "phone": "+1 (555) 456-7890",
                "bio": "Renowned orthopedic surgeon specializing in robotic total knee and hip replacements, complex trauma reconstructive surgeries.",
                "profile_image": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },
            {
                "name": "Dr. Priya Patel",
                "department": "Orthopedics",
                "specialization": "Spine Surgery & Sports Medicine",
                "consultation_fee": 125.00,
                "available_days": "Monday, Wednesday, Friday, Saturday",
                "qualification": "MBBS, MS (Orthopedics), DNB",
                "experience_years": 12,
                "email": "priya.patel@auracarehealth.org",
                "phone": "+1 (555) 456-7891",
                "bio": "Specialized in minimally invasive spine procedures, disc herniation, sports ligament repairs, and musculoskeletal pain clinics.",
                "profile_image": "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },

            # Neurology
            {
                "name": "Dr. Alexander Wright",
                "department": "Neurology",
                "specialization": "Comprehensive Stroke & Neurocritical Care",
                "consultation_fee": 140.00,
                "available_days": "Monday, Tuesday, Wednesday, Thursday",
                "qualification": "MBBS, DM (Neurology), FAAN",
                "experience_years": 15,
                "email": "alexander.wright@auracarehealth.org",
                "phone": "+1 (555) 567-8901",
                "bio": "Chief of Neurology focusing on acute ischemic stroke interventions, cognitive disorders, dementia, and neuromuscular illnesses.",
                "profile_image": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },
            {
                "name": "Dr. Sophia Al-Mansoor",
                "department": "Neurology",
                "specialization": "Epileptology, Headache & Movement Disorders",
                "consultation_fee": 135.00,
                "available_days": "Tuesday, Wednesday, Friday, Saturday",
                "qualification": "MBBS, MD, Fellowship in Movement Disorders",
                "experience_years": 9,
                "email": "sophia.almansoor@auracarehealth.org",
                "phone": "+1 (555) 567-8902",
                "bio": "Specialized in refractory epilepsy management, Parkinson's disease, chronic migraine protocols, and clinical neurophysiology.",
                "profile_image": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=500&auto=format&fit=crop&q=80",
                "is_active": True,
            },
        ]

        created_doctors = []
        for d in doctors_data:
            doc = Doctor.objects.create(**d)
            created_doctors.append(doc)
        print(f"Created {len(created_doctors)} doctors.")

    created_doctors = list(Doctor.objects.all())

    # 3. Seed realistic sample Patients, Appointments & Reports if no appointments
    if Appointment.objects.count() == 0 and len(created_doctors) >= 4:
        p1, _ = Patient.objects.get_or_create(
            email="emily.watson@example.com",
            defaults={
                "first_name": "Emily",
                "last_name": "Watson",
                "phone": "+1 (555) 901-2345",
                "date_of_birth": datetime.date(1992, 5, 14),
                "gender": "Female",
                "blood_group": "O+",
                "address": "452 Maple Street, Westview"
            }
        )
        p2, _ = Patient.objects.get_or_create(
            email="michael.chang@example.com",
            defaults={
                "first_name": "Michael",
                "last_name": "Chang",
                "phone": "+1 (555) 901-6789",
                "date_of_birth": datetime.date(1985, 11, 23),
                "gender": "Male",
                "blood_group": "A+",
                "address": "812 Oakridge Blvd, North Hills"
            }
        )
        p3, _ = Patient.objects.get_or_create(
            email="olivia.taylor@example.com",
            defaults={
                "first_name": "Olivia",
                "last_name": "Taylor",
                "phone": "+1 (555) 901-7890",
                "date_of_birth": datetime.date(2018, 3, 10),
                "gender": "Female",
                "blood_group": "B+",
                "address": "19 Cedar Court, Greenfield"
            }
        )

        doc1 = created_doctors[0]  # Dr. Sarah Jenkins (Cardiology)
        past_date_1 = get_valid_date_for_doctor(doc1, offset_days=3, forward=False)
        apt1 = Appointment.objects.create(
            patient=p1,
            doctor=doc1,
            date=past_date_1,
            time_slot="10:00 AM - 10:30 AM",
            reason="Chest discomfort after vigorous exercise and recurrent palpitations.",
            status="Completed"
        )
        MedicalReport.objects.create(
            patient=p1,
            appointment=apt1,
            doctor=doc1,
            diagnosis="Exertional Sinus Tachycardia with mild benign ventricular ectopy.",
            symptoms="Palpitations, mild dyspnea on exertion. BP: 125/80 mmHg, HR: 88 bpm.",
            prescription="1. Metoprolol Tartrate 25mg - 1 tablet once daily after breakfast (30 days)\n2. CoQ10 100mg - 1 capsule daily with food\n3. Daily hydration minimum 2.5 Liters",
            doctor_notes="Avoid heavy caffeinated beverages. 24-hour Holter monitoring normal. Light walking encouraged.",
            report_date=past_date_1,
            follow_up_date=timezone.now().date() + datetime.timedelta(days=28)
        )

        # Appointment 2: Confirmed Upcoming
        doc3 = created_doctors[2]  # Dr. Elena Rostova (Pediatrics)
        future_date_2 = get_valid_date_for_doctor(doc3, offset_days=2, forward=True)
        Appointment.objects.create(
            patient=p3,
            doctor=doc3,
            date=future_date_2,
            time_slot="11:00 AM - 11:30 AM",
            reason="Routine annual pediatric wellness evaluation and booster vaccination.",
            status="Confirmed"
        )

        # Appointment 3: Pending Upcoming
        doc5 = created_doctors[4]  # Dr. Robert Sterling (Orthopedics)
        future_date_3 = get_valid_date_for_doctor(doc5, offset_days=3, forward=True)
        Appointment.objects.create(
            patient=p2,
            doctor=doc5,
            date=future_date_3,
            time_slot="02:30 PM - 03:00 PM",
            reason="Right knee swelling and sharp pain when descending stairs.",
            status="Pending"
        )

        # Appointment 4: Cancelled
        doc7 = created_doctors[6]  # Dr. Alexander Wright (Neurology)
        past_date_4 = get_valid_date_for_doctor(doc7, offset_days=4, forward=False)
        Appointment.objects.create(
            patient=p1,
            doctor=doc7,
            date=past_date_4,
            time_slot="09:00 AM - 09:30 AM",
            reason="Occasional tension headaches during screen time.",
            status="Cancelled",
            cancellation_reason="Patient had urgent travel; rescheduled consultation."
        )

        print("Seeded sample appointments and medical reports successfully.")


if __name__ == '__main__':
    create_superuser_and_seed()
