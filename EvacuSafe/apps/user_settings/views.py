from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from .forms import UserSettingsForm
from .models import UserSettings


@login_required
def settings_view(request):
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    settings_form = UserSettingsForm(instance=user_settings)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'save_settings' in request.POST:
            settings_form = UserSettingsForm(request.POST, instance=user_settings)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, "Settings saved.")
                return redirect('user_settings')
            messages.error(request, "Please correct the errors below.")

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully.")
                return redirect('user_settings')
            messages.error(request, "Please correct the password errors below.")

    return render(request, 'user_settings/settings.html', {
        'settings_form': settings_form,
        'password_form': password_form,
    })
