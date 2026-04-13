from django.db import models
from patients.models import Patient

class Visit(models.Model):
    FORMAT_CHOICES = [
        ('dicom', 'DICOM Series'),
        ('nifti', 'NIfTI (.nii / .nii.gz)'),
        ('zip',   'ZIP Archive'),
        ('unknown', 'Unknown'),
    ]
    STATUS_CHOICES = [
        ('pending', 'En attente...'),
        ('processing', 'En cours...'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    date = models.DateField()

    # Single-file upload (NIfTI / ZIP)
    mri_file = models.FileField(upload_to='mri_scans/', blank=True, null=True)

    # Multi-file DICOM: we store the relative folder path inside MEDIA_ROOT
    mri_folder = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="Relative path to saved DICOM folder (e.g. mri_scans/visit_12/)"
    )
    mri_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='unknown')
    file_count  = models.IntegerField(default=0, help_text="Number of DICOM slices uploaded")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.date} ({self.mri_format})"
