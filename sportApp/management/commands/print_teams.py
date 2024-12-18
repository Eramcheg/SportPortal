import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sportApp.models import Tournament, Season, Player, Match, Score, Statistic
import json

class Command(BaseCommand):
    help = "Заполняет базу данных матчами ITF за указанный период"

    def handle(self, *args, **kwargs):
        base_url = "https://api.sofascore.com/api/v1/team/"

        team_id = 142942#462878
        url = f"{base_url}{team_id}"
        print(f"Fetching data for {team_id}...")
        self.parse_matches(url)

    def parse_matches(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data)
        else:
            print(f"Failed to fetch matches: {response.status_code}")



