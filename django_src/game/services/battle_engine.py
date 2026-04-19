import random
from django.db import transaction
from game.models import BattlePartyState, BattleSession, OwnedLucid
from .lucid_data import get_species
from .progression import get_or_create_profile, get_party_queryset
from .spawn import build_enemy_upgrade_history, choose_wild_species, determine_enemy_level
from .stats import calculate_damage, calculate_stats
from .type_chart import get_multiplier

# A template of this .py file was written by Codex

# Utility function to serialize battle state (FOR FRONTEND)
def serialize_owned_lucid(owned_lucid, current_hp=None):
    species = get_species(owned_lucid.species_id)
    stats = calculate_stats(owned_lucid.species_id, owned_lucid.upgrade_history)
    payload = {
        "owned_id": owned_lucid.id,
        "species_id": owned_lucid.species_id,
        "name": species["name"],
        "types": species["type"],
        "level": owned_lucid.level,
        "party_slot": owned_lucid.party_slot,
        "pending_levelups": owned_lucid.pending_levelups,
        "stats": stats,
        "current_hp": stats["hp"] if current_hp is None else current_hp,
    }
    return payload

# Utility function to serialize entire battle session (FOR FRONTEND)
def serialize_battle_session(session):
    enemy_species = get_species(session.enemy_species_id)
    enemy_stats = calculate_stats(session.enemy_species_id, session.enemy_upgrade_history)
    states = {
        state.owned_lucid_id: state
        for state in session.party_states.select_related("owned_lucid").all()
    }
    party_payload = []
    for owned_lucid in OwnedLucid.objects.filter(id__in=states.keys()).order_by("party_slot", "id"):
        state = states[owned_lucid.id]
        payload = serialize_owned_lucid(owned_lucid, current_hp=state.current_hp)
        payload["is_active"] = session.active_party_lucid_id == owned_lucid.id
        payload["is_fainted"] = state.current_hp == 0
        party_payload.append(payload)
    return {
        "status": session.status,
        "enemy": {
            "species_id": session.enemy_species_id,
            "name": enemy_species["name"],
            "types": enemy_species["type"],
            "level": session.enemy_level,
            "stats": enemy_stats,
            "current_hp": session.enemy_current_hp,
        },
        "party": party_payload,
        "active_party_lucid_id": session.active_party_lucid_id,
        "log": session.log,
    }

# Getter for current battle session for user
def get_active_battle(user):
    return (
        BattleSession.objects.filter(owner=user)
        .select_related("active_party_lucid")
        .prefetch_related("party_states__owned_lucid")
        .first()
    )

# Helper function to append msg to battle log and save session
def _append_log(session, message):
    log = list(session.log)
    log.append(message)
    session.log = log

# Helper function to get BattlePartyState for specific Lucid in session
def _get_party_state(session, owned_lucid_id):
    return session.party_states.select_related("owned_lucid").get(owned_lucid_id=owned_lucid_id)

# Helper function to get BattlePartyState for currently active Lucid in session
def _get_active_party_state(session):
    if session.active_party_lucid_id is None:
        return None
    return _get_party_state(session, session.active_party_lucid_id)

# Determines turn based on (turn count * speed) with random tiebreaker
def _next_actor(session, player_speed, enemy_speed):
    player_score = (session.player_turn_count + 1) * enemy_speed
    enemy_score = (session.enemy_turn_count + 1) * player_speed
    if player_score < enemy_score:
        return "player"
    if enemy_score < player_score:
        return "enemy"
    return random.choice(["player", "enemy"])

# Determines best attack for enemy to use
def _best_enemy_attack_type(enemy_types, defender_types):
    best_type = enemy_types[0]
    best_multiplier = get_multiplier(best_type, defender_types)
    for attack_type in enemy_types[1:]:
        multiplier = get_multiplier(attack_type, defender_types)
        if multiplier > best_multiplier:
            best_type = attack_type
            best_multiplier = multiplier
    return best_type

