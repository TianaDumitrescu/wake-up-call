from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Create your models here.
class Alarm(models.Model):
    alarm_time = models.TimeField()
    wake_up_time = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.label} at {self.alarm_time}"
    
    def get_next_due(self):
        now = datetime.now()

        due_today = now.replace(
            hour=self.alarm_time.hour,
            minute=self.alarm_time.minute,
            second=0,
            microsecond=0
        )

        if due_today > now:
            return due_today
        return due_today + timedelta(days=1)
    
    def is_due(self):
        next_due = self.get_next_due()
        return datetime.now() >= next_due

    def update_wake_up(self):
        self.wake_up_time = datetime.now()

    def met_alarm(self):
        if self.wake_up_time == None:
            return False
        if self.wake_up_time >= self.get_next_due():
            return True
        else:
            return False