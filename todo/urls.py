from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add/', views.add_task, name='add_task'),
    path('toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('mark-notified/<int:task_id>/', views.mark_notified, name='mark_notified'),
    path('api/due-tasks/', views.get_due_tasks, name='get_due_tasks'),
    path('snooze/<int:task_id>/', views.snooze_task, name='snooze_task'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
]