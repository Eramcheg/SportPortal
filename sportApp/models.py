from datetime import datetime

from django.db import models

# Create your models here.


class Tournament(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=255)  # Например, Davis Cup
    country = models.CharField(max_length=255, blank=True, null=True)
    sport = models.CharField(max_length=255, default="Tennis")

    def __str__(self):
        return self.name


class Season(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=255)
    year = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.tournament.name} - {self.year}"


class Player(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    birthdate = models.CharField(max_length=100, blank=True, null=True)
    plays = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    players = models.ManyToManyField(Player)

    def __str__(self):
        return self.name


class Match(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="matches")
    home_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="home_matches", null=True, blank=True)
    away_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="away_matches", null=True, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_matches", null=True, blank=True)
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_matches", null=True, blank=True)
    status = models.CharField(max_length=50)
    start_timestamp = models.DateTimeField()
    winner_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="wins")
    winner_player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="player_wins")
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.slug


class Score(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="score")
    home_total = models.IntegerField()
    away_total = models.IntegerField()
    period_scores = models.JSONField()

    def __str__(self):
        return f"Score: {self.home_total} - {self.away_total}"


class Statistic(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="statistics")
    group_name = models.CharField(max_length=255)  # Example: "Service", "Points"
    key = models.CharField(max_length=100)  # Example: "aces", "double_faults"
    home_value = models.FloatField()
    away_value = models.FloatField()

    def __str__(self):
        return f"{self.group_name}: {self.key} ({self.match})"