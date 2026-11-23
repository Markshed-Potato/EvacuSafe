from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.utils import translation
from .forms import UserSettingsForm
from .models import UserSettings


LANGUAGE_SESSION_KEY = '_language'


@login_required
def settings_view(request):
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    
    # Activate preferred language
    if user_settings.language:
        translation.activate(user_settings.language)
        request.session[LANGUAGE_SESSION_KEY] = user_settings.language

    settings_form = UserSettingsForm(instance=user_settings)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'save_settings' in request.POST:
            settings_form = UserSettingsForm(request.POST, instance=user_settings)
            if settings_form.is_valid():
                saved_settings = settings_form.save()
                lang = saved_settings.language
                translation.activate(lang)
                request.session[LANGUAGE_SESSION_KEY] = lang

                messages.success(request, "Settings saved.")
                response = redirect('user_settings')
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    lang,
                    max_age=365 * 24 * 60 * 60,
                )
                return response
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
        'current_language': user_settings.language,
    })
