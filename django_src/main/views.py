from django.shortcuts import render, redirect
from .models import Alarm
from datetime import datetime, timedelta
from django.utils import timezone

def home(request):
    # For the home page, we want to show the user their current alarm (if they have one) and whether it is due or not.
    alarm = Alarm.objects.first()

    # If there is an alarm, we check if it is due or not and pass that information to the template to be rendered.
    is_due = False
    if alarm:
        is_due = alarm.is_due()

    return render(request, "main/home.html", {
        "alarm": alarm,
        "is_due": is_due
    })

def delete_alarm(request):
    # User should only have one alarm, so we can just get the first one and delete it.
    alarm = Alarm.objects.first()

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

    alarm = Alarm.objects.first()

    # If there is no existing alarm, create a new one. 
    # If there is an existing alarm, update it with the new time and mark it as not completed.
    if not alarm:
        alarm = Alarm(time=timezone.now())

    alarm.time = alarm_datetime
    alarm.completed = False
    alarm.save()

    return redirect("home")

def account(request):
    return render(request, 'main/account.html')
