from django.db import models

class Patient(models.Model):
    DIAGNOSIS_CHOICES = [
        ('CN', 'Cognitively Normal'),
        ('MCI', 'Mild Cognitive Impairment'),
        ('AD', 'Alzheimer\'s Disease'),
    ]
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    diagnosis = models.CharField(max_length=3, choices=DIAGNOSIS_CHOICES, default='CN')
    clinical_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.diagnosis})"

class Appointment(models.Model):
    TYPE_CHOICES = [
        ('Consultation', 'Consultation'),
        ('IRM', 'IRM'),
        ('Evaluation', 'Évaluation'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Consultation')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.appointment_type} le {self.date}"