# Resolves enemy turn and returns result if battle ends or switch is required
def _resolve_enemy_turn(session):
    active_state = _get_active_party_state(session)
    if active_state is None or active_state.current_hp == 0:
        session.status = BattleSession.STATUS_AWAITING_SWITCH
        session.save(update_fields=["status", "updated_at"])
        return None
    enemy_species = get_species(session.enemy_species_id)
    enemy_stats = calculate_stats(session.enemy_species_id, session.enemy_upgrade_history)
    defender_species = get_species(active_state.owned_lucid.species_id)
    attack_type = _best_enemy_attack_type(enemy_species["type"], defender_species["type"])
    multiplier = get_multiplier(attack_type, defender_species["type"])
    damage = calculate_damage(enemy_stats["attack"], multiplier)
    active_state.current_hp = max(active_state.current_hp - damage, 0)
    active_state.save(update_fields=["current_hp"])
    session.enemy_turn_count += 1
    _append_log(
        session,
        f"{enemy_species['name']} used {attack_type} for {damage} damage.",
    )
    session.save(update_fields=["enemy_turn_count", "log", "updated_at"])
    if active_state.current_hp == 0:
        _append_log(session, f"{defender_species['name']} fainted.")
        alive_exists = session.party_states.exclude(owned_lucid_id=active_state.owned_lucid_id).filter(current_hp__gt=0).exists()
        if alive_exists:
            session.status = BattleSession.STATUS_AWAITING_SWITCH
            session.save(update_fields=["status", "log", "updated_at"])
            return {"result": "awaiting_switch", "battle": serialize_battle_session(session)}
        return _finish_loss(session)
    return None

# Advances battle state until it's player's turn or battle ends (Done only after player actions or battle starts)
def _advance_until_player_turn(session):
    while session.status == BattleSession.STATUS_ACTIVE:
        active_state = _get_active_party_state(session)
        if active_state is None or active_state.current_hp == 0:
            session.status = BattleSession.STATUS_AWAITING_SWITCH
            session.save(update_fields=["status", "updated_at"])
            break
        player_stats = calculate_stats(active_state.owned_lucid.species_id, active_state.owned_lucid.upgrade_history)
        enemy_stats = calculate_stats(session.enemy_species_id, session.enemy_upgrade_history)
        if _next_actor(session, player_stats["speed"], enemy_stats["speed"]) == "player":
            break
        result = _resolve_enemy_turn(session)
        if result is not None:
            return result
    return {"result": "ongoing", "battle": serialize_battle_session(session)}

# Handles battle end on player victory, granting Lucid to player and deleting session
def _finish_victory(session):
    caught_lucid = OwnedLucid.objects.create(
        owner=session.owner,
        species_id=session.enemy_species_id,
        level=1,
        upgrade_history=[],
        pending_levelups=0,
        party_slot=None,
    )
    result = {
        "result": "victory",
        "caught": serialize_owned_lucid(caught_lucid),
    }
    session.delete()
    return result

# Handles battle end on player loss, just deleting session
def _finish_loss(session):
    session.delete()
    return {"result": "loss"}

# Same as loss but for when player runs away
def _finish_run(session):
    session.delete()
    return {"result": "ran"}

# MAIN PUBLIC FUNCTIONS FOR BATTLE FLOW

# Starts a new battle for the given user
    # Checks battle charges, no active battle, valid party, then spawns enemy and records battle session
@transaction.atomic
def start_battle(user):
    profile = get_or_create_profile(user)
    if profile.battle_charges < 1:
        raise ValueError("No battle charges are available.")
    if BattleSession.objects.filter(owner=user).exists():
        raise ValueError("A battle is already in progress.")
    party = list(get_party_queryset(user))
    if not party:
        raise ValueError("You need at least one Lucid in your party to battle.")
    if any(lucid.pending_levelups > 0 for lucid in party):
        raise ValueError("Resolve all pending level-ups before starting a battle.")
    wild_species = choose_wild_species()
    enemy_level = determine_enemy_level(party, wild_species)
    enemy_upgrade_history = build_enemy_upgrade_history(enemy_level)
    enemy_stats = calculate_stats(wild_species["id"], enemy_upgrade_history)
    profile.battle_charges -= 1
    profile.save(update_fields=["battle_charges", "updated_at"])
    session = BattleSession.objects.create(
        owner=user,
        enemy_species_id=wild_species["id"],
        enemy_level=enemy_level,
        enemy_upgrade_history=enemy_upgrade_history,
        enemy_current_hp=enemy_stats["hp"],
        active_party_lucid=party[0],
        log=[f"A wild {wild_species['name']} appeared."],
    )
    party_states = []
    for lucid in party:
        current_stats = calculate_stats(lucid.species_id, lucid.upgrade_history)
        party_states.append(
            BattlePartyState(
                battle=session,
                owned_lucid=lucid,
                current_hp=current_stats["hp"],
            )
        )
    BattlePartyState.objects.bulk_create(party_states)
    return _advance_until_player_turn(session)

