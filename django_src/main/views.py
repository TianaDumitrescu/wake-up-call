from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from game.models import BattleSession, PlayerProfile
from game.services.progression import (
    ALARM_EARLY_NO_EFFECT,
    ALARM_LATE,
    ALARM_ON_TIME,
    apply_alarm_result,
)
from .forms import RegisterForm
from .models import Alarm, UserDatabase
from django.utils import timezone

@login_required
def home(request):
    user = request.user
    profile, _ = PlayerProfile.objects.get_or_create(user=user)

    # For the home page, we want to show the user their current alarm (if they have one) and whether it is due or not.
    alarm = Alarm.objects.filter(user=user).first()

    # If there is an alarm, we check if it is due or not and pass that information to the template to be rendered.
    is_due = False
    if alarm:
        is_due = alarm.is_due()

    return render(request, "main/home.html", {
        "alarm": alarm,
        "is_due": is_due,
        "user": user,
        "game_profile": profile,
        "has_active_battle": BattleSession.objects.filter(owner=user).exists(),
    })

@login_required
@require_POST
def delete_alarm(request):
    alarm = Alarm.objects.filter(user=request.user).first()
    if alarm:
        now = timezone.localtime()
        on_time_window_start = alarm.time - timedelta(minutes=10)

        if now < on_time_window_start:
            outcome = ALARM_EARLY_NO_EFFECT
        elif now <= alarm.time:
            outcome = ALARM_ON_TIME
        else:
            outcome = ALARM_LATE

        apply_alarm_result(request.user, outcome)
        alarm.delete()

    return redirect("home")

@login_required
@require_POST
def create_alarm(request):
    alarm_time_str = request.POST.get("time")
    if not alarm_time_str:
        return redirect("home")

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
    alarm.due_determiner = False
    alarm.save()

    return redirect("home")

@login_required
def account(request):
    current_user = UserDatabase.objects.get(user=request.user)
    
    name = current_user.user.first_name
    username = current_user.user.username
    email = current_user.user.email

    return render(request, 'main/account.html', {"user_name": name, "user_username": username, "user_email": email})


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

@login_required
def leaderboard(request):
    user_database = UserDatabase.objects.select_related("user").all()

    leaderboard_data = []
    for user_obj in user_database:
        profile = PlayerProfile.objects.get(user=user_obj.user)

        leaderboard_data.append({
            "username": user_obj.user.username,
            "total_points": user_obj.totalPoints,
            "alarm_streak": profile.alarm_streak if profile else 0,
        })

    leaderboard_data.sort(
        key=lambda x: (x["total_points"], x["alarm_streak"]),
        reverse=True,
    )

    return render(request, "main/leaderboard.html", {
        "leaderboard": leaderboard_data,
    })