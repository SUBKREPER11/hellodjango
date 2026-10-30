import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Task


class TaskApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(title="Przykładowe zadanie", completed=False)

    def test_get_tasks_list(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "Przykładowe zadanie")

    def test_taskboard_html_view(self):
        response = self.client.get('/taskboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TaskBoard')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_task_success(self):
        payload = json.dumps({'title': 'Nowe zadanie testowe'})
        response = self.client.post('/api/tasks/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['title'], 'Nowe zadanie testowe')
        self.assertFalse(data['completed'])
        self.assertTrue(Task.objects.filter(title='Nowe zadanie testowe').exists())

    def test_post_task_empty_title(self):
        payload = json.dumps({'title': '   '})
        response = self.client.post('/api/tasks/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_patch_task_status(self):
        payload = json.dumps({'completed': True})
        response = self.client.patch(f'/api/tasks/{self.task.id}/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_patch_task_not_found(self):
        payload = json.dumps({'completed': True})
        response = self.client.patch('/api/tasks/99999/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_delete_task_success(self):
        response = self.client.delete(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_delete_task_not_found(self):
        response = self.client.delete('/api/tasks/99999/')
        self.assertEqual(response.status_code, 404)
