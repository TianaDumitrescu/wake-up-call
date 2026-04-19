import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import BattlePartyState, OwnedLucid
from .services import battle_engine
from .services.lucid_data import get_species
from .services.progression import (
    STARTER_SPECIES_IDS,
    apply_level_choice,
    choose_starter,
    get_or_create_profile,
    set_party,
)

# Used Codex for some helper functions and syntax/error handling

# Normalizes request data
def _request_data(request):
    if request.content_type and request.content_type.startswith("application/json") and request.body:
        return json.loads(request.body.decode("utf-8"))
    return request.POST

# Error response formatter
def _error_response(message, status=400):
    return JsonResponse({"error": message}, status=status)

# Returns starter options and whether user already chose
@login_required
@require_GET
def starter_options(request):
    profile = get_or_create_profile(request.user)
    options = [get_species(species_id) for species_id in sorted(STARTER_SPECIES_IDS)]
    return JsonResponse(
        {
            "starter_chosen": profile.starter_species_id is not None,
            "starter_species_id": profile.starter_species_id,
            "options": options,
        }
    )

# Returns unique starter based on user's choice
@login_required
@require_POST
def choose_starter_view(request):
    data = _request_data(request)
    species_id = data.get("species_id")
    if species_id is None:
        return _error_response("species_id is required.")

    try:
        starter = choose_starter(request.user, species_id)
    except ValueError as exc:
        return _error_response(str(exc))

    return JsonResponse({"starter": battle_engine.serialize_owned_lucid(starter)})

# Returns user's full collection of Lucids
@login_required
@require_GET
def collection_view(request):
    owned_lucids = OwnedLucid.objects.filter(owner=request.user).order_by("party_slot", "id")
    payload = [battle_engine.serialize_owned_lucid(lucid) for lucid in owned_lucids]
    return JsonResponse({"collection": payload})

# Returns user's current party of Lucids (ordered)
@login_required
@require_GET
def party_view(request):
    party = OwnedLucid.objects.filter(owner=request.user, party_slot__isnull=False).order_by("party_slot")
    payload = [battle_engine.serialize_owned_lucid(lucid) for lucid in party]
    return JsonResponse({"party": payload})

# Sets user's party based on provided list of owned Lucid IDs (ordered)
@login_required
@require_POST
def set_party_view(request):
    data = _request_data(request)
    lucid_ids = data.get("owned_lucid_ids", [])
    if isinstance(lucid_ids, str):
        lucid_ids = [lucid_id for lucid_id in lucid_ids.split(",") if lucid_id]
    try:
        party = set_party(request.user, lucid_ids)
    except ValueError as exc:
        return _error_response(str(exc))

    payload = [battle_engine.serialize_owned_lucid(lucid) for lucid in party]
    return JsonResponse({"party": payload})

# Applies level-up stat choice to Lucid
@login_required
@require_POST
def apply_level_choice_view(request):
    data = _request_data(request)
    owned_lucid_id = data.get("owned_lucid_id")
    stat_choice = data.get("stat_choice")
    if owned_lucid_id is None or stat_choice is None:
        return _error_response("owned_lucid_id and stat_choice are required.")
    try:
        lucid = OwnedLucid.objects.get(id=int(owned_lucid_id), owner=request.user)
        lucid = apply_level_choice(lucid, stat_choice)
    except (OwnedLucid.DoesNotExist, ValueError) as exc:
        return _error_response(str(exc), status=404 if isinstance(exc, OwnedLucid.DoesNotExist) else 400)
    return JsonResponse({"lucid": battle_engine.serialize_owned_lucid(lucid)})

# Starts up battle
@login_required
@require_POST
def start_battle_view(request):
    try:
        result = battle_engine.start_battle(request.user)
    except ValueError as exc:
        return _error_response(str(exc))
    return JsonResponse(result)

# Returns current battle state (no advancing)
@login_required
@require_GET
def battle_state_view(request):
    session = battle_engine.get_active_battle(request.user)
    if session is None:
        return _error_response("No active battle was found.", status=404)
    return JsonResponse({"result": "ongoing", "battle": battle_engine.serialize_battle_session(session)})

# Returns updated battle state after attack
@login_required
@require_POST
def battle_fight_view(request):
    data = _request_data(request)
    attack_type_index = data.get("attack_type_index")
    if attack_type_index is None:
        return _error_response("attack_type_index is required.")
    try:
        result = battle_engine.player_attack(request.user, attack_type_index)
    except ValueError as exc:
        return _error_response(str(exc))
    return JsonResponse(result)

# Returns updated battle state after switch
@login_required
@require_POST
def battle_switch_view(request):
    data = _request_data(request)
    owned_lucid_id = data.get("owned_lucid_id")
    if owned_lucid_id is None:
        return _error_response("owned_lucid_id is required.")
    try:
        result = battle_engine.player_switch(request.user, owned_lucid_id)
    except (BattlePartyState.DoesNotExist, ValueError) as exc:
        return _error_response(str(exc), status=404 if isinstance(exc, BattlePartyState.DoesNotExist) else 400)
    return JsonResponse(result)

# Returns updated battle state after run
@login_required
@require_POST
def battle_run_view(request):
    try:
        result = battle_engine.player_run(request.user)
    except ValueError as exc:
        return _error_response(str(exc))
    return JsonResponse(result)