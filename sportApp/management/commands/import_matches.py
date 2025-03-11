import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from sportApp.models import (
    Category, UniqueTournament, Tournament, Season,
    Player, Team, Match, MatchSet, MatchStatistics
)

class Command(BaseCommand):
    help = "Заполняет базу данных матчами ITF за указанный период"

    def handle(self, *args, **kwargs):
        base_url = "https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/"
        start_date = datetime(2023, 2, 2)   # При желании можно оставить 3 февраля, если нужен ровно один день
        end_date = datetime(2023, 2, 3)
        delta = timedelta(days=1)

        while start_date <= end_date:
            url = f"{base_url}{start_date.strftime('%Y-%m-%d')}"
            print(f"Fetching data for {start_date.strftime('%Y-%m-%d')}...")
            self.parse_matches(url)
            start_date += delta

    def parse_matches(self, url):
        """
        Загружает и парсит список матчей за конкретный день.
        Сохраняет только ITF-матчи (или, например, Davis Cup, если это тоже ITF-соревнование).
        """
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            return

        data = response.json()
        events = data.get('events', [])

        for event in events:
            # 1) Проверяем, что турнир ITF (или Davis Cup под ITF)
            #    Здесь пример: ищем 'davis-cup' в slug
            #    В реальном коде это нужно адаптировать под ваши кейсы (например, 'itf' in slug).
            tournament_data = event.get('tournament', {})
            unique_tournament_data = tournament_data.get('uniqueTournament', {})
            category_data = tournament_data.get('category', {})

            # Примеры проверок (адаптируйте логику под реальные ITF-слуги/названия):
            # if 'itf' not in tournament_data.get('slug', '').lower():
            #     continue
            # Для демонстрации допустим, что Davis Cup — это ITF-турнир:
            if 'itf' not in tournament_data.get('slug', '').lower():
                continue

            # 2) Проверяем статус и дату начала матча:
            #    startTimestamp — это unix-время, преобразуем и проверяем точную дату, если нужно
            start_timestamp = event.get('startTimestamp')
            if not start_timestamp:
                continue
            match_date = datetime.utcfromtimestamp(start_timestamp)
            # Если нужно жёстко парсить только 3 февраля, раскомментируйте:
            # if match_date.date() != datetime(2023, 2, 3).date():
            #     continue

            # 3) Сохраняем/обновляем категорию
            category_slug = category_data.get('slug', '')
            category_obj, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={
                    'name': category_data.get('name', 'Unknown category'),
                }
            )

            # 4) Сохраняем/обновляем UniqueTournament
            ut_slug = unique_tournament_data.get('slug', '')
            unique_tournament_obj, _ = UniqueTournament.objects.get_or_create(
                slug=ut_slug,
                defaults={
                    'name': unique_tournament_data.get('name', 'Unknown unique tournament'),
                    'category': category_obj,
                    'groundType': unique_tournament_data.get('groundType', 'Unknown ground type'),
                }
            )

            # 5) Сохраняем/обновляем сам турнир
            tournament_name = tournament_data.get('name', 'Unknown tournament')
            tournament_slug = tournament_data.get('slug', '')
            tournament_api_id = tournament_data.get('id', None)

            tournament_obj, _ = Tournament.objects.get_or_create(
                slug=tournament_slug,
                api_id=tournament_api_id,
                defaults={
                    'name': tournament_name,
                    'category': category_obj,
                    'unique_tournament': unique_tournament_obj,
                    'priority': tournament_data.get('priority'),
                }
            )

            # 6) Сезон
            season_data = event.get('season', {})
            season_api_id = season_data.get('id', None)
            # Чтобы не было ошибок при отсутствии id:
            if not season_api_id:
                continue

            season_obj, _ = Season.objects.get_or_create(
                api_id=season_api_id,
                defaults={
                    'name': season_data.get('name', ''),
                    'year': season_data.get('year', '')
                }
            )

            # 7) Сохраняем команды (home/away)
            home_team_data = event.get('homeTeam', {})
            away_team_data = event.get('awayTeam', {})



            # -- Функция для создания/получения Player и Team
            def get_or_create_team(team_data):
                """
                Обрабатывает данные команды:
                - Если это doubles (type == 2) и присутствует список subTeams, то создаются отдельные записи для каждого игрока,
                  которые затем связываются с командой.
                - Для одиночных матчей создаётся один игрок.
                """
                # Для одиночных матчей создаём Player:
                team_api_id = team_data.get('id')
                team_name = team_data.get('name', '')
                team_slug = team_data.get('slug', '')
                team_type = team_data.get('type', 1)  # 1 - singles, 2 - doubles

                team_obj, created = Team.objects.get_or_create(
                    api_id=team_api_id,
                    defaults={'name': team_name, 'slug': team_slug}
                )

                if team_type == 2 and team_data.get('subTeams'):
                    # Обработка doubles: проходим по каждому подкомпоненту
                    for sub_team in team_data.get('subTeams', []):
                        player_api_id = sub_team.get('id')
                        player_name = sub_team.get('name', '')
                        player_slug = sub_team.get('slug', '')
                        short_name = sub_team.get('shortName', '')
                        country_info = sub_team.get('country', {})
                        country_name = country_info.get('name', '')
                        alpha2 = country_info.get('alpha2', '')

                        player_obj, _ = Player.objects.get_or_create(
                            api_id=player_api_id,
                            defaults={
                                'name': player_name,
                                'slug': player_slug,
                                'short_name': short_name,
                                'country_name': country_name,
                                'country_alpha2': alpha2
                            }
                        )
                        team_obj.players.add(player_obj)
                else:
                    # Одиночный случай или если subTeams отсутствуют
                    player_api_id = team_data.get('id')
                    player_name = team_data.get('name', '')
                    player_slug = team_data.get('slug', '')
                    short_name = team_data.get('shortName', '')
                    country_info = team_data.get('country', {})
                    country_name = country_info.get('name', '')
                    alpha2 = country_info.get('alpha2', '')

                    player_obj, _ = Player.objects.get_or_create(
                        api_id=player_api_id,
                        defaults={
                            'name': player_name,
                            'slug': player_slug,
                            'short_name': short_name,
                            'country_name': country_name,
                            'country_alpha2': alpha2
                        }
                    )
                    team_obj.players.add(player_obj)
                return team_obj

            home_team_obj = get_or_create_team(home_team_data)
            away_team_obj = get_or_create_team(away_team_data)

            # 8) Сохраняем/обновляем Match
            event_id = event.get('id')
            firstToServe = event.get('firstToServe', 0)
            round_info = event.get('roundInfo', {})
            roundName = round_info.get('name', "")
            roundType = round_info.get('round', 0)
            winner_code = event.get('winnerCode')
            status_info = event.get('status', {})
            status_code = status_info.get('code')
            status_description = status_info.get('description')

            match_obj, created_match = Match.objects.get_or_create(
                event_id=event_id,
                defaults={
                    'firstToServe': firstToServe,
                    'tournament': tournament_obj,
                    'season': season_obj,
                    'roundName': roundName,
                    'roundType': roundType,
                    'home_team': home_team_obj,
                    'away_team': away_team_obj,
                    'winner_code': winner_code,
                    'status_code': status_code,
                    'status_description': status_description,
                    'start_timestamp': match_date,  # datetime-объект
                }
            )
            # Если уже существовал, обновим данные (на случай изменения счёта, статуса и т.п.)
            if not created_match:
                match_obj.winner_code = winner_code
                match_obj.status_code = status_code
                match_obj.status_description = status_description
                match_obj.start_timestamp = match_date
                match_obj.save()

            # 9) Сохраняем счёт по сетам (из полей "period1", "period2" и т.д.)
            home_score = event.get('homeScore', {})
            away_score = event.get('awayScore', {})

            # Пример: если period1, period2... в homeScore/awayScore — это сеты.
            # Важно проверить, есть ли они в данных вообще.
            # Допустим, максимум 5 сетов в теннисе (BO5); пройдем по range(1,6).
            for set_number in range(1, 6):
                home_set_key = f"period{set_number}"
                away_set_key = f"period{set_number}"

                if home_set_key in home_score and away_set_key in away_score:
                    hs = home_score[home_set_key]
                    as_ = away_score[away_set_key]
                    if hs is not None and as_ is not None:
                        # Сохраняем/обновляем
                        # Если нет очков (0 или None), можно проверять, был ли сет
                        if hs == 0 and as_ == 0:
                            continue

                        # MatchSet
                        match_set_obj, _ = MatchSet.objects.get_or_create(
                            match=match_obj,
                            set_number=set_number,
                            defaults={
                                'home_score': hs,
                                'away_score': as_,
                            }
                        )
                        # Если уже было - обновим
                        match_set_obj.home_score = hs
                        match_set_obj.away_score = as_
                        match_set_obj.save()

            # 10) Парсим статистику, если есть (второй JSON) и сохраняем
            stats_data = self.get_match_statistics(match_id=event_id)
            if not stats_data:
                continue

            # У JSON вид: {"statistics": [ ... ]}
            stat_list = stats_data.get('statistics', [])
            for stat_block in stat_list:
                period = stat_block.get('period', 'ALL')
                groups = stat_block.get('groups', [])

                for group in groups:
                    group_name = group.get('groupName', '')
                    stats_items = group.get('statisticsItems', [])

                    for item in stats_items:
                        stat_name = item.get('name', '')
                        home_total = None
                        away_total = None
                        if item.get('homeTotal', None) is not None:
                            home_total = item.get('homeTotal')
                            away_total = item.get('awayTotal')
                        home_value = item.get('homeValue')
                        away_value = item.get('awayValue')
                        api_key = item.get('key', '')

                        # Сохраняем/обновляем запись MatchStatistics
                        ms_obj, _ = MatchStatistics.objects.get_or_create(
                            match=match_obj,
                            period=period,
                            group_name=group_name,
                            stat_name=stat_name,
                            defaults={
                                'home_value': home_value,
                                'away_value': away_value,
                                'home_Total': home_total,
                                'away_Total': away_total,
                                'api_key': api_key
                            }
                        )
                        # Если уже было, обновим
                        ms_obj.home_value = home_value
                        ms_obj.away_value = away_value
                        ms_obj.api_key = api_key
                        ms_obj.save()

    @staticmethod
    def get_match_statistics(match_id):
        """
        Возвращает JSON-данные со статистикой по конкретному матчу.
        """
        base_url = f"https://api.sofascore.com/api/v1/event/{match_id}/statistics"
        response = requests.get(base_url)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch statistics for match ID {match_id}: {response.status_code}")
            return None