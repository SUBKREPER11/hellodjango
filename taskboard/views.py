import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Task


@ensure_csrf_cookie
def index(request):
    """Widok renderujący główny interfejs TaskBoard."""
    return render(request, 'taskboard/index.html')


def tasks_api(request):
    """Obsługa pobierania listy zadań (GET) oraz dodawania nowego zadania (POST)."""
    if request.method == 'GET':
        tasks = Task.objects.order_by('-created_at')
        return JsonResponse([task.to_dict() for task in tasks], safe=False, status=200)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Nieprawidłowy format danych JSON.'}, status=400)

        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'Treść zadania nie może być pusta.'}, status=400)

        completed = bool(data.get('completed', False))
        task = Task.objects.create(title=title, completed=completed)
        return JsonResponse(task.to_dict(), status=201)

    return HttpResponseNotAllowed(['GET', 'POST'])


def task_detail_api(request, task_id):
    """Obsługa aktualizacji statusu zadania (PATCH) oraz usuwania (DELETE)."""
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'error': f'Zadanie o ID {task_id} nie zostało znalezione.'}, status=404)

    if request.method == 'PATCH':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Nieprawidłowy format danych JSON.'}, status=400)

        if 'completed' in data:
            task.completed = bool(data['completed'])

        if 'title' in data:
            title = str(data['title']).strip()
            if not title:
                return JsonResponse({'error': 'Treść zadania nie może być pusta.'}, status=400)
            task.title = title

        task.save()
        return JsonResponse(task.to_dict(), status=200)

    elif request.method == 'DELETE':
        task_data = task.to_dict()
        task.delete()
        return JsonResponse({'message': 'Zadanie zostało pomyślnie usunięte.', 'task': task_data}, status=200)

    return HttpResponseNotAllowed(['PATCH', 'DELETE'])
