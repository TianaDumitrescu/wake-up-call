from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone

# Create your models here.
class Alarm(models.Model):
    time = models.DateTimeField() # The time the alarm is set for
    completed = models.BooleanField(default=False) # Whether the alarm has been marked as completed (serves as a backup for if the alarm is not deleted properly)
    due_determiner = models.BooleanField(default=False) # This field is used to determine if the alarm is due or not. It is necessary because if the user sets an alarm for a time that has already passed, we want the alarm to be due immediately instead of waiting until the next day. This field is set to True when the alarm is created or updated, and then set to False when the alarm is marked as completed or deleted. This way, if the user sets an alarm for a time that has already passed, the alarm will be due immediately instead of waiting until the next day.

    def __str__(self):
        return f"Alarm at {self.time}"
    
    def get_next_due(self):
        now = datetime.now()

        # Setting the "next due" time to be similar to "now" so it can be compared to "now" to determine if the alarm is due or not.
        next_due = now.replace(
            hour= self.time.hour,
            minute= self.time.minute,
            second= 0,
            microsecond= 0
        )

        if next_due < now and self.due_determiner == False:
            self.due_determiner = True
            self.save()
            next_due += timedelta(days=1)

        return next_due
    
    # Function to see if the user's set alarm time is due or not
    def is_due(self):
        print(timezone.now())
        print(self.time)
        if not self.time:
            return False
        return timezone.now() >= self.time

    def update_wake_up(self):
        self.wake_up_time = datetime.now()

    def met_alarm(self):
        if self.wake_up_time == None:
            return False
        if self.wake_up_time >= self.get_next_due():
            return True
        else:
            return False