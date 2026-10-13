from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
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
    return render(request, 'index.html', {'tasks': tasks})

@login_required(login_url='register')
def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        priority = request.POST.get('priority', "O'rta")
        if title:
            Task.objects.create(user=request.user, title=title, priority=priority)
    return redirect('index')

@login_required(login_url='register')
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    
    if task.completed:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
        
    task.save()
    return redirect('index')

@login_required(login_url='register')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('index')