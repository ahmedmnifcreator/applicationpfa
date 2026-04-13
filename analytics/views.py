from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def analytics_dashboard(request):
    # This view will render placeholders for ML clustering and model comparisons
    return render(request, 'analytics/dashboard.html')
