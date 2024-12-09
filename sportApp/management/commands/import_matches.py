import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sportApp.models import Tournament, Player, Match, Set, Team


class Command(BaseCommand):
    help = "Заполняет базу данных матчами ITF за февраль 2023 года"

    def handle(self, *args, **kwargs):
        base_url = "https://api.sofascore.com/api/v1/sport/tennis/scheduled-events"
        start_date = datetime(2023, 2, 1)
        end_date = datetime(2023, 2, 28)
        delta = timedelta(days=1)

        while start_date <= end_date:
            url = f"{base_url}/{start_date.strftime('%Y-%m-%d')}"
            print(f"Fetching data for {start_date.strftime('%Y-%m-%d')}...")
            self.parse_matches(url)
            start_date += delta

    def create_team(self, team_data):
        """
        Создает или получает команду и её игроков.
        :param team_data: Данные о команде из JSON.
        :return: Объект Team.
        """
        team_name = team_data['name']  # Например: "Player A / Player B"
        player_names = team_name.split(" / ")  # Разделяем имена

        # Создаём игроков
        players = []
        for player_name in player_names:
            player, _ = Player.objects.get_or_create(name=player_name)
            players.append(player)

        # Создаём или получаем команду
        team, _ = Team.objects.get_or_create(name=team_name)
        team.players.set(players)  # Устанавливаем связь с игроками
        return team

    def parse_matches(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data from {url}")
            return

        data = response.json()
        matches = data.get('events', [])

        for match_data in matches:
            # Tournament

            print(f"MATCH DATA: {match_data}" )

            tournament_data = match_data['tournament']

            # Фильтруем только турниры ITF
            tournament_category = tournament_data['category']['name']
            if "ITF" not in tournament_category:
                print(f"Skipping non-ITF tournament: {tournament_data['name']}")
                continue

            tournament, _ = Tournament.objects.get_or_create(
                name=tournament_data['name'],
                category=tournament_category,
                ground_type=tournament_data.get('uniqueTournament', {}).get('groundType', None)
            )

            # Players
            home_team = self.create_team(match_data['homeTeam'])
            away_team = self.create_team(match_data['awayTeam'])

            # Победитель
            winner = None
            if 'winnerCode' in match_data:
                winner = home_team if match_data['winnerCode'] == 1 else away_team

            # Дата матча
            start_time = datetime.fromtimestamp(match_data['startTimestamp'])

            # Фильтрация по дате
            if start_time.month != 2 or start_time.year != 2023:
                print(f"Skipping match on {start_time.strftime('%Y-%m-%d')}")
                continue

            # Match
            match, created = Match.objects.get_or_create(
                tournament=tournament,
                home_team=home_team,
                away_team=away_team,
                start_time=start_time,
                defaults={
                    'winner': winner,
                    'round_name': match_data['roundInfo']['name'],
                    'status': match_data['status']['description']
                }
            )

            if not created:
                print(f"Match {match} already exists, skipping.")

            # Sets
            home_score = match_data['homeScore']
            away_score = match_data['awayScore']
            for i in range(1, 6):
                home_set_score = home_score.get(f'period{i}')
                away_set_score = away_score.get(f'period{i}')
                if home_set_score is not None and away_set_score is not None:
                    Set.objects.get_or_create(
                        match=match,
                        set_number=i,
                        defaults={
                            'home_score': home_set_score,
                            'away_score': away_set_score
                        }
                    )