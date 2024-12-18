import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sportApp.models import Tournament, Season, Player, Match, Score, Statistic, Team


class Command(BaseCommand):
    help = "Заполняет базу данных матчами ITF за указанный период"

    def handle(self, *args, **kwargs):
        base_url = "https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/"
        start_date = datetime(2023, 2, 2)
        end_date = datetime(2023, 2, 3)
        delta = timedelta(days=1)

        while start_date <= end_date:
            url = f"{base_url}{start_date.strftime('%Y-%m-%d')}"
            print(f"Fetching data for {start_date.strftime('%Y-%m-%d')}...")
            self.parse_matches(url)
            start_date += delta

    def parse_matches(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("events", [])
            for match_data in matches:
                tournament_data = match_data.get("tournament", {})
                if "ITF" in tournament_data.get("category", {}).get("name", ""):
                    self.save_match_data(match_data)
        else:
            print(f"Failed to fetch matches: {response.status_code}")

    def save_match_data(self, match_data):
        # Save Tournament
        tournament_data = match_data["tournament"]
        tournament, _ = Tournament.objects.get_or_create(
            name=tournament_data["name"],
            slug=tournament_data["slug"],
            category=tournament_data["category"]["name"],
        )
        season_data = match_data["season"]
        season, _ = Season.objects.get_or_create(
            tournament=tournament,
            name=season_data["name"],
            year=int(season_data["year"]),
        )

        # Check if it's a team match
        if match_data["homeTeam"]["type"] == 2:
            # Save Teams
            home_team, _ = Team.objects.get_or_create(
                name=match_data["homeTeam"]["name"], slug=match_data["homeTeam"]["slug"]
            )
            away_team, _ = Team.objects.get_or_create(
                name=match_data["awayTeam"]["name"], slug=match_data["awayTeam"]["slug"]
            )

            self.save_players_to_team(match_data["homeTeam"], home_team)
            self.save_players_to_team(match_data["awayTeam"], away_team)

            # Save Match for teams
            match, created = Match.objects.get_or_create(
                slug=match_data["slug"],
                defaults={
                    "season": season,
                    "home_team": home_team,
                    "away_team": away_team,
                    "status": match_data["status"]["description"],
                    "winner_team": home_team if match_data.get("winnerCode") == 1 else away_team,
                    "start_timestamp": datetime.fromtimestamp(match_data["startTimestamp"]),
                },
            )
        else:
            # Save Players for singles
            home_player_data = self.get_player_detailed_data(match_data["homeTeam"]["id"])
            away_player_data = self.get_player_detailed_data(match_data["awayTeam"]["id"])

            home_player, _ = Player.objects.get_or_create(name=home_player_data["short_name"], full_name=home_player_data["full_name"], slug=home_player_data["slug"])
            away_player, _ = Player.objects.get_or_create(name=away_player_data["short_name"], full_name=away_player_data["full_name"], slug=away_player_data["slug"])

            match, created = Match.objects.get_or_create(
                slug=match_data["slug"],
                defaults={
                    "season": season,
                    "home_player": home_player,
                    "away_player": away_player,
                    "status": match_data["status"]["description"],
                    "winner_player": home_player if match_data.get("winnerCode") == 1 else away_player,
                    "start_timestamp": datetime.fromtimestamp(match_data["startTimestamp"]),
                },
            )

        # Save Score
        home_score = match_data.get("homeScore", {}).get("current", 0)
        away_score = match_data.get("awayScore", {}).get("current", 0)
        period_scores = {
            k: [match_data["homeScore"].get(k, 0), match_data["awayScore"].get(k, 0)]
            for k in match_data.get("periods", {}).keys()
        }

        Score.objects.update_or_create(
            match=match,
            defaults={"home_total": home_score, "away_total": away_score, "period_scores": period_scores},
        )

        # Save Statistics
        statistics = self.get_match_statistics(match_data["id"])
        if statistics and statistics.get("statistics"):
            self.save_statistics(match, statistics)

    @staticmethod
    def get_match_statistics(match_id):
        base_url = f"https://api.sofascore.com/api/v1/event/{match_id}/statistics"
        response = requests.get(base_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch statistics for match ID {match_id}: {response.status_code}")
            return None


    def save_statistics(self, match, statistics_data):
        statistics = statistics_data.get("statistics", [])
        for stat_group in statistics:
            period = stat_group["period"]
            for group in stat_group["groups"]:
                group_name = group["groupName"]
                for stat_item in group["statisticsItems"]:
                    Statistic.objects.update_or_create(
                        match=match,
                        group_name=group_name,
                        key=stat_item["key"],
                        defaults={
                            "home_value": stat_item["homeValue"],
                            "away_value": stat_item["awayValue"],
                        },
                    )

    def save_players_to_team(self, team_data, team):
        if "subTeams" in team_data and team_data["subTeams"]:
            # Если subTeams содержит информацию об игроках
            for player_data in team_data["subTeams"]:

                player_detailed_data = self.get_player_detailed_data(player_data["id"])

                player, _ = Player.objects.get_or_create(
                    name=player_detailed_data["short_name"],
                    full_name=player_detailed_data["full_name"],
                    slug=player_detailed_data["slug"],
                    defaults={
                        "country": player_detailed_data.get("country", ""),
                        "birthdate": player_detailed_data.get("birthdate", ""),
                        "plays": player_detailed_data.get("plays", ""),
                    },
                )
                team.players.add(player)
        else:
            # Если нет subTeams, разделяем name по символу "/"
            player_names = team_data["name"].split(" / ")
            for player_name in player_names:
                slug = player_name.lower().replace(" ", "-")
                player, _ = Player.objects.get_or_create(name=player_name, full_name=player_name, slug=slug)
                team.players.add(player)

    def get_player_detailed_data(self, player_id):
        base_url = "https://api.sofascore.com/api/v1/team/"
        url = f"{base_url}{player_id}"
        print(f"Fetching data for {player_id}...")
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            player_data = data.get("team", {})

            birth_timestamp = player_data.get("playerTeamInfo", {}).get("birthDateTimestamp")
            birth_date = datetime.utcfromtimestamp(birth_timestamp).strftime('%Y-%m-%d') if birth_timestamp else None

            # Извлечение только нужных полей
            parsed_data = {
                "full_name": player_data.get("fullName"),
                "short_name": player_data.get("shortName"),
                "country": player_data.get("country", {}).get("name"),
                "plays": player_data.get("playerTeamInfo", {}).get("plays"),
                "birth_date": birth_date,
                "slug": player_data.get("slug"),
                "tournament": player_data.get("tournament", {}).get("name"),
            }
            return parsed_data
        else:
            print(f"Error fetching data: {response.status_code}")
            return None