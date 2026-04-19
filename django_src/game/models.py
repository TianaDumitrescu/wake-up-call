from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

# Stores streak progress, battle charges, and starter species choice for each user
class PlayerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alarm_streak = models.PositiveIntegerField(default=0)
    battle_charges = models.PositiveIntegerField(default=0)
    starter_species_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username}'s game profile"

# Represents a Lucid owned by a player, including its species, level, upgrade history, and party status
class OwnedLucid(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_lucids",
    )
    species_id = models.PositiveIntegerField()
    level = models.PositiveIntegerField(default=1)
    upgrade_history = models.JSONField(default=list, blank=True)
    pending_levelups = models.PositiveIntegerField(default=0)
    party_slot = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("party_slot", "id")
        constraints = [
            models.CheckConstraint(
                check=Q(party_slot__isnull=True) | Q(party_slot__in=[1, 2, 3]),
                name="ownedlucid_valid_party_slot",
            ),
            models.UniqueConstraint(
                fields=("owner", "party_slot"),
                condition=Q(party_slot__isnull=False),
                name="ownedlucid_unique_party_slot_per_owner",
            ),
        ]
    def clean(self):
        if self.level < 1:
            raise ValidationError("Lucids cannot go below level 1.")

        if len(self.upgrade_history) > max(self.level - 1, 0):
            raise ValidationError("Upgrade history cannot exceed the Lucid's committed level.")
    def __str__(self):
        return f"OwnedLucid #{self.pk} for {self.owner.username}"

# Represents an active battle session for a player, including the enemy's species, level, HP, turn counts, and battle log
class BattleSession(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_AWAITING_SWITCH = "awaiting_switch"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_AWAITING_SWITCH, "Awaiting Switch"),
    ]
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="battle_session",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    enemy_species_id = models.PositiveIntegerField()
    enemy_level = models.PositiveIntegerField()
    enemy_upgrade_history = models.JSONField(default=list, blank=True)
    enemy_current_hp = models.PositiveIntegerField()
    player_turn_count = models.PositiveIntegerField(default=0)
    enemy_turn_count = models.PositiveIntegerField(default=0)
    active_party_lucid = models.ForeignKey(
        OwnedLucid,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Battle for {self.owner.username} vs {self.enemy_species_id}"

# Represents the state of each party Lucid during a battle, including current HP and reference to the battle and owned Lucid
class BattlePartyState(models.Model):
    battle = models.ForeignKey(
        BattleSession,
        on_delete=models.CASCADE,
        related_name="party_states",
    )
    owned_lucid = models.ForeignKey(
        OwnedLucid,
        on_delete=models.CASCADE,
        related_name="battle_states",
    )
    current_hp = models.PositiveIntegerField()

    class Meta:
        unique_together = ("battle", "owned_lucid")

    def __str__(self):
        return f"Battle state for {self.owned_lucid_id} in battle {self.battle_id}"