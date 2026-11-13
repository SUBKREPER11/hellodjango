from decimal import Decimal
from django.test import TestCase
from .models import Game


class GameLab5Tests(TestCase):
    """Testy modelu Game, zapytań ORM oraz endpointów JSON dla Lab 5."""

    def setUp(self):
        self.g1 = Game.objects.create(
            title='Wiedźmin 3',
            genre='RPG',
            release_year=2015,
            description='Gra RPG fantasy.',
            is_multiplayer=False,
            platform='PC / Konsole',
            rating=Decimal('9.8'),
            status=Game.STATUS_RELEASED,
        )
        self.g2 = Game.objects.create(
            title='Counter-Strike 2',
            genre='FPS',
            release_year=2023,
            description='Taktyczna strzelanka.',
            is_multiplayer=True,
            platform='PC',
            rating=Decimal('8.3'),
            status=Game.STATUS_RELEASED,
        )
        self.g3 = Game.objects.create(
            title='Hades II',
            genre='Roguelike',
            release_year=2024,
            description='Roguelike w świecie mitologii.',
            is_multiplayer=False,
            platform='PC',
            rating=Decimal('9.1'),
            status=Game.STATUS_EARLY_ACCESS,
        )
        self.g4 = Game.objects.create(
            title='Baldurs Gate 3',
            genre='cRPG',
            release_year=2023,
            description='Gra fabularna D&D.',
            is_multiplayer=True,
            platform='PC / Konsole',
            rating=Decimal('9.7'),
            status=Game.STATUS_RELEASED,
        )

    def test_model_str_and_defaults(self):
        game = Game.objects.create(
            title='Test Game',
            genre='Indie',
            release_year=2025,
            description='Opis testowy.',
        )
        self.assertEqual(game.platform, 'PC')
        self.assertEqual(game.status, Game.STATUS_RELEASED)
        self.assertIsNone(game.rating)
        self.assertEqual(str(game), 'Test Game (2025) [PC]')

    def test_games_index_renders(self):
        response = self.client.get('/games/')
        self.assertEqual(response.status_code, 200)

    def test_api_games_sorting_and_featured_first(self):
        response = self.client.get('/games/api/?sort=title')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        titles = [item['title'] for item in payload['items']]
        self.assertEqual(titles, ['Baldurs Gate 3', 'Counter-Strike 2', 'Hades II', 'Wiedźmin 3'])
        self.assertEqual(payload['featured_game']['title'], 'Wiedźmin 3')

    def test_api_games_filters_and_limit(self):
        response = self.client.get('/games/api/?multiplayer=true&status=released&limit=1&sort=rating')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['items'][0]['title'], 'Baldurs Gate 3')

        platform_resp = self.client.get('/games/api/?platform=PC&min_rating=9.0')
        self.assertEqual(platform_resp.status_code, 200)
        platform_titles = {item['title'] for item in platform_resp.json()['items']}
        self.assertEqual(platform_titles, {'Wiedźmin 3', 'Hades II', 'Baldurs Gate 3'})

    def test_api_game_detail_get_and_404(self):
        response = self.client.get(f'/games/api/{self.g1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['item']['title'], 'Wiedźmin 3')

        missing = self.client.get('/games/api/99999/')
        self.assertEqual(missing.status_code, 404)

    def test_api_games_top_limit_3(self):
        response = self.client.get('/games/api/top/')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.json()['items']]
        self.assertEqual(titles, ['Wiedźmin 3', 'Baldurs Gate 3', 'Counter-Strike 2'])

    def test_api_games_invalid_params(self):
        self.assertEqual(self.client.get('/games/api/?limit=abc').status_code, 400)
        self.assertEqual(self.client.get('/games/api/?min_rating=xyz').status_code, 400)
