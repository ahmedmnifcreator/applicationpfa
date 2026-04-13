from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Patient, Appointment

@login_required
def patient_list(request):
    query = request.GET.get('q', '')
    if query:
        patients = Patient.objects.filter(name__icontains=query)
    else:
        patients = Patient.objects.all().order_by('-created_at')
    return render(request, 'patients/list.html', {'patients': patients, 'query': query})

@login_required
def patient_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        diagnosis = request.POST.get('diagnosis', 'CN')
        clinical_notes = request.POST.get('clinical_notes')
        
        patient = Patient.objects.create(
            name=name, age=age, gender=gender,
            diagnosis=diagnosis, clinical_notes=clinical_notes
        )
        messages.success(request, f"Patient {patient.name} ajouté avec succès.")
        return redirect('patients:detail', pk=patient.pk)
    return render(request, 'patients/add.html')

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    visits = list(patient.visits.all().order_by('date').select_related('biomarker'))
    appointments = patient.appointments.all().order_by('date')
    latest_visit = visits[-1] if visits else None
    return render(request, 'patients/detail.html', {
        'patient': patient,
        'visits': visits,
        'appointments': appointments,
        'latest_visit': latest_visit,
    })

@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.name = request.POST.get('name', patient.name)
        patient.age = request.POST.get('age', patient.age)
        patient.gender = request.POST.get('gender', patient.gender)
        patient.diagnosis = request.POST.get('diagnosis', patient.diagnosis)
        patient.clinical_notes = request.POST.get('clinical_notes', patient.clinical_notes)
        patient.save()
        messages.success(request, "Dossier patient mis à jour.")
        return redirect('patients:detail', pk=patient.pk)
    return render(request, 'patients/edit.html', {'patient': patient})

@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, "Patient supprimé.")
        return redirect('patients:list')
    return render(request, 'patients/confirm_delete.html', {'patient': patient})

@login_required
def appointment_add(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        date = request.POST.get('date')
        time = request.POST.get('time') or None
        appointment_type = request.POST.get('appointment_type', 'Consultation')
        notes = request.POST.get('notes', '')
        
        patient = get_object_or_404(Patient, pk=patient_id)
        Appointment.objects.create(
            patient=patient,
            date=date,
            time=time,
            appointment_type=appointment_type,
            notes=notes
        )
        messages.success(request, f"Rendez-vous créé pour {patient.name}.")
        return redirect('dashboard:index')
    patients = Patient.objects.all().order_by('name')
    return render(request, 'patients/appointment_add.html', {'patients': patients})

@login_required
def appointment_delete(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    appt.delete()
    messages.success(request, "Rendez-vous supprimé.")
    return redirect('dashboard:index')
