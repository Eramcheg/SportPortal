from django.contrib import admin

from sportApp.models import Player, Match, Set, Game, Tournament

# Register your models here.
admin.site.register(Player)
admin.site.register(Match)
admin.site.register(Set)
admin.site.register(Game)