from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from patients.models import Patient, Appointment
from visits.models import Visit
import calendar
from datetime import date, timedelta

@login_required
def dashboard_index(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Navigate months
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    # Build calendar grid (list of weeks, each week is 7 days or None)
    cal = calendar.monthcalendar(year, month)
    
    # Get appointments for this month
    appointments = Appointment.objects.filter(
        date__year=year, date__month=month
    ).select_related('patient').order_by('date', 'time')

    # Build a dict: day -> list of appointments
    appointments_by_day = {}
    for appt in appointments:
        d = appt.date.day
        if d not in appointments_by_day:
            appointments_by_day[d] = []
        appointments_by_day[d].append(appt)

    # Build calendar weeks with appointment info
    calendar_weeks = []
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': None, 'appointments': []})
            else:
                week_days.append({
                    'day': day,
                    'is_today': (day == today.day and month == today.month and year == today.year),
                    'appointments': appointments_by_day.get(day, []),
                })
        calendar_weeks.append(week_days)

    # Prev / next month
    prev_month_date = date(year, month, 1) - timedelta(days=1)
    next_month_date = date(year, month, 28) + timedelta(days=4)
    next_month_date = next_month_date.replace(day=1)

    total_patients = Patient.objects.count()
    active_cases = Patient.objects.exclude(diagnosis='CN').count()
    recent_uploads = Visit.objects.order_by('-created_at').select_related('patient')[:5]

    month_names = [
        '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ]

    context = {
        'total_patients': total_patients,
        'active_cases': active_cases,
        'recent_uploads': recent_uploads,
        'calendar_weeks': calendar_weeks,
        'current_month_name': month_names[month],
        'current_year': year,
        'current_month': month,
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,
    }
    return render(request, 'dashboard/index.html', context)
