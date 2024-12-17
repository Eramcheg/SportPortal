import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sportApp.models import Tournament, Season, Player, Match, Score, Statistic


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
            defaults={
                "category": tournament_data.get("category", {}).get("name", ""),
                "country": tournament_data.get("category", {}).get("country", {}).get("name", ""),
            },
        )

        # Save Season
        season_data = match_data["season"]
        season, _ = Season.objects.get_or_create(
            tournament=tournament,
            name=season_data["name"],
            year=int(season_data["year"]),
        )

        # Save Players
        home_player_data = match_data["homeTeam"]
        away_player_data = match_data["awayTeam"]

        home_player, _ = Player.objects.get_or_create(
            name=home_player_data["name"],
            slug=home_player_data["slug"],
            defaults={
                "short_name": home_player_data.get("shortName", ""),
                "country": home_player_data.get("country", {}).get("name", ""),
                "national": home_player_data.get("national", False),
            },
        )

        away_player, _ = Player.objects.get_or_create(
            name=away_player_data["name"],
            slug=away_player_data["slug"],
            defaults={
                "short_name": away_player_data.get("shortName", ""),
                "country": away_player_data.get("country", {}).get("name", ""),
                "national": away_player_data.get("national", False),
            },
        )
        print(match_data["status"]["description"])
        # Save Match
        match, created = Match.objects.get_or_create(
            slug=match_data["slug"],
            defaults={
                "season": season,
                "home_player": home_player,
                "away_player": away_player,
                "status": match_data["status"]["description"],
                "winner": home_player if match_data.get("winnerCode") == 1 else away_player,
                "start_timestamp": datetime.fromtimestamp(match_data["startTimestamp"]),
            },
        )

        if created:
            print(f"Match {match} added to the database.")
        else:
            print(f"Match {match} already exists in the database.")

        # Handle Score
        home_score = match_data.get("homeScore", {}).get("current", 0)
        away_score = match_data.get("awayScore", {}).get("current", 0)

        Score.objects.update_or_create(
            match=match,
            defaults={
                "home_total": home_score or 0,
                "away_total": away_score or 0,
                "period_scores": {},
            },
        )

        # Fetch and save Statistics (if available)
        statistics = self.get_match_statistics(match_data["id"])
        if statistics and statistics.get("statistics"):
            self.save_statistics(match, statistics)
        else:
            print(f"No statistics available for match {match.slug}.")

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