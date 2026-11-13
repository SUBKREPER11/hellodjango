from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .models import Game

SORT_OPTIONS = {
    'year_desc': ('-release_year', 'title'),
    'year_asc': ('release_year', 'title'),
    'title': ('title',),
    '-title': ('-title',),
    'rating': ('-rating', 'title'),
}

VALID_STATUSES = {
    Game.STATUS_RELEASED,
    Game.STATUS_EARLY_ACCESS,
    Game.STATUS_UPCOMING,
}


def index(request):
    return render(request, 'games/index.html')


@require_GET
def api_games(request):
    """Zwraca listę gier z sortowaniem, filtrowaniem i opcjonalnym limitem po stronie ORM."""
    sort_key = request.GET.get('sort', 'year_desc')
    order_fields = SORT_OPTIONS.get(sort_key, SORT_OPTIONS['year_desc'])

    # 1. Pobranie rekordów z sortowaniem (order_by)
    games = Game.objects.all().order_by(*order_fields)

    # 2. Filtrowanie według wybranych pól (filter)
    multiplayer = request.GET.get('multiplayer')
    if multiplayer == 'true':
        games = games.filter(is_multiplayer=True)
    elif multiplayer == 'false':
        games = games.filter(is_multiplayer=False)

    status = request.GET.get('status')
    if status in VALID_STATUSES:
        games = games.filter(status=status)

    platform = request.GET.get('platform', '').strip()
    if platform:
        games = games.filter(platform__icontains=platform)

    genre = request.GET.get('genre', '').strip()
    if genre:
        games = games.filter(genre__icontains=genre)

    min_rating = request.GET.get('min_rating', '').strip()
    if min_rating:
        try:
            games = games.filter(rating__gte=Decimal(min_rating))
        except InvalidOperation:
            return JsonResponse({'error': 'Nieprawidłowa wartość parametru min_rating.'}, status=400)

    # 3. Ograniczenie wyników ([:N]) oraz pobranie najlepszego rekordu (first)
    limit = request.GET.get('limit', '').strip()
    if limit:
        try:
            limit_val = int(limit)
            if limit_val <= 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Parametr limit musi być dodatnią liczbą całkowitą.'}, status=400)
        games = games[:limit_val]

    featured_game = Game.objects.filter(rating__isnull=False).order_by('-rating', 'title').first()
    data = [game.to_dict() for game in games]

    return JsonResponse({
        'items': data,
        'count': len(data),
        'featured_game': featured_game.to_dict() if featured_game else None,
    })


@require_GET
def api_game_detail(request, game_id):
    """Zwraca szczegóły pojedynczej gry pobranej przez ORM get()."""
    try:
        game = Game.objects.get(pk=game_id)
    except Game.DoesNotExist:
        return JsonResponse({'error': f'Gra o ID {game_id} nie została znaleziona.'}, status=404)

    return JsonResponse({'item': game.to_dict()})


@require_GET
def api_games_top(request):
    """Zwraca 3 najwyżej oceniane wydane gry (filter + order_by + [:3])."""
    top_games = (
        Game.objects.filter(status=Game.STATUS_RELEASED, rating__isnull=False)
        .order_by('-rating', 'title')[:3]
    )
    return JsonResponse({'items': [game.to_dict() for game in top_games]})
