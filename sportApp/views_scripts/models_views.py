import math

from django.shortcuts import render
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from sportApp.models import (
    Category, UniqueTournament, Tournament, Season,
    Player, Team, Match, MatchSet, MatchStatistics
)

def match_list(request):
    matches = Match.objects.all().order_by('-start_timestamp')
    return render(request, 'pages/match_list.html', {'matches': matches})


def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    # Получаем все статистические записи для матча
    stats_qs = match.statistics.all()

    # Группируем статистику по периоду и затем по группе
    grouped = {}
    for stat in stats_qs:
        period = stat.period
        group = stat.group_name
        if period not in grouped:
            grouped[period] = {}
        if group not in grouped[period]:
            grouped[period][group] = []
        grouped[period][group].append({
            "name": stat.stat_name,
            "home_value": int(stat.home_value),
            "away_value": int(stat.away_value),
            "home_total": int(stat.home_Total) if stat.home_Total is not None else None,
            "away_total": int(stat.away_Total) if stat.away_Total is not None else None,
            "home_percent": calc_percent(stat.home_value,
                                         int(stat.home_Total)) if stat.home_Total is not None else "N/A",
            "away_percent": calc_percent(stat.away_value,
                                         int(stat.away_Total)) if stat.away_Total is not None else "N/A",
        })

    # Преобразуем сгруппированные данные в список для удобства обработки в шаблоне
    statistics_data = []
    for period, groups in grouped.items():
        period_obj = {
            "period": period,
            "groups": [],
        }
        for group_name, statistics_items in groups.items():
            period_obj["groups"].append({
                "groupName": group_name,
                "statisticsItems": statistics_items,
            })
        statistics_data.append(period_obj)

    return render(request, 'pages/match_detail.html', {
        'match': match,
        'statistics_data': statistics_data
    })

def calc_percent(value, total):
    if total is None or total == 0:
        return "N/A"
    return f"{math.floor((float(value) / total) * 100)}%"

def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    return render(request, 'pages/team_detail.html', {'team': team})

def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return render(request, 'pages/player_detail.html', {'player': player})

