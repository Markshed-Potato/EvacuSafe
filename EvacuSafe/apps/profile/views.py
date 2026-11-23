from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import UserBasicForm, ProfileForm
from .models import Profile
from apps.home.permissions import get_user_role


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Self-service account deactivation / deletion workflow
        if action == 'deactivate_account':
            user = request.user
            user.is_active = False
            user.save()
            logout(request)
            messages.info(request, "Your account has been deactivated. Contact an administrator to reactivate.")
            return redirect('login')

        elif action == 'delete_account':
            confirm_username = request.POST.get('confirm_username', '').strip()
            if confirm_username == request.user.username:
                user = request.user
                logout(request)
                user.delete()
                messages.warning(request, "Your account and personal profile data have been permanently deleted.")
                return redirect('login')
            else:
                messages.error(request, "Account deletion cancelled: username confirmation did not match.")
                return redirect('profile')

        user_form = UserBasicForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        # Restrict non-admin users from escalating themselves to Admin
        if not (request.user.is_staff or request.user.is_superuser or profile.role == 'Admin'):
            if request.POST.get('role') == 'Admin':
                profile_form.add_error('role', 'Only existing Administrators or staff may assign the Admin role.')

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserBasicForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    # Active session and audit context
    session_info = {
        'ip_address': request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip(),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Browser / Web Client'),
        'session_key': request.session.session_key or 'Active Session',
        'last_login': request.user.last_login or timezone.now(),
        'date_joined': request.user.date_joined,
    }

    return render(request, 'profile/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'user_role': get_user_role(request.user),
        'session_info': session_info,
    })
