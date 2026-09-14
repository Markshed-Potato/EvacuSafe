from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import UserBasicForm, ProfileForm
from .models import Profile


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserBasicForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserBasicForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'profile/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })
