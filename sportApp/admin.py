from django.contrib import admin

from sportApp.models import (
    Category, UniqueTournament, Tournament, Season,
    Player, Team, Match, MatchSet, MatchStatistics
)
# Register your models here.
admin.site.register(Player)
admin.site.register(Season)
admin.site.register(Tournament)
admin.site.register(Match)
admin.site.register(Category)
admin.site.register(UniqueTournament)
admin.site.register(Team)
admin.site.register(MatchSet)
admin.site.register(MatchStatistics)

