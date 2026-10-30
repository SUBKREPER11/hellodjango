from django.shortcuts import render
from django.http import JsonResponse
from .models import Game


def index(request):
    return render(request, 'games/index.html')


def api_games(request):
    multiplayer = request.GET.get('multiplayer')
    
    games = Game.objects.all()
    if multiplayer == 'true':
        games = games.filter(is_multiplayer=True)
    elif multiplayer == 'false':
        games = games.filter(is_multiplayer=False)
        
    data = [
        {
            'id': game.id,
            'title': game.title,
            'genre': game.genre,
            'release_year': game.release_year,
            'description': game.description,
            'is_multiplayer': game.is_multiplayer,
        }
        for game in games
    ]
    return JsonResponse({'items': data})
