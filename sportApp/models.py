from datetime import datetime

from django.db import models

# Create your models here.
class Player(models.Model):
    """Информация об игроках."""
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    """Информация о командах (для парных матчей)."""
    name = models.CharField(max_length=200)  # Имя команды, например, "Player A / Player B"
    players = models.ManyToManyField(Player, related_name="teams")  # Связь с игроками

    def __str__(self):
        return self.name


class Tournament(models.Model):
    """Информация о турнирах."""
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    ground_type = models.CharField(max_length=100, null=True, blank=True)
    season_name = models.CharField(max_length=200, null=True, blank=True)
    season_year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    """Информация о матчах."""
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    home_team = models.ForeignKey(Team, related_name="home_matches", on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name="away_matches", on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="wins", null=True, blank=True)
    round_name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

class Set(models.Model):
    """Информация о сетах в матче."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="sets")
    set_number = models.IntegerField()
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    def __str__(self):
        return f"Set {self.set_number} of Match {self.match}"


class Game(models.Model):
    """Информация о геймах (опционально)."""
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name="games")
    game_number = models.IntegerField()
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    def __str__(self):
        return f"Game {self.game_number} of Set {self.set}"