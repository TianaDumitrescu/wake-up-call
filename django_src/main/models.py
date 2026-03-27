from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Create your models here.
class Alarm(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    time = models.TimeField()
    label = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.label} at {self.time}"
    
    def get_next_due(alarm):
        now = datetime.now()

        due_today = now.replace(
            hour=alarm.time.hour,
            minute=alarm.time.minute,
            second=0,
            microsecond=0
        )

        if due_today > now:
            return due_today
        return due_today + timedelta(days=1)
    
    def is_due(self):
        next_due = self.get_next_due()
        return datetime.now() >= next_due