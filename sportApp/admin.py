from django.contrib import admin

from sportApp.models import Tournament, Season, Player, Match, Score, Statistic, Team

# Register your models here.
admin.site.register(Player)
admin.site.register(Season)
admin.site.register(Tournament)
admin.site.register(Match)
admin.site.register(Score)
admin.site.register(Statistic)
admin.site.register(Team)
