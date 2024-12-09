from django.shortcuts import render
from datetime import datetime, timedelta
# Create your views here.

def generate_urls(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = timedelta(days=1)

    urls = []
    while start <= end:
        urls.append(f"https://www.sofascore.com/ru/tennis/{start.strftime('%Y-%m-%d')}")
        start += delta

    return urls