TYPE_CHART = {
    "Fire": {"Fire": 0.5, "Water": 0.5, "Wood": 2, "Bug": 2, "Light": 1, "ESP": 1, "Bird": 1, "Neutral": 1, "Cyber": 1, "Dark": 1},
    "Water": {"Fire": 2, "Water": 0.5, "Wood": 0.5, "Bug": 1, "Light": 1, "ESP": 1, "Bird": 0.5, "Neutral": 1, "Cyber": 2, "Dark": 1},
    "Wood": {"Fire": 0.5, "Water": 2, "Wood": 0.5, "Bug": 0.5, "Light": 2, "ESP": 1, "Bird": 2, "Neutral": 1, "Cyber": 1, "Dark": 0.5},
    "Bug": {"Fire": 0.5, "Water": 1, "Wood": 2, "Bug": 0.5, "Light": 1, "ESP": 1, "Bird": 0.5, "Neutral": 1, "Cyber": 2, "Dark": 1},
    "Light": {"Fire": 1, "Water": 1, "Wood": 0.5, "Bug": 1, "Light": 1, "ESP": 1, "Bird": 1, "Neutral": 1, "Cyber": 1, "Dark": 2},
    "ESP": {"Fire": 1, "Water": 1, "Wood": 1, "Bug": 1, "Light": 1, "ESP": 1, "Bird": 1, "Neutral": 1, "Cyber": 0.5, "Dark": 2},
    "Bird": {"Fire": 1, "Water": 2, "Wood": 0.5, "Bug": 2, "Light": 1, "ESP": 1, "Bird": 0.5, "Neutral": 1, "Cyber": 1, "Dark": 1},
    "Neutral": {"Fire": 1, "Water": 1, "Wood": 1, "Bug": 1, "Light": 1, "ESP": 1, "Bird": 1, "Neutral": 1, "Cyber": 0.5, "Dark": 1},
    "Cyber": {"Fire": 1, "Water": 0.5, "Wood": 1, "Bug": 0.5, "Light": 1, "ESP": 2, "Bird": 1, "Neutral": 2, "Cyber": 0.5, "Dark": 1},
    "Dark": {"Fire": 1, "Water": 1, "Wood": 2, "Bug": 1, "Light": 1, "ESP": 0.5, "Bird": 1, "Neutral": 1, "Cyber": 1, "Dark": 1},
}

def get_multiplier(attack_type, defender_types):
    multiplier = 1
    for defender_type in defender_types:
        multiplier *= TYPE_CHART.get(attack_type, {}).get(defender_type, 1)
    return multiplier