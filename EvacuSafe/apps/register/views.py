from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome to EvacuSafe!")
            return redirect('home')
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'register/register.html', {'form': form})
