import json
from functools import lru_cache
from pathlib import Path
LUCIDS_PATH = Path(__file__).resolve().parents[3] / "lucids.json"

# Reads from lucids.json and caches results.

@lru_cache(maxsize=1)
def load_lucids():
    with LUCIDS_PATH.open("r", encoding="utf-8") as lucid_file:
        data = json.load(lucid_file)
    return data["lucids"]

@lru_cache(maxsize=1)
def get_species_map():
    return {species["id"]: species for species in load_lucids()}

@lru_cache(maxsize=1)
def get_species_name_map():
    return {species["name"]: species for species in load_lucids()}

def get_species(species_id):
    species = get_species_map().get(species_id)
    if species is None:
        raise ValueError(f"Unknown species id: {species_id}")
    return species

def get_species_by_name(name):
    species = get_species_name_map().get(name)
    if species is None:
        raise ValueError(f"Unknown species name: {name}")
    return species

def get_spawnable_species():
    return [species for species in load_lucids() if species["spawn_rate"] is not None]

def get_chain_for_species(species_id):
    species = get_species(species_id)

    while species["evolution"]["prev"] is not None:
        species = get_species_by_name(species["evolution"]["prev"])

    chain = [species]
    while chain[-1]["evolution"]["next"] is not None:
        chain.append(get_species_by_name(chain[-1]["evolution"]["next"]))
    return chain

def get_evolution_stage(species_id):
    chain = get_chain_for_species(species_id)
    for index, species in enumerate(chain):
        if species["id"] == species_id:
            return index
    raise ValueError(f"Species {species_id} is not in its own chain.")

def get_species_for_level(species_id, level):
    chain = get_chain_for_species(species_id)
    target = chain[0]
    for current_species in chain[:-1]:
        next_name = current_species["evolution"]["next"]
        evolve_level = current_species["evolution"]["level"]
        if next_name is not None and evolve_level is not None and level >= evolve_level:
            target = get_species_by_name(next_name)
        else:
            break
    return target