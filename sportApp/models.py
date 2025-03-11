from datetime import datetime

from django.db import models

# ---- Справочник категорий (например, "ITF", "WTA", "Davis Cup" и т.п.) ----
class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    # Доп. поля, если нужно: страна, флаг и проч.

    def __str__(self):
        return self.name

# ---- Справочник уникальных турниров (например, ITF) ----
class UniqueTournament(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    groundType = models.CharField(max_length=255)

    # Можно добавить флаги, страны и прочие поля при необходимости
    # Например, userCount, hasPerformanceGraphFeature, ид из API и т.д.

    def __str__(self):
        return f"{self.name} ({self.category.name})"

# ---- Турнир. Например, "Davis Cup Single Matches 2023" ----
class Tournament(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    unique_tournament = models.ForeignKey(UniqueTournament, on_delete=models.PROTECT, null=True, blank=True)
    priority = models.IntegerField(null=True, blank=True)
    # При желании можно хранить id из API (например, 294 для Davis Cup и т.д.)
    api_id = models.IntegerField(unique=True,null=True, blank=True)

    class Meta:
        unique_together = ("name", "slug", "api_id")

    def __str__(self):
        return self.name

# ---- Сезон (например, "2023", "Davis Cup 2023" и т.д.) ----
class Season(models.Model):
    name = models.CharField(max_length=255)  # "Davis Cup 2023"
    year = models.CharField(max_length=10, null=True, blank=True)
    # id из API при желании
    api_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

# ---- Игрок (для одиночных матчей) ----
class Player(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=255, null=True, blank=True)
    country_alpha2 = models.CharField(max_length=10, null=True, blank=True)
    country_name = models.CharField(max_length=255, null=True, blank=True)
    # Если из API есть некий уникальный ID для игрока:
    api_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

# ---- Команда (на случай если понадобится парсить пары в парном разряде) ----
# Но даже для одиночки логично держать эту модель, чтобы всегда иметь "home_team" / "away_team".
class Team(models.Model):
    # Если одиночный разряд, будет 1 игрок. Если парный – двое и т.д.
    players = models.ManyToManyField(Player, related_name='teams')
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=False)  # Бывает, что slug у игрока повторяется, но для команды можно хранить иначе
    api_id = models.IntegerField(unique=True)  # Например, 198223 (Fomin S.) или 63438 (McDonald M.)

    # Признак, что это "сборная"/"национальная команда" и т.п. – если потребуется
    # country_alpha2 = ...
    # etc.

    def __str__(self):
        return self.name

# ---- Матч ----
class Match(models.Model):
    # Уникальный идентификатор события из API (например, "id": 11034695)
    event_id = models.IntegerField(unique=True, default=0)
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, null=True, blank=True)
    firstToServe = models.IntegerField(null=True, blank=True)
    roundName = models.CharField(max_length=255, null=True, blank=True)
    roundType = models.IntegerField(null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.PROTECT, null=True, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_home', null=True, blank=True)
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='matches_away', null=True, blank=True)
    winner_code = models.PositiveSmallIntegerField(null=True, blank=True)  # 1 (home), 2 (away)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)  # API status code (100 = ended)
    status_description = models.CharField(max_length=255, null=True, blank=True)
    start_timestamp = models.DateTimeField(null=True, blank=True)  # Можно преобразовать из unix timestamp
    # Доп. поля для финального счёта и т.д.

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.event_id})"

# ---- Сеты (чтобы хранить, например, счёт по каждому сету) ----
class MatchSet(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField()  # 1, 2, 3 и т.д.
    home_score = models.PositiveIntegerField()
    away_score = models.PositiveIntegerField()

    class Meta:
        unique_together = ("match", "set_number")

    def __str__(self):
        return f"Set {self.set_number} of match {self.match.event_id}"

# ---- Общая модель для статистики по матчу (разбивка по периодам и группам) ----
class MatchStatistics(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='statistics')
    period = models.CharField(max_length=50)  # "ALL", "1ST", "2ND", "3RD" и т.д.
    group_name = models.CharField(max_length=100)  # "Service", "Points", "Games", "Return", "Miscellaneous"
    stat_name = models.CharField(max_length=255)   # "Aces", "Double faults", ...
    home_value = models.FloatField(null=True, blank=True)
    away_value = models.FloatField(null=True, blank=True)
    home_Total = models.FloatField(null=True, blank=True)
    away_Total = models.FloatField(null=True, blank=True)
    # Если нужно хранить ещё и "homeTotal", "awayTotal" или проценты – можете добавить поля:
    # home_total = models.FloatField(null=True, blank=True)
    # away_total = models.FloatField(null=True, blank=True)
    # Можно хранить и "compareCode", если потребуется.
    # Ключ (key) из API, например "aces", "doubleFaults" и т.д.
    api_key = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        # Если на уровне периода + group_name + stat_name уже не должно быть дублей –
        # можно добавить такую уникальность:
        unique_together = ("match", "period", "group_name", "stat_name")

    def __str__(self):
        return f"{self.match.event_id} | {self.period} | {self.group_name} | {self.stat_name}"
