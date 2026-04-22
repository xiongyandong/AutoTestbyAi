from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import LoginForm, RegisterForm


User = get_user_model()


def _resolve_username(identifier):
    identifier = identifier.strip()
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).only('username').first()
        return user.username if user else identifier
    return identifier


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = _resolve_username(form.cleaned_data['username'])
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, '用户名、邮箱或密码不正确')
        elif not user.is_active:
            messages.error(request, '当前账号已被禁用')
        else:
            login(request, user)
            if not form.cleaned_data['remember_me']:
                request.session.set_expiry(0)
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('dashboard')
            messages.success(request, f'欢迎回来，{user.username}')
            return redirect(next_url)

    return render(request, 'auth/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        request.session.set_expiry(0)
        messages.success(request, '注册成功，已自动登录')
        return redirect('dashboard')

    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, '已退出登录')
    return redirect('login')
