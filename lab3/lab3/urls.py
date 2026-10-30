from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='taskboard_root'),
    path('taskboard/', views.index, name='taskboard_index'),
    path('api/tasks/', views.tasks_api, name='tasks_api'),
    path('api/tasks/<int:task_id>/', views.task_detail_api, name='task_detail_api'),
]
