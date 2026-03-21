from django.db import models
from django.contrib.auth.models import User

class AllLucids(models.Model):
    # all the Lucids obtained by the user so far
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    lucid_id = models.IntegerField()
    level = models.IntegerField(default=1)
    hp_upgrades = models.IntegerField(default=0)
    ap_upgrades = models.IntegerField(default=0)
    sp_upgrades = models.IntegerField(default=0)

class TeamLucids(models.Model):
    # all the Lucids in the users team (capped at 3)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    slot = models.IntegerField()
    lucid = models.ForeignKey(AllLucids, on_delete=models.SET_NULL, null=True)