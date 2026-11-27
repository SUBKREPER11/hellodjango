import json
from decimal import Decimal
from django.test import Client, TestCase
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


class GameLab6ApiAddTests(TestCase):
    """Testy formularza, walidacji, CSRF oraz endpointu POST JSON dla Lab 6."""

    def setUp(self):
        self.add_url = '/games/api/add/'
        self.valid_payload = {
            'title': 'Cyberpunk 2077',
            'genre': 'Action RPG',
            'release_year': 2020,
            'platform': 'PC / Konsole',
            'status': Game.STATUS_RELEASED,
            'rating': '8.9',
            'is_multiplayer': False,
            'description': 'Futurystyczna gra RPG w Night City.',
        }

    def test_games_index_contains_form_and_csrf(self):
        response = self.client.get('/games/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('id="game-form"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('name="title"', html)
        self.assertIn('name="genre"', html)
        self.assertIn('name="release_year"', html)
        self.assertIn('name="description"', html)
        self.assertIn('id="form-message"', html)

    def test_add_game_valid_full_and_minimal_payload(self):
        response = self.client.post(
            self.add_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['item']['title'], 'Cyberpunk 2077')
        self.assertEqual(body['item']['rating'], 8.9)
        self.assertEqual(Game.objects.count(), 1)

        minimal_payload = {
            'title': 'Portal 2',
            'genre': 'Puzzle',
            'release_year': '2011',
            'description': 'Gra logiczna z portalami.',
        }
        minimal_resp = self.client.post(
            '/api/games/add/',
            data=json.dumps(minimal_payload),
            content_type='application/json',
        )
        self.assertEqual(minimal_resp.status_code, 201)
        created = Game.objects.get(pk=minimal_resp.json()['id'])
        self.assertEqual(created.platform, 'PC')
        self.assertEqual(created.status, Game.STATUS_RELEASED)
        self.assertFalse(created.is_multiplayer)
        self.assertIsNone(created.rating)

    def test_add_game_missing_or_empty_required_fields(self):
        for field in ('title', 'genre', 'release_year', 'description'):
            payload = dict(self.valid_payload)
            del payload[field]
            resp = self.client.post(
                self.add_url,
                data=json.dumps(payload),
                content_type='application/json',
            )
            self.assertEqual(resp.status_code, 400)
            self.assertFalse(resp.json()['ok'])
            self.assertTrue(resp.json()['error'])

        empty_title = dict(self.valid_payload, title='   ')
        resp = self.client.post(
            self.add_url,
            data=json.dumps(empty_title),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])
        self.assertEqual(Game.objects.count(), 0)

    def test_add_game_invalid_json_and_invalid_values(self):
        bad_json_resp = self.client.post(
            self.add_url,
            data='{niepoprawny json',
            content_type='application/json',
        )
        self.assertEqual(bad_json_resp.status_code, 400)
        self.assertFalse(bad_json_resp.json()['ok'])

        list_json_resp = self.client.post(
            self.add_url,
            data=json.dumps(['not', 'an', 'object']),
            content_type='application/json',
        )
        self.assertEqual(list_json_resp.status_code, 400)
        self.assertFalse(list_json_resp.json()['ok'])

        invalid_variants = [
            {'release_year': 'abc'},
            {'release_year': 1900},
            {'release_year': True},
            {'rating': '10.5'},
            {'rating': '-0.5'},
            {'rating': '8.55'},
            {'rating': 'wysoka'},
            {'status': 'archived'},
            {'title': 'A' * 101},
        ]
        for overrides in invalid_variants:
            payload = dict(self.valid_payload, **overrides)
            resp = self.client.post(
                self.add_url,
                data=json.dumps(payload),
                content_type='application/json',
            )
            self.assertEqual(resp.status_code, 400, msg=f'Oczekiwano 400 dla {overrides}')
            self.assertFalse(resp.json()['ok'])

        self.assertEqual(Game.objects.count(), 0)

    def test_add_game_requires_post(self):
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 405)

    def test_add_game_csrf_protection(self):
        csrf_client = Client(enforce_csrf_checks=True)

        no_csrf_resp = csrf_client.post(
            self.add_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
        )
        self.assertEqual(no_csrf_resp.status_code, 403)

        bad_csrf_resp = csrf_client.post(
            self.add_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN='nieprawidlowy-token',
        )
        self.assertEqual(bad_csrf_resp.status_code, 403)

        csrf_client.get('/games/')
        csrf_token = csrf_client.cookies['csrftoken'].value
        valid_csrf_resp = csrf_client.post(
            self.add_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(valid_csrf_resp.status_code, 201)
        self.assertTrue(valid_csrf_resp.json()['ok'])
        self.assertEqual(Game.objects.count(), 1)
