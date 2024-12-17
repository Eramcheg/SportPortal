import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sportApp.models import Tournament, Season, Player, Match, Score, Statistic
import json

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
        # Define file path
        output_file = "match_data.txt"

        try:
            # Fetch Statistics
            statistics = self.get_match_statistics(match_data["id"])

            # Prepare Data to Save
            combined_data = {
                "MATCH DATA": match_data,
                "MATCH STATISTICS": statistics if statistics else "No statistics available"
            }

            # Append Combined Data in JSON Format with Pretty Printing
            with open(output_file, "a", encoding="utf-8") as file:
                file.write(json.dumps(combined_data, indent=4, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"An error occurred while saving match data: {e}")
    @staticmethod
    def get_match_statistics(match_id):
        base_url = f"https://api.sofascore.com/api/v1/event/{match_id}/statistics"
        response = requests.get(base_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch statistics for match ID {match_id}: {response.status_code}")
            return None