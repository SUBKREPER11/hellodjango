from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='games_index'),
    path('games/', views.index, name='games_index_sub'),
    path('api/', views.api_games, name='games_api'),
    path('api/top/', views.api_games_top, name='games_api_top'),
    path('api/add/', views.api_game_add, name='games_api_add'),
    path('api/<int:game_id>/', views.api_game_detail, name='games_api_detail'),
    path('api/games/', views.api_games, name='games_api_root'),
    path('api/games/top/', views.api_games_top, name='games_api_root_top'),
    path('api/games/add/', views.api_game_add, name='games_api_root_add'),
    path('api/games/<int:game_id>/', views.api_game_detail, name='games_api_root_detail'),
    path('games/api/', views.api_games, name='games_api_sub'),
    path('games/api/top/', views.api_games_top, name='games_api_sub_top'),
    path('games/api/add/', views.api_game_add, name='games_api_sub_add'),
    path('games/api/<int:game_id>/', views.api_game_detail, name='games_api_sub_detail'),
]
