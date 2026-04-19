from django.contrib import admin
from .models import BattlePartyState, BattleSession, OwnedLucid, PlayerProfile

# Registers core game models for debugging purpose
@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "alarm_streak", "battle_charges", "starter_species_id")

@admin.register(OwnedLucid)
class OwnedLucidAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "species_id", "level", "party_slot", "pending_levelups")
    list_filter = ("party_slot",)
    search_fields = ("owner__username",)

@admin.register(BattleSession)
class BattleSessionAdmin(admin.ModelAdmin):
    list_display = ("owner", "status", "enemy_species_id", "enemy_level", "active_party_lucid")

@admin.register(BattlePartyState)
class BattlePartyStateAdmin(admin.ModelAdmin):
    list_display = ("battle", "owned_lucid", "current_hp")