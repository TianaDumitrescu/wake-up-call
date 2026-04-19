import random
from .lucid_data import get_spawnable_species
from .stats import build_even_upgrade_history

# Handles logic for spawning wild Lucids

def choose_wild_species():
    spawnable_species = get_spawnable_species()
    if not spawnable_species:
        raise ValueError("No spawnable Lucids are configured.")
    weights = [species["spawn_rate"] for species in spawnable_species]
    return random.choices(spawnable_species, weights=weights, k=1)[0]

def determine_enemy_level(party_lucids, wild_species):
    highest_party_level = max(lucid.level for lucid in party_lucids)
    return highest_party_level + (wild_species["spawn_level_offset"] or 0)

def build_enemy_upgrade_history(level):
    return build_even_upgrade_history(level)