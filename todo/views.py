import secrets
import urllib.parse
import requests
from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        remember_me = request.POST.get('remember_me')

        if not username or not password:
            messages.error(request, "Barcha maydonlarni to'ldiring!")
            return render(request, 'register.html')

        if len(password) < 4:
            messages.error(request, "Parol kamida 4 ta belgidan iborat bo'lishi kerak!")
            return render(request, 'register.html')

        if password != password_confirm:
            messages.error(request, "Kiritilgan parollar bir-biriga mos kelmadi!")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi band, boshqa nom tanlang!")
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, password=password)
        login(request, user)

        # Eslab qolish (Remember me)
        if remember_me:
            request.session.set_expiry(1209600)  # 2 hafta (yoki 30 kun: 2592000)
        else:
            request.session.set_expiry(0)  # Brauzer yopilganda chiqib ketadi

        messages.success(request, f"Xush kelibsiz, {user.username}! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
        return redirect('index')

    return render(request, 'register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Eslab qolish (Remember me)
            if remember_me:
                request.session.set_expiry(2592000)  # 30 kun
            else:
                request.session.set_expiry(0)  # Brauzer yopilganda sessiya tugaydi
            return redirect('index')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='register')
def index(request):
    tasks = Task.objects.filter(user=request.user).order_by('-id')
    tasks_data = [
        {
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'dueEpochSec': int(t.due_date.timestamp()) if t.due_date else None,
            'dueFormatted': t.due_date.strftime('%d.%m.%Y %H:%M') if t.due_date else '',
            'notified': t.notified,
        }
        for t in tasks if not t.completed and t.due_date
    ]
    return render(request, 'index.html', {'tasks': tasks, 'tasks_data': tasks_data})

@login_required(login_url='register')
def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        priority = request.POST.get('priority', "O'rta")
        due_date_str = request.POST.get('due_date', '').strip()
        
        due_date = None
        if due_date_str:
            parsed = parse_datetime(due_date_str)
            if parsed:
                if timezone.is_naive(parsed):
                    due_date = timezone.make_aware(parsed, timezone.get_current_timezone())
                else:
                    due_date = parsed

        if title:
            Task.objects.create(
                user=request.user,
                title=title,
                priority=priority,
                due_date=due_date
            )
    return redirect('index')

@login_required(login_url='register')
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    
    if task.completed:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
        # Agar vazifa muddati hali kelmagan bo'lsa, bildirishnomani qayta faollashtiramiz
        if task.due_date and task.due_date > timezone.now():
            task.notified = False
        
    task.save()
    return redirect('index')

@login_required(login_url='register')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('index')

@login_required(login_url='register')
def mark_notified(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        task.notified = True
        task.save(update_fields=['notified'])
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Faqat POST so\'rovi qabul qilinadi'}, status=405)

@login_required(login_url='register')
def get_due_tasks(request):
    now = timezone.now()
    tasks = Task.objects.filter(
        user=request.user,
        completed=False,
        due_date__isnull=False,
        notified=False,
        due_date__lte=now
    )
    task_list = []
    for t in tasks:
        task_list.append({
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'due_date': t.due_date.isoformat(),
            'due_formatted': t.due_date.strftime('%d.%m.%Y %H:%M')
        })
    return JsonResponse({'tasks': task_list})

@login_required(login_url='register')
def snooze_task(request, task_id):
    if request.method == 'POST':
        try:
            minutes = int(request.POST.get('minutes', 15))
        except (ValueError, TypeError):
            minutes = 15
        task = get_object_or_404(Task, id=task_id, user=request.user)
        task.due_date = timezone.now() + timedelta(minutes=minutes)
        task.notified = False
        task.save(update_fields=['due_date', 'notified'])
        return JsonResponse({
            'status': 'ok',
            'new_due_date': task.due_date.strftime('%d.%m.%Y %H:%M')
        })
    return JsonResponse({'status': 'error'}, status=400)

def service_worker(request):
    js_content = """// Service Worker for To-Do List Push Notifications
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if (client.url.includes('/') && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});
"""
    return HttpResponse(js_content, content_type='application/javascript')

def google_login(request):
    if not getattr(settings, 'GOOGLE_CLIENT_ID', None) or not getattr(settings, 'GOOGLE_CLIENT_SECRET', None):
        messages.error(
            request, 
            "Google orqali kirish sozlanmagan. Iltimos, loyihaga GOOGLE_CLIENT_ID va GOOGLE_CLIENT_SECRET kalitlarini kiriting."
        )
        return redirect('login')
        
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://127.0.0.1:8000/google/callback/')

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

def google_callback(request):
    error = request.GET.get('error')
    if error:
        messages.error(request, f"Google orqali kirish bekor qilindi yoki xatolik: {error}")
        return redirect('login')
        
    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('google_oauth_state')
    
    if not state or state != saved_state:
        messages.error(request, "Xavfsizlik tekshiruvidan o'tmadi (State mos kelmadi). Qaytadan urinib ko'ring.")
        return redirect('login')
        
    if not code:
        messages.error(request, "Google avtorizatsiya kodi (code) qabul qilinmadi.")
        return redirect('login')
        
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://127.0.0.1:8000/google/callback/')

    try:
        token_res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10
        )
        if token_res.status_code != 200:
            messages.error(request, "Google'dan token olishda xatolik yuz berdi.")
            return redirect('login')
            
        token_data = token_res.json()
        access_token = token_data.get('access_token')
        
        userinfo_res = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=10
        )
        if userinfo_res.status_code != 200:
            messages.error(request, "Google hisob ma'lumotlarini olib bo'lmadi.")
            return redirect('login')
            
        user_info = userinfo_res.json()
        email = user_info.get('email')
        if not email:
            messages.error(request, "Google hisobingizdan email manzili topilmadi.")
            return redirect('login')
            
        user = User.objects.filter(email=email).first()
        if not user:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
                
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_unusable_password()
            user.save()
            
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session.set_expiry(2592000)
        
        display_name = user.first_name or user.username
        messages.success(request, f"Xush kelibsiz, {display_name}! Google orqali tizimga kirdingiz.")
        return redirect('index')
        
    except requests.RequestException as e:
        messages.error(request, f"Google serveriga ulanishda xatolik yuz berdi: {e}")
        return redirect('login')