import requests
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from django.apps import apps
from django.conf import settings
from django.apps import apps

class Command(BaseCommand):
    help = "Заполняет базу данных матчами ITF за февраль 2023 года"

    def handle(self, *args, **kwargs):
        for model in apps.get_models():
            # Если модель не является моделью пользователя
            if model != User:
                # Удаляем все записи
                model.objects.all().delete()


