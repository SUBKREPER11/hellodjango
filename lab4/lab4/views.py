import json
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
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

MIN_RELEASE_YEAR = 1950
MAX_RELEASE_YEAR = 2100


@ensure_csrf_cookie
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


def _parse_text_field(data, key, label, required=True, max_length=None, default=''):
    """Waliduje i zwraca pole tekstowe z obiektu JSON."""
    raw = data.get(key)
    if raw is None:
        if required:
            return None, f'Pole „{label}” jest wymagane.'
        return default, None
    if not isinstance(raw, str):
        return None, f'Pole „{label}” musi być tekstem.'
    value = raw.strip()
    if not value:
        if required:
            return None, f'Pole „{label}” nie może być puste.'
        return default, None
    if max_length is not None and len(value) > max_length:
        return None, f'Pole „{label}” może mieć maksymalnie {max_length} znaków.'
    return value, None


def _parse_release_year(raw):
    """Waliduje rok wydania gry jako liczbę całkowitą z dopuszczalnego zakresu."""
    if raw is None or isinstance(raw, bool):
        return None, 'Podaj poprawny rok wydania.'
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None, 'Pole „Rok wydania” jest wymagane.'
    elif isinstance(raw, float) and not raw.is_integer():
        return None, 'Rok wydania musi być liczbą całkowitą.'
    try:
        year = int(raw)
    except (TypeError, ValueError):
        return None, 'Rok wydania musi być liczbą całkowitą.'
    if not (MIN_RELEASE_YEAR <= year <= MAX_RELEASE_YEAR):
        return None, f'Rok wydania musi mieścić się w zakresie {MIN_RELEASE_YEAR}–{MAX_RELEASE_YEAR}.'
    return year, None


def _parse_rating(raw):
    """Waliduje opcjonalną ocenę gry z zakresu 0–10 (maksymalnie 1 miejsce po przecinku)."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, None
    if isinstance(raw, bool):
        return None, 'Ocena musi być liczbą z zakresu 0–10.'
    try:
        rating = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        return None, 'Ocena musi być poprawną liczbą z zakresu 0–10.'
    if not rating.is_finite() or rating < Decimal('0') or rating > Decimal('10'):
        return None, 'Ocena musi mieścić się w zakresie od 0 do 10.'
    exponent = rating.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -1:
        return None, 'Ocena może mieć maksymalnie jedno miejsce po przecinku.'
    return rating, None


def _parse_multiplayer(raw):
    """Konwertuje i waliduje wartość logiczną trybu multiplayer."""
    if raw is None:
        return False, None
    if isinstance(raw, bool):
        return raw, None
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {'true', 'on', '1', 'tak'}:
            return True, None
        if normalized in {'false', 'off', '0', 'nie', ''}:
            return False, None
    return None, 'Nieprawidłowa wartość pola „Tryb multiplayer”.'


def _validate_game_payload(data):
    """Waliduje wszystkie pola wejściowe dla nowej gry i zwraca (cleaned_data, error)."""
    title, err = _parse_text_field(data, 'title', 'Tytuł gry', required=True, max_length=100)
    if err:
        return None, err

    genre, err = _parse_text_field(data, 'genre', 'Gatunek', required=True, max_length=50)
    if err:
        return None, err

    release_year, err = _parse_release_year(data.get('release_year'))
    if err:
        return None, err

    description, err = _parse_text_field(data, 'description', 'Opis', required=True, max_length=5000)
    if err:
        return None, err

    platform, err = _parse_text_field(
        data, 'platform', 'Platforma', required=False, max_length=50, default='PC'
    )
    if err:
        return None, err

    status, err = _parse_text_field(
        data, 'status', 'Status', required=False, max_length=20, default=Game.STATUS_RELEASED
    )
    if err:
        return None, err
    if status not in VALID_STATUSES:
        return None, 'Nieprawidłowy status gry.'

    rating, err = _parse_rating(data.get('rating'))
    if err:
        return None, err

    is_multiplayer, err = _parse_multiplayer(data.get('is_multiplayer'))
    if err:
        return None, err

    return {
        'title': title,
        'genre': genre,
        'release_year': release_year,
        'description': description,
        'platform': platform,
        'status': status,
        'rating': rating,
        'is_multiplayer': is_multiplayer,
    }, None


@require_POST
def api_game_add(request):
    """Obsługuje dodanie nowej gry przez JSON POST oraz zapis przez ORM."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Niepoprawny format danych JSON.'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'Oczekiwano obiektu JSON.'}, status=400)

    cleaned_data, error = _validate_game_payload(data)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=400)

    try:
        game = Game(**cleaned_data)
        game.full_clean()
        game.save()
    except (ValidationError, IntegrityError, DatabaseError):
        return JsonResponse(
            {'ok': False, 'error': 'Nie udało się zapisać gry w bazie danych.'},
            status=400,
        )

    return JsonResponse(
        {
            'ok': True,
            'id': game.id,
            'item': game.to_dict(),
            'message': f'Dodano grę „{game.title}”.',
        },
        status=201,
    )
