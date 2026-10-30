from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='games_index'),
    path('games/', views.index, name='games_index_sub'),
    path('api/', views.api_games, name='games_api'),
    path('api/games/', views.api_games, name='games_api_root'),
    path('games/api/', views.api_games, name='games_api_sub'),
]
