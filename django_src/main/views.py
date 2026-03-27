from django.shortcuts import render, redirect
from .models import Alarm
from datetime import datetime, timedelta
from django.utils import timezone

def home(request):
    # If the user submits a form to set an alarm (create alarm popup), then we create a new alarm object with submitted information
    if request.method == 'POST':
        alarm_time = request.POST["time"]

        alarm = Alarm.objects.first()

        # If the user already has an alarm, the existing alarm is updated 
        # (in the future i have to change the html to make the button called "edit alarm" if there is a alarm already)
        if not alarm:
            alarm = Alarm()

        alarm.time = alarm_time
        alarm.completed = False
        alarm.save()
    
    # For the home page, we want to show the user their current alarm (if they have one) and whether it is due or not.
    alarm = Alarm.objects.first()
    is_due = False

    # If there is an alarm, we check if it is due or not and pass that information to the template to be rendered.
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

def account(request):
    return render(request, 'main/account.html')
