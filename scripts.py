import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sportApp.models import Player, Match, Set, Game


def parse_matches_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Найти все матчи на странице
    matches = soup.select('.event-list .event')  # Пример селектора, уточнить под HTML сайта
    for match in matches:
        # Извлекаем информацию о матче
        player1_name = match.select_one('.player1 .name').text
        player2_name = match.select_one('.player2 .name').text
        score = match.select_one('.score').text.strip()
        date_text = match.select_one('.date').text.strip()
        match_date = datetime.strptime(date_text, "%Y-%m-%d")

        # Добавляем игроков в базу данных или получаем существующих
        player1, _ = Player.objects.get_or_create(name=player1_name)
        player2, _ = Player.objects.get_or_create(name=player2_name)

        # Создаем запись о матче
        match_obj = Match.objects.create(
            player1=player1,
            player2=player2,
            date=match_date,
            tournament="ITF",  # Уточнить по данным
            score=score,
            winner=player1 if "W" in score else player2  # Условие для определения победителя
        )

        # Если есть сеты и геймы, добавляем их
        sets = match.select('.sets .set')  # Пример
        for set_number, set_item in enumerate(sets, start=1):
            player1_set_score = int(set_item.select_one('.player1').text)
            player2_set_score = int(set_item.select_one('.player2').text)

            Set.objects.create(
                match=match_obj,
                set_number=set_number,
                player1_score=player1_set_score,
                player2_score=player2_set_score
            )


def get_matches_by_date(date):
    """
    Получить список матчей по указанной дате из Sofascore API.

    :param date: Дата в формате YYYY-MM-DD.
    :return: Список матчей с их информацией.
    """
    base_url = "https://api.sofascore.com/api/v1"
    endpoint = f"/sport/tennis/scheduled-events/{date}"
    url = base_url + endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        matches = data.get('events', [])
        if not matches:
            print(f"No matches found for {date}")
            return

        for match in matches:
            tournament = match.get('tournament', {}).get('name', 'Unknown Tournament')
            home_team = match.get('homeTeam', {}).get('name', 'Unknown Player')
            away_team = match.get('awayTeam', {}).get('name', 'Unknown Player')
            start_time = datetime.fromtimestamp(match.get('startTimestamp', 0))

            print(f"Tournament: {tournament}")
            print(f"Match: {home_team} vs {away_team}")
            print(f"Start Time: {start_time}")
            print("-" * 40)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")


# Указанная дата
date = "2023-03-03"
get_matches_by_date(date)