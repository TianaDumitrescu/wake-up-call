from django.urls import path
from . import views

urlpatterns = [
    path("starter/", views.starter_options, name="starter_options"),
    path("starter/choose/", views.choose_starter_view, name="choose_starter"),
    path("party/", views.party_view, name="party_view"),
    path("party/set/", views.set_party_view, name="set_party"),
    path("collection/", views.collection_view, name="collection_view"),
    path("level-up/", views.apply_level_choice_view, name="apply_level_choice"),
    path("battle/start/", views.start_battle_view, name="start_battle"),
    path("battle/", views.battle_state_view, name="battle_state"),
    path("battle/fight/", views.battle_fight_view, name="battle_fight"),
    path("battle/switch/", views.battle_switch_view, name="battle_switch"),
    path("battle/run/", views.battle_run_view, name="battle_run"),
]
