import math
from .lucid_data import get_evolution_stage

BASE_STATS = {
    "hp": 20,
    "attack": 4,
    "speed": 10,
}

STAT_INCREASES = {
    "hp": 20,
    "attack": 4,
    "speed": 10,
}

STAT_ORDER = ("hp", "attack", "speed")

# Counts how many times each stat has been upgraded based on history list
def count_upgrades(upgrade_history):
    counts = {stat: 0 for stat in STAT_ORDER}
    for stat in upgrade_history:
        if stat not in counts:
            raise ValueError(f"Unknown stat upgrade '{stat}'.")
        counts[stat] += 1
    return counts

# Generates balanced upgrade history for opponent Lucids
def build_even_upgrade_history(level):
    upgrades = []
    total_upgrades = max(level - 1, 0)
    for index in range(total_upgrades):
        upgrades.append(STAT_ORDER[index % len(STAT_ORDER)])
    return upgrades

# Calculates final stats based on base stats, evolution stage, and upgrade history
def calculate_stats(species_id, upgrade_history):
    counts = count_upgrades(upgrade_history)
    evolution_stage = get_evolution_stage(species_id)
    stats = {}
    for stat_name, base_value in BASE_STATS.items():
        total_bumps = counts[stat_name] + evolution_stage
        stats[stat_name] = base_value + (STAT_INCREASES[stat_name] * total_bumps)
    return stats

# Calculates damage dealt based on type strengths/weaknesses
def calculate_damage(attack_value, multiplier):
    damage = attack_value * multiplier
    return max(1, math.floor(damage))