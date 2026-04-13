import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hho_core.settings')
django.setup()

from django.contrib.auth.models import User
from patients.models import Patient
from visits.models import Visit
from biomarkers.models import Biomarker

# Create Superuser
if not User.objects.filter(username='doctor').exists():
    User.objects.create_superuser('doctor', 'doctor@example.com', 'password123')

# Create Patients
if Patient.objects.count() == 0:
    for i in range(15):
        p = Patient.objects.create(
            name=f"Demo Patient {i+1}",
            age=random.randint(60, 90),
            gender=random.choice(['M', 'F']),
            diagnosis=random.choice(['CN', 'CN', 'MCI', 'MCI', 'AD']),
            clinical_notes="Generated demo data."
        )
        
        # Create Visit
        v = Visit.objects.create(
            patient=p,
            date=date.today() - timedelta(days=random.randint(1, 300)),
            status='completed'
        )
        
        # Create Biomarker
        Biomarker.objects.create(
            visit=v,
            volume=random.uniform(2000, 4500) if p.diagnosis != 'AD' else random.uniform(1500, 2500),
            surface=random.uniform(1500, 3000),
            asymmetry=random.uniform(0.01, 0.15) if p.diagnosis != 'AD' else random.uniform(0.08, 0.25)
        )
        
print("Demo data initialized successfully!")
