from django.db import transaction
from game.models import OwnedLucid, PlayerProfile
from .lucid_data import get_species_for_level

STARTER_SPECIES_IDS = {1, 4, 7}
VALID_STAT_CHOICES = {"hp", "attack", "speed"}
ALARM_ON_TIME = "on_time"
ALARM_EARLY_NO_EFFECT = "early_no_effect"
ALARM_LATE = "late"

# Besides logic-based functions, most of this .py file was written by Codex

# Simple getter for player profile (creates if DNE)
def get_or_create_profile(user):
    profile, _ = PlayerProfile.objects.get_or_create(user=user)
    return profile

# Returns user's current party
def get_party_queryset(user):
    return OwnedLucid.objects.filter(owner=user, party_slot__isnull=False).order_by("party_slot", "id")

# Handles evolution if level threshold crossed
def sync_evolution(owned_lucid):
    target_species = get_species_for_level(owned_lucid.species_id, owned_lucid.level)
    changed = owned_lucid.species_id != target_species["id"]
    owned_lucid.species_id = target_species["id"]
    return changed

# MAIN PROGRESSION FUNCTIONS

# Handles starter selection close to account creation
@transaction.atomic
def choose_starter(user, species_id):
    species_id = int(species_id)
    if species_id not in STARTER_SPECIES_IDS:
        raise ValueError("Starter choice must be one of the starter Lucids.")
    profile = get_or_create_profile(user)
    if profile.starter_species_id is not None:
        raise ValueError("Starter has already been chosen.")
    starter = OwnedLucid.objects.create(
        owner=user,
        species_id=species_id,
        level=1,
        upgrade_history=[],
        party_slot=1,
    )
    profile.starter_species_id = species_id
    profile.save(update_fields=["starter_species_id", "updated_at"])
    return starter

# Grants level-up to each Lucid in party (pending status)
def grant_party_levelup(user):
    updated = []
    for lucid in get_party_queryset(user):
        lucid.pending_levelups += 1
        lucid.save(update_fields=["pending_levelups", "updated_at"])
        updated.append(lucid)
    return updated

# Handles level-up choice for a Lucid (hp, ap, sp)
@transaction.atomic
def apply_level_choice(owned_lucid, stat_choice):
    stat_choice = stat_choice.lower()
    if stat_choice not in VALID_STAT_CHOICES:
        raise ValueError("Stat choice must be hp, attack, or speed.")
    if owned_lucid.pending_levelups < 1:
        raise ValueError("This Lucid does not have a pending level-up.")
    history = list(owned_lucid.upgrade_history)
    history.append(stat_choice)
    owned_lucid.upgrade_history = history
    owned_lucid.level += 1
    owned_lucid.pending_levelups -= 1
    sync_evolution(owned_lucid)
    owned_lucid.full_clean()
    owned_lucid.save()
    return owned_lucid

# Opposite of apply_level_choice (used for streak breaks)
@transaction.atomic
def level_down_lucid(owned_lucid):
    if owned_lucid.pending_levelups > 0:
        owned_lucid.pending_levelups -= 1
        owned_lucid.save(update_fields=["pending_levelups", "updated_at"])
        return owned_lucid
    if owned_lucid.level <= 1:
        return owned_lucid
    history = list(owned_lucid.upgrade_history)
    if history:
        history.pop()
    owned_lucid.level -= 1
    owned_lucid.upgrade_history = history
    sync_evolution(owned_lucid)
    owned_lucid.full_clean()
    owned_lucid.save()
    return owned_lucid

# Sets the user's party to specified Lucids (handles ordering and validation)
@transaction.atomic
def set_party(user, owned_lucid_ids):
    normalized_ids = [int(lucid_id) for lucid_id in owned_lucid_ids]
    if len(normalized_ids) > 3:
        raise ValueError("A party can have at most 3 Lucids.")
    if len(normalized_ids) != len(set(normalized_ids)):
        raise ValueError("A Lucid cannot be assigned to multiple party slots.")
    selected_lucids = list(OwnedLucid.objects.filter(owner=user, id__in=normalized_ids))
    if len(selected_lucids) != len(normalized_ids):
        raise ValueError("All party Lucids must belong to the current user.")
    OwnedLucid.objects.filter(owner=user).update(party_slot=None)
    lucid_by_id = {lucid.id: lucid for lucid in selected_lucids}
    for slot, lucid_id in enumerate(normalized_ids, start=1):
        lucid = lucid_by_id[lucid_id]
        lucid.party_slot = slot
        lucid.save(update_fields=["party_slot", "updated_at"])
    return list(get_party_queryset(user))

# ALARM FUNCTIONS

# Handles result of alarm check-in
@transaction.atomic
def apply_alarm_result(user, outcome):
    profile = get_or_create_profile(user)
    summary = {
        "outcome": outcome,
        "streak": profile.alarm_streak,
        "battle_charges": profile.battle_charges,
        "party_levelups_granted": 0,
    }
    # Increments streak (3 = level-up; 5 = battle charge)
    if outcome == ALARM_ON_TIME:
        profile.alarm_streak += 1
        if profile.alarm_streak % 3 == 0:
            leveled_party = grant_party_levelup(user)
            summary["party_levelups_granted"] = len(leveled_party)
        if profile.alarm_streak % 5 == 0:
            profile.battle_charges += 1
        profile.save(update_fields=["alarm_streak", "battle_charges", "updated_at"])
    # Breaks streak; de-levels party
    elif outcome == ALARM_LATE:
        profile.alarm_streak = 0
        profile.save(update_fields=["alarm_streak", "updated_at"])
        for lucid in get_party_queryset(user):
            level_down_lucid(lucid)
    elif outcome != ALARM_EARLY_NO_EFFECT:
        raise ValueError("Unknown alarm outcome.")
    summary["streak"] = profile.alarm_streak
    summary["battle_charges"] = profile.battle_charges
    return summary