# If user selects "Attack"
    # Validates turn order, calculates damage, updates battle state, and checks for end of battle
@transaction.atomic
def player_attack(user, attack_type_index):
    session = get_active_battle(user)
    if session is None:
        raise ValueError("No active battle was found.")
    if session.status != BattleSession.STATUS_ACTIVE:
        raise ValueError("You must switch Lucids before attacking.")
    attack_type_index = int(attack_type_index)
    active_state = _get_active_party_state(session)
    if active_state is None or active_state.current_hp == 0:
        raise ValueError("Choose an active Lucid before attacking.")
    player_species = get_species(active_state.owned_lucid.species_id)
    if attack_type_index < 0 or attack_type_index >= len(player_species["type"]):
        raise ValueError("Invalid attack choice.")
    player_stats = calculate_stats(active_state.owned_lucid.species_id, active_state.owned_lucid.upgrade_history)
    enemy_species = get_species(session.enemy_species_id)
    enemy_stats = calculate_stats(session.enemy_species_id, session.enemy_upgrade_history)
    if _next_actor(session, player_stats["speed"], enemy_stats["speed"]) != "player":
        raise ValueError("It is not the player's turn.")
    attack_type = player_species["type"][attack_type_index]
    multiplier = get_multiplier(attack_type, enemy_species["type"])
    damage = calculate_damage(player_stats["attack"], multiplier)
    session.enemy_current_hp = max(session.enemy_current_hp - damage, 0)
    session.player_turn_count += 1
    _append_log(session, f"{player_species['name']} used {attack_type} for {damage} damage.")
    session.save(update_fields=["enemy_current_hp", "player_turn_count", "log", "updated_at"])
    if session.enemy_current_hp == 0:
        _append_log(session, f"{enemy_species['name']} fainted.")
        session.save(update_fields=["log", "updated_at"])
        return _finish_victory(session)
    return _advance_until_player_turn(session)

# If user selects "Switch"
    # Validates chosen Lucid, updates active Lucid, and checks if enemy gets free
@transaction.atomic
def player_switch(user, owned_lucid_id):
    session = get_active_battle(user)
    if session is None:
        raise ValueError("No active battle was found.")
    target_state = _get_party_state(session, int(owned_lucid_id))
    if target_state.current_hp == 0:
        raise ValueError("You cannot switch to a fainted Lucid.")
    if session.status == BattleSession.STATUS_ACTIVE and session.active_party_lucid_id == target_state.owned_lucid_id:
        raise ValueError("That Lucid is already active.")
    session.active_party_lucid = target_state.owned_lucid
    session.status = BattleSession.STATUS_ACTIVE
    session.player_turn_count = 0
    session.enemy_turn_count = 0
    _append_log(session, f"Switched to {get_species(target_state.owned_lucid.species_id)['name']}.")
    session.save(update_fields=["active_party_lucid", "status", "player_turn_count", "enemy_turn_count", "log", "updated_at"])
    free_turn_result = _resolve_enemy_turn(session)
    if free_turn_result is not None:
        if free_turn_result["result"] == "awaiting_switch":
            session.player_turn_count = 0
            session.enemy_turn_count = 0
            session.save(update_fields=["player_turn_count", "enemy_turn_count", "updated_at"])
            return {"result": "awaiting_switch", "battle": serialize_battle_session(session)}
        return free_turn_result
    session.player_turn_count = 0
    session.enemy_turn_count = 0
    session.save(update_fields=["player_turn_count", "enemy_turn_count", "updated_at"])
    return _advance_until_player_turn(session)

# If user selects "Run"
    # Ends battle with "ran" result
@transaction.atomic
def player_run(user):
    session = get_active_battle(user)
    if session is None:
        raise ValueError("No active battle was found.")
    return _finish_run(session)