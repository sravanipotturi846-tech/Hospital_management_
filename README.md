# AuraCare Health — Hospital & Patient Appointment Management Portal
**Django Full-Stack Final Project — Student Assignment**

---

## 1. Project Overview
AuraCare Health is a responsive hospital and patient appointment management web portal. Patients can browse certified doctors filtered by department, interactively select available appointment slots in real-time, view appointment status tracking, and download medical reports. Administrators and clinical staff manage doctors, review patient bookings, update appointment statuses, and record consultation reports.

---

## 2. Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Backend**: Python 3.11+, Django 5.x / 6.x (MVT Architecture, Django ORM, ModelForms)
- **Database**: SQLite (`db.sqlite3` — Django default database)
- **Production Server**: Gunicorn (WSGI HTTP Server)
- **Static Assets**: WhiteNoise (Compressed & cached asset serving)
- **Deployment**: Render Web Service / Render Blueprint (`render.yaml`)

---

## 3. Database Schema & Architecture
Managed exclusively through the **Django ORM** using SQLite:

1. **`Doctor`**:
   - `name`: Doctor's full name
   - `department`: Choices (`Cardiology`, `Pediatrics`, `Orthopedics`, `Neurology`)
   - `specialization`: Detailed clinical sub-specialization
   - `consultation_fee`: Decimal fee
   - `available_days`: Comma-separated active consultation days (e.g. `Monday, Tuesday, Wednesday`)
   - `is_active`: Boolean active status
   - `qualification`, `experience_years`, `email`, `phone`, `bio`, `profile_image`
2. **`Patient`**:
   - `user`: Optional OneToOne/ForeignKey to Django `User`
   - `first_name`, `last_name`, `email`, `phone`, `gender`, `blood_group`, `address`, `created_at`
3. **`Appointment`**:
   - `patient`: `ForeignKey(Patient, on_delete=CASCADE)`
   - `doctor`: `ForeignKey(Doctor, on_delete=CASCADE)`
   - `date`: `DateField`
   - `time_slot`: `CharField` (e.g., `09:00 AM - 09:30 AM`)
   - `reason`: `TextField` (Chief complaint / symptoms)
   - `status`: `CharField` (`Pending`, `Confirmed`, `Completed`, `Cancelled`)
   - `cancellation_reason`: `TextField` (optional note upon cancellation)
   - `created_at`: `DateTimeField`
   - **Double-booking prevention**: `UniqueConstraint(fields=['doctor', 'date', 'time_slot'], condition=~Q(status='Cancelled'))`
4. **`MedicalReport`**:
   - `patient`: `ForeignKey(Patient)`
   - `appointment`: `OneToOneField(Appointment)`
   - `doctor`: `ForeignKey(Doctor)`
   - `diagnosis`, `symptoms`, `prescription`, `doctor_notes`, `report_date`, `follow_up_date`

---

## 4. Key Functional Features
- **Department Doctor Filtering**: Instant client-side JavaScript filtering across Cardiology, Pediatrics, Orthopedics, Neurology, plus real-time keyword search.
- **Interactive Slot Selector**: Dynamic AJAX slot availability check (`/api/doctor-slots/`) highlighting available slots in green and booked slots in disabled red strike-through.
- **Double Booking Prevention**: Enforced at both client UI, Model `clean()`, Form validation, and database `UniqueConstraint`.
- **Status Badges**: Distinct color-coded status badges for `Pending` (amber), `Confirmed` (blue), `Completed` (green), and `Cancelled` (red).
- **Patient Dashboard**: Lookup appointments by email, filter by upcoming vs past, cancel pending bookings, and access medical consultation reports.
- **Staff / Admin Console**: Metric cards (Total, Today, Pending, Confirmed, Completed, Cancelled), multi-parameter search/filters, one-click status transitions, and doctor roster management.
- **Medical Consultation Reports**: Clinical prescription slips with doctor sign-off, printable view, and medication regimens.

---

## 5. Local Setup & Execution Guide

### Step 1: Clone or navigate to repository
```bash
cd Hospital_management
```

### Step 2: Create & activate virtual environment
**Windows**:
```powershell
python -m venv venv
.\venv\Scripts\activate
```
**macOS / Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Initialize superuser and seed sample data
```bash
python create_superuser.py
```
*Creates default staff credentials:*
- **Username**: `admin`
- **Password**: `admin123`
- *Also seeds 8 realistic doctors across Cardiology, Pediatrics, Orthopedics, Neurology, sample patients, appointments, and medical reports.*

### Step 6: Start local server
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** in your browser.

---

## 6. Testing Workflows
1. **Browse Doctors**: Visit `/doctors/`, click department pills (`Cardiology`, `Pediatrics`, `Orthopedics`, `Neurology`), search by doctor name, and click "Quick View" modal.
2. **Book Slot**: Visit `/book/`, select a doctor and date. Notice the interactive slot picker loading available vs booked slots. Fill patient details and submit.
3. **Double Booking Test**: Try booking the exact same doctor, date, and slot again. Notice the system blocks duplicate booking and highlights the slot as booked.
4. **Patient Portal**: Visit `/patient/dashboard/`, enter `emily.watson@example.com` to review active and completed appointments, or cancel an upcoming appointment.
5. **Staff Portal**: Visit `/login/`, click **Auto-fill Demo Credentials** (`admin` / `admin123`), enter the dashboard, confirm pending appointments, and create consultation reports with prescriptions.
6. **Django Admin**: Visit `/admin/` to manage raw database records.

---

## 7. Render Deployment Guide (Mandatory)

The project includes `render.yaml` configured for Render Blueprint deployment.

### Step 1: Commit and push repository to GitHub
```bash
git init
git add .
git commit -m "Hospital appointment portal ready for Render"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to [https://dashboard.render.com/](https://dashboard.render.com/).
2. Click **New +** → **Blueprint** (or **Web Service**).
3. Connect your GitHub repository.
4. Render detects `render.yaml`:
   - **Runtime**: `Python 3.11.0`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py`
   - **Start Command**: `python manage.py migrate && python create_superuser.py && gunicorn hospital_core.wsgi:application`
5. Under Environment Variables:
   - `RENDER` = `True`
   - `SECRET_KEY` = `<your-production-secret-key>`
6. Click **Apply / Create Service**.
7. Once deployed, open the live `https://<service-name>.onrender.com` URL.
8. Access `/admin/` or `/login/` with `admin` / `admin123`.

> **Note on SQLite on Render**: SQLite is deliberately utilized per assignment rules. Render's free web service instances have ephemeral storage, so data may reset on dyno restarts. `create_superuser.py` automatically reseeds baseline data upon startup.

---

## 8. Security & Code Integrity
- `{% csrf_token %}` present on every POST form.
- Server-side validation via Django `ModelForm` & Model `clean()`.
- Staff authentication required for administrative actions (`@login_required`).
- WhiteNoise gzip/brotli static asset caching enabled.
- `DEBUG` automatically disabled in Render (`DEBUG = os.environ.get("RENDER", "False") != "True"`).
