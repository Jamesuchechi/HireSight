from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def personal_account_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.account_type != 'personal':
            messages.error(request, "This page is only for job seekers.")
            return redirect('dashboard:company_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def company_account_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.account_type != 'company':
            messages.error(request, "This page is only for recruiters.")
            return redirect('dashboard:personal_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper