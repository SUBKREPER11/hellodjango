from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='games_index'),
    path('api/', views.api_games, name='games_api'),
]
