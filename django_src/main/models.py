import json
import math

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
from parser import LUCIDS
from parser import Lucid
from parser import load_lucids

def create_lucid(unique_id, nickname, species_id):
    species_base = LUCIDS.get(species_id)

    if species_base is None:
        raise ValueError("This species hasn't been initialized.")

    return Lucid.objects.create(unique_id = unique_id, nickname = nickname, species_id=species_id)

# Alarm Clock Model
class Alarm(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE) # Each user should only have one alarm, so we use a OneToOneField to link the alarm to the user
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
    unique_id = models.IntegerField()
    nickname = models.CharField(max_length = 64)
    species_id = models.IntegerField()
   
    def __str__(self):
        return f"This is your {self.get_species_name()} Lucid! Their name is {self.nickname}."

    def stats(self):
        return f"Name: {self.get_species_name()}\n Description: {self.get_description()}"

    def get_species(self):
        load_lucids()
        lucid = LUCIDS.get(self.species_id)
        return lucid

    def get_unique_id(self):
        return self.unique_id

    def get_nickname(self):
        return self.nickname

    def set_nickname(self, nickname):
        self.nickname = nickname
    
    def get_species_name(self):
       species = self.get_species()
       return species.get_name() if species else ""

    # Types represents what "species" is inherited by the Lucids (i.e. )
    def get_types(self):
       species = self.get_species()
       return species.get_types() if species else []
  
    def get_description(self):
       species = self.get_species()
       return species.get_description() if species else ""

    def get_spawn_rate(self):
       species = self.get_species()
       return species.get_spawn_rate() if species else -1
       
    def get_spawn_level_offset(self):
       species = self.get_species()
       return species.get_spawn_level_offset() if species else -1

    # Evolution represents the current level of the Lucid in it's "progression path"
    def get_evolution(self):
       species = self.get_species()
       return species.get_evolution() if species else []

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
    #lucids = ArrayField(models.IntegerField(), size = 25)
    lucids = models.JSONField(default=list)
    # Represents the actual alarm clock model
    alarm = models.ForeignKey(Alarm, on_delete = models.SET_NULL, null = True, blank = True)

    # String representing the user
    def __str__(self):
        return f"Welcome {self.user.username}!"


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
            
    # # Setter for the alarm
    # def set_alarm(self, alarm):
    #     self.alarm = alarm

    # # Getter for the alarm
    # def get_alarm(self):
    #     return self.alarm