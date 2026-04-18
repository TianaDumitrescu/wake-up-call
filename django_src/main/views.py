from django.shortcuts import render, redirect
from .models import Alarm
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import UserDatabase
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    user = request.user

    # For the home page, we want to show the user their current alarm (if they have one) and whether it is due or not.
    alarm = Alarm.objects.filter(user=user).first()

    # If there is an alarm, we check if it is due or not and pass that information to the template to be rendered.
    is_due = False
    if alarm:
        is_due = alarm.is_due()

    return render(request, "main/home.html", {
        "alarm": alarm,
        "is_due": is_due,
        "user": user
    })

def delete_alarm(request):
    # User should only have one alarm, so we can just get the first one and delete it.
    alarm = Alarm.objects.filter(user=request.user).first()

    # If there is an alarm, delete it. If there isn't, do nothing and just redirect to the home page.
    if alarm:
        alarm.delete()

    return redirect("home")

def create_alarm(request):
    alarm_time_str = request.POST["time"]
    alarm_time = datetime.strptime(alarm_time_str, "%H:%M").time()
    now = timezone.localtime()

    alarm_datetime = now.replace(
        hour=alarm_time.hour,
        minute=alarm_time.minute,
        second=0,
        microsecond=0
    )

    # if time already passed → schedule for tomorrow
    if alarm_datetime <= now:
        alarm_datetime += timezone.timedelta(days=1)

    alarm = Alarm.objects.filter(user=request.user).first()

    if not alarm:
        alarm = Alarm(user=request.user, time=alarm_datetime)

    alarm.time = alarm_datetime
    alarm.completed = False
    alarm.save()

    return redirect("home")

def account(request):
    return render(request, 'main/account.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create your custom UserDatabase entry
            UserDatabase.objects.create(user=user)

            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "main/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "main/login.html", {"error": "Invalid credentials"})

    return render(request, "main/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")