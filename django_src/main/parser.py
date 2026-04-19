import json
from os import name

LUCIDS = {};

class LucidSpecies:
    identification = 0
    name = ""
    types = {}
    description = ""
    spawn_rate = 0
    spawn_level_offset = 0
    evolution = {}

    def __init__(self, identification, name, types, description, spawn_rate, spawn_level_offset, evolution):
        self.identification = identification
        self.name = name
        self.types = types
        self.description = description
        self.spawn_rate = spawn_rate
        self.spawn_level_offset = spawn_level_offset
        self.evolution = evolution

    def get_name(self):
        return self.name
    
    def get_types(self):
        return self.types

    def get_description(self):
        return self.description

    def get_spawn_rate(self):
        return self.spawn_rate

    def get_spawn_level_offset(self):
        return self.spawn_level_offset

    def get_evolution(self):
        return self.evolution

def load_lucids():
    with open("../Lucids.json", "r") as file:
        data = json.load(file);

    lucids = data["lucids"]
    for i in range(len(lucids)):
        lucid = lucids[i];
        identification = lucid["id"]
        name = lucid["name"]
        types = lucid["type"]
        description = lucid["description"]
        spawn_rate = lucid["spawn_rate"]
        spawn_level_offset = lucid["spawn_level_offset"]
        evolution = lucid["evolution"]

        LUCIDS[identification] = LucidSpecies(identification, name, types, description, spawn_rate, spawn_level_offset, evolution)