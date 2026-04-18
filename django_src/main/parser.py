import json

global LUCIDS = {};

class Lucid:
    identification = 0
    name = ""
    types = {}
    descriptions = ""
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

        LUCIDS[i] = Lucid(identification, name, types, description, spawn_rate, spawn_level_offset, evolution)

load_lucids