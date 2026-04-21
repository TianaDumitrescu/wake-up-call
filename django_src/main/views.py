from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from game.models import BattleSession, PlayerProfile
from game.services.progression import (
    ALARM_EARLY_NO_EFFECT,
    ALARM_LATE,
    ALARM_ON_TIME,
    apply_alarm_result,
)
from .forms import EditProfileForm, RegisterForm, PasswordChangeForm
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

    # Make name the given name, if not the username
    current_user = UserDatabase.objects.get(user=request.user)
    name = current_user.user.first_name
    if name == "":
        name = current_user.user.username

    return render(request, "main/home.html", {
        "alarm": alarm,
        "is_due": is_due,
        "user": user,
        "name": name,
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

    minimum_alarm_time = now + timezone.timedelta(hours=5)

    if alarm_datetime < minimum_alarm_time:
        messages.error(request, "You cannot create an alarm within 5 hours of the current time.")
        return redirect("home")


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
    if name == "":
        name = current_user.user.username

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

            # Adds logic for changing password
            profile = UserDatabase.objects.get(user=user)
            time_since = timezone.now() - profile.password_last_changed
            ##if time_since.total_seconds() >= 60: // For demoing purposes
            if time_since.days >= 60:
                return redirect("edit_password")
            
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
        profile, _ = PlayerProfile.objects.get_or_create(user=user_obj.user)

        leaderboard_data.append({
            "name": user_obj.user.first_name,
            "username": user_obj.user.username,
            "total_points": user_obj.totalPoints,
            "alarm_streak": profile.alarm_streak,
            "battle_win_streak": profile.battleWinStreak,
        })

    leaderboard_data.sort(
        key=lambda x: (x["total_points"], x["alarm_streak"], x["battle_win_streak"]),
        reverse=True,
    )

    return render(request, "main/leaderboard.html", {
        "leaderboard": leaderboard_data,
    })

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("account")
    else:
        form = EditProfileForm(instance=request.user)

    return render(request, "main/edit_profile.html", {"form": form})

@login_required
def edit_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            profile = UserDatabase.objects.get(user=request.user)
            profile.password_last_changed = timezone.now()
            profile.save(update_fields=["password_last_changed"])
            return redirect("home")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "edit_password.html", {"form": form})
