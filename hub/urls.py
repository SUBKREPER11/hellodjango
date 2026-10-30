from django.contrib import admin
from django.urls import path, include
from lab4 import views as lab4_views

urlpatterns = [
    # Panel administratora (jeden, unikalny w całym projekcie)
    path('admin/', admin.site.urls),

    # Gry (Lab 4)
    path('games/', lab4_views.index, name='games_index'),
    path('games/api/', lab4_views.api_games, name='games_api_sub'),
    path('api/games/', lab4_views.api_games, name='games_api_root'),

    # Taskboard (Lab 3)
    path('', include('lab3.urls')),

    # Strona główna frontend_demo (Lab 2)
    path('', include('lab2.urls')),

    # Witaj (Lab 1)
    path('', include('lab1.urls')),

    # Aliasy lab1, lab2, lab3, lab4
    path('lab1/', include('lab1.urls')),
    path('lab2/', include('lab2.urls')),
    path('lab3/', include('lab3.urls')),
    path('lab4/', include([
        path('', lab4_views.index),
        path('api/', lab4_views.api_games),
    ])),
]
