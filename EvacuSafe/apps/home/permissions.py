"""
Role-Based Access Control (RBAC) helpers and decorators for EvacuSafe.
Roles supported:
- 'Responder' / 'Viewer': Read-only dashboard view.
- 'Coordinator': Can add, edit, and archive evacuation centers, log incidents & resources.
- 'Admin': Full access, including permanent deletion of centers and account administration.
Django is_staff and is_superuser accounts are treated as Admin.
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages


def get_user_role(user):
    if not user or not user.is_authenticated:
        return 'Anonymous'
    if user.is_superuser or user.is_staff:
        return 'Admin'
    if user.username.lower() in ('admin', 'superuser'):
        return 'Admin'
    if user.username.lower() == 'coordinator':
        return 'Coordinator'
    try:
        profile = getattr(user, 'profile', None)
        if profile and profile.role:
            role = profile.role.strip()
            if role in ('Admin', 'Coordinator'):
                return role
            return 'Responder'
    except Exception:
        pass
    return 'Responder'


def is_coordinator_or_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = get_user_role(user)
    return role in ('Coordinator', 'Admin')


def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return get_user_role(user) == 'Admin'


def coordinator_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('login')
        if not is_coordinator_or_admin(request.user):
            error_msg = 'Permission denied. Coordinator or Admin role required.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'error': error_msg}, status=403)
            messages.error(request, error_msg)
            return JsonResponse({'error': error_msg}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('login')
        if not is_admin(request.user):
            error_msg = 'Permission denied. Admin role required.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'error': error_msg}, status=403)
            messages.error(request, error_msg)
            return JsonResponse({'error': error_msg}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
