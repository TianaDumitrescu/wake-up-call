import random
import json
import os
from .models import AllLucids, TeamLucids

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUCIDS_PATH = os.path.join(BASE_DIR, 'lucids.json')

TYPE_CHART = {
    "Fire":    {"Fire": 0.5, "Water": 0.5, "Wood": 2,   "Bug": 2,   "Light": 1,   "ESP": 1,   "Bird": 1,   "Neutral": 1,   "Cyber": 1,   "Dark": 1},
    "Water":   {"Fire": 2,   "Water": 0.5, "Wood": 0.5, "Bug": 1,   "Light": 1,   "ESP": 1,   "Bird": 0.5, "Neutral": 1,   "Cyber": 2,   "Dark": 1},
    "Wood":    {"Fire": 0.5, "Water": 2,   "Wood": 0.5, "Bug": 0.5, "Light": 2,   "ESP": 1,   "Bird": 2,   "Neutral": 1,   "Cyber": 1,   "Dark": 0.5},
    "Bug":     {"Fire": 0.5, "Water": 1,   "Wood": 2,   "Bug": 0.5, "Light": 1,   "ESP": 1,   "Bird": 0.5, "Neutral": 1,   "Cyber": 2,   "Dark": 1},
    "Light":   {"Fire": 1,   "Water": 1,   "Wood": 0.5, "Bug": 1,   "Light": 1,   "ESP": 1,   "Bird": 1,   "Neutral": 1,   "Cyber": 1,   "Dark": 2},
    "ESP":     {"Fire": 1,   "Water": 1,   "Wood": 1,   "Bug": 1,   "Light": 1,   "ESP": 1,   "Bird": 1,   "Neutral": 1,   "Cyber": 0.5, "Dark": 2},
    "Bird":    {"Fire": 1,   "Water": 2,   "Wood": 0.5, "Bug": 2,   "Light": 1,   "ESP": 1,   "Bird": 0.5, "Neutral": 1,   "Cyber": 1,   "Dark": 1},
    "Neutral": {"Fire": 1,   "Water": 1,   "Wood": 1,   "Bug": 1,   "Light": 1,   "ESP": 1,   "Bird": 1,   "Neutral": 1,   "Cyber": 0.5, "Dark": 1},
    "Cyber":   {"Fire": 1,   "Water": 0.5, "Wood": 1,   "Bug": 0.5, "Light": 1,   "ESP": 2,   "Bird": 1,   "Neutral": 2,   "Cyber": 0.5, "Dark": 1},
    "Dark":    {"Fire": 1,   "Water": 1,   "Wood": 2,   "Bug": 1,   "Light": 1,   "ESP": 0.5, "Bird": 1,   "Neutral": 1,   "Cyber": 1,   "Dark": 1},
}

def load_lucids():
    # reads from lucidex
    with open(LUCIDS_PATH, 'r') as f:
        data = json.load(f)
    return data['lucids']

class Lucid:
    def __init__(self, data, level = 1, hp_upgrades = 0, ap_upgrades = 0, sp_upgrades = 0):
        # constructor
        self.id = data['id']
        self.name = data['name']
        self.type = data['type']
        self.desc = data['description']
        self.evolution = data['evolution']
        self.level = level
        self.hp_upgrades = hp_upgrades
        self.ap_upgrades = ap_upgrades
        self.sp_upgrades = sp_upgrades
        self.max_hp, self.ap, self.sp = self.stat_dist()
        self.curr_hp = self.max_hp

    def stat_dist(self):
        # calculates stats
        hp = 20 + (self.hp_upgrades * 20) # hp = 20 at lvl 1; increments by 20 each upgrade
        ap = 4  + (self.ap_upgrades * 4) # ap = 4 at lvl 1; increments by 4 each upgrade
        sp = 10 + (self.sp_upgrades * 10) #sp = 10 at lvl 1; increments by 10 each upgrade
        return hp, ap, sp
    
def get_user_party(user):
    # handles the user's party
    all_lucids_data = load_lucids()
    team_slots = TeamLucids.objects.filter(owner=user).order_by('slot')
    # TEAM CAPPED AT 3 LUCIDS MAX!!!
    if team_slots.count() > 3:
        raise ValueError("Party cannot have more than 3 Lucids")
    party = []
    for slot in team_slots:
        # goes through each of the 3 slots
        member = slot.lucid
        lucid_data = None
        for l in all_lucids_data:
            # matches id with the one in lucidex
            if l['id'] == member.lucid_id:
                lucid_data = l
                break
        # lucid object creation and adding to party
        lucid = Lucid(lucid_data, member.level, member.hp_upgrades, member.ap_upgrades, member.sp_upgrades)
        party.append(lucid)
    return party