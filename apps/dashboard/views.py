from django.shortcuts import render
from apps.accounts.decorators import personal_required, company_required


@personal_required
def personal_dashboard(request):
    return render(request, 'dashboard/personal_dashboard.html')


@company_required
def company_dashboard(request):
    return render(request, 'dashboard/company_dashboard.html')