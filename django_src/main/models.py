from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Create your models here.
class Alarm(models.Model):
    time = models.TimeField() # The time the alarm is set for
    completed = models.BooleanField(default=False) # Whether the alarm has been marked as completed (serves as a backup for if the alarm is not deleted properly)

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

        return next_due
    
    # Function to see if the user's set alarm time is due or not
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