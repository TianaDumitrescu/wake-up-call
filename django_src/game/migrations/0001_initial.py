import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q

# Initial migration that creates all game models and constraints
class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="OwnedLucid",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("species_id", models.PositiveIntegerField()),
                ("level", models.PositiveIntegerField(default=1)),
                ("upgrade_history", models.JSONField(blank=True, default=list)),
                ("pending_levelups", models.PositiveIntegerField(default=0)),
                ("party_slot", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owned_lucids", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("party_slot", "id"),
            },
        ),
        migrations.CreateModel(
            name="PlayerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alarm_streak", models.PositiveIntegerField(default=0)),
                ("battle_charges", models.PositiveIntegerField(default=0)),
                ("starter_species_id", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BattleSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("active", "Active"), ("awaiting_switch", "Awaiting Switch")], default="active", max_length=32)),
                ("enemy_species_id", models.PositiveIntegerField()),
                ("enemy_level", models.PositiveIntegerField()),
                ("enemy_upgrade_history", models.JSONField(blank=True, default=list)),
                ("enemy_current_hp", models.PositiveIntegerField()),
                ("player_turn_count", models.PositiveIntegerField(default=0)),
                ("enemy_turn_count", models.PositiveIntegerField(default=0)),
                ("log", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("active_party_lucid", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="game.ownedlucid")),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="battle_session", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BattlePartyState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("current_hp", models.PositiveIntegerField()),
                ("battle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="party_states", to="game.battlesession")),
                ("owned_lucid", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="battle_states", to="game.ownedlucid")),
            ],
            options={
                "unique_together": {("battle", "owned_lucid")},
            },
        ),
        migrations.AddConstraint(
            model_name="ownedlucid",
            constraint=models.CheckConstraint(
                check=Q(party_slot__isnull=True) | Q(party_slot__in=[1, 2, 3]),
                name="ownedlucid_valid_party_slot",
            ),
        ),
        migrations.AddConstraint(
            model_name="ownedlucid",
            constraint=models.UniqueConstraint(
                condition=Q(party_slot__isnull=False),
                fields=("owner", "party_slot"),
                name="ownedlucid_unique_party_slot_per_owner",
            ),
        ),
    ]