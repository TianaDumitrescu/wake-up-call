import json
import math
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from datetime import datetime, timedelta
from django.utils import timezone

# Create your models here.

# Alarm Clock Model
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

# Lucid Model - Essentially represents
class Lucid(models.Model):
    identification = models.IntegerField
    name = models.CharField(max_length = 64)
    # Types represents what "species" is inherited by the Lucids (i.e. )
    types = ArrayField(models.CharField(max_length = 64), size = 5)
    description = models.CharField(max_length = 1024)
    spawn_rate = models.FloatField
    spawn_level_offset = models.IntegerField
    # Evolution represents the current level of the Lucid in it's "progression path"
    # Index one is the previous, index 2 is the next
    evolution = ArrayField(models.CharField(max_length = 64), size = 2)
   
    def __str__(self):
        return f"This is a {self.name} Lucid!"

    #def stats(self):
       # return f"Name: {self.name}\n Description: {self.description}\n Rarity: "

   # def new(identification, name, types, description, spawn_rate, spawn_level)

    #def get_id():
      #  return self.identification

    #def get_name():
   #     return 


# User Database Model - Each user will officially have one
class UserDatabase(models.Model):
    # The actual user model, which stores the username, password, and name
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    # The current score the user has
    totalPoints = models.IntegerField(default = 0);
    # The current winning streak the user has
    currentWinStreak = models.IntegerField(default = 0);
    # The current losing streak the use rhas
    currentLoseStreak = models.IntegerField(default = 0);
    # The lucids array essentially holds all the lucids
    # The number represents the Lucid ID
    lucids = ArrayField(models.IntegerField(), size = 25)
    # Represents the actual alarm clock model
    alarm = models.ForeignKey(Alarm, on_delete = models.SET_NULL, null = True, blank = True)

    # String representing the user
    def __str__(self):
        return f"Welcome {self.user.name}!"

    # Initialization for the model, occurs when a user is initially set
    def __init__(self, user):
        self.user = user

    # Getter for the user
    def get_user(self):
        return self.user

    # We use a quadratic function to allow more points to be added 
    # during higher win streaks.
    def add_points(self): 
        self.totalPoints += int(self.currentWinStreak**2 + 10)
        self.currentWinStreak += 1
        self.currentLoseStreak = 0

    # We use a quadratic function again to allow for more points
    # to be taken during higher lose streaks.
    def subtract_points(self):
        self.totalPoints -= int(self.currentLoseStreak**2 + 10)
        self.currentLoseStreak += 1
        self.currentWinStreak = 0

    # Returns -1 if too expensive, and the amount remaining otherwise.
    def spend_points(self, spending):
        if (spending > self.totalPoints):
            return -1
        else:
            self.totalPoints -= spending
            return self.totalPoints
            
    # Setter for the alarm
    def set_alarm(self, alarm):
        self.alarm = alarm

    # Getter for the alarm
    def get_alarm(self):
        return self.alarm