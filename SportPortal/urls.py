"""
URL configuration for SportPortal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from sportApp.views import home_page
from sportApp.views_scripts.models_views import match_list, match_detail, team_detail, player_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name="homepage"),
    path('matches/', match_list, name='match_list'),
    path('matches/<int:match_id>/', match_detail, name='match_detail'),
    path('teams/<int:team_id>/', team_detail, name='team_detail'),
    path('players/<int:player_id>/', player_detail, name='player_detail'),
]
