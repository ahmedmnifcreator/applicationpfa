from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Biomarker

@login_required
def biomarker_list(request):
    biomarkers = Biomarker.objects.all().select_related('visit__patient')
    return render(request, 'biomarkers/list.html', {'biomarkers': biomarkers})

import csv
from django.http import HttpResponse

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="biomarkers_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Patient', 'Diagnosis', 'Date IRM', 'Volume (mm3)', 'Distance Kendall', 'Risque (%)'])
    
    biomarkers = Biomarker.objects.all().select_related('visit__patient')
    for b in biomarkers:
        writer.writerow([
            b.visit.patient.name,
            b.visit.patient.diagnosis,
            b.visit.date.strftime('%Y-%m-%d') if b.visit.date else '',
            b.volume if b.volume else '',
            b.kendall_distance if b.kendall_distance else '',
            b.risk_score if b.risk_score else ''
        ])
    return response
