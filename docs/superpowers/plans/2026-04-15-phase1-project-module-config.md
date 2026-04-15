# Pytest 测试平台 - 第一阶段实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 Django 项目框架，实现项目管理、模块管理、配置管理的完整 CRUD 功能及 Web 界面。

**Architecture:** Django 4.x 单体应用，Bootstrap 5 前端，SQLite 开发数据库。采用 Django 模板渲染，单 app (`api`) 承载所有业务逻辑。模型关系：Project → Module → Config，支持多环境配置。

**Tech Stack:** Python 3.10, Django 4.x, Bootstrap 5, jQuery 3.x, SQLite

---

## File Structure

```
f:/work/openAItest/
├── pytest_platform/              # Django project package
│   ├── __init__.py
│   ├── settings.py               # 项目配置
│   ├── urls.py                   # 根 URL 配置
│   ├── wsgi.py
│   └── asgi.py
├── api/                          # 主业务 app
│   ├── __init__.py
│   ├── models.py                 # Project, Module, Config 模型
│   ├── views/                    # 视图模块
│   │   ├── __init__.py
│   │   ├── project.py            # 项目管理视图
│   │   ├── module.py             # 模块管理视图
│   │   ├── config.py             # 配置管理视图
│   │   └── dashboard.py          # Dashboard 视图
│   ├── forms.py                  # 表单定义
│   ├── urls.py                   # API URL 配置
│   ├── admin.py                  # Admin 注册
│   └── migrations/
├── templates/                    # 模板目录
│   ├── base.html                 # 基础布局模板
│   ├── dashboard.html            # 首页
│   ├── project/                  # 项目管理模板
│   │   ├── list.html
│   │   └── form.html
│   ├── module/                   # 模块管理模板
│   │   ├── list.html
│   │   └── form.html
│   └── config/                   # 配置管理模板
│       ├── list.html
│       └── form.html
├── static/                       # 静态文件
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── manage.py
├── requirements.txt
└── docs/
```

---

### Task 1: Django 项目初始化

**Files:**
- Create: `manage.py`
- Create: `pytest_platform/__init__.py`
- Create: `pytest_platform/settings.py`
- Create: `pytest_platform/urls.py`
- Create: `pytest_platform/wsgi.py`
- Create: `pytest_platform/asgi.py`
- Create: `requirements.txt`

- [ ] **Step 1: 安装 Django 依赖**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/pip.exe install django==4.2.*
```

- [ ] **Step 2: 创建 Django 项目**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/django-admin.exe startproject pytest_platform .
```

- [ ] **Step 3: 创建 requirements.txt**

```txt
Django==4.2.*
```

Run: `cd f:/work/openAItest && .venv/Scripts/pip.exe freeze | grep -i django > requirements.txt`

- [ ] **Step 4: 验证项目可运行**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: 配置 settings.py 中的中文和时区**

Modify `pytest_platform/settings.py`:
```python
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Templates
TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: initialize Django project"
```

---

### Task 2: 创建 api app 和基础模型

**Files:**
- Create: `api/__init__.py`
- Create: `api/models.py`
- Create: `api/admin.py`
- Create: `api/apps.py`

- [ ] **Step 1: 创建 api app**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py startapp api
```

- [ ] **Step 2: 注册 app 到 settings.py**

Modify `pytest_platform/settings.py`, add `'api'` to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',
]
```

- [ ] **Step 3: 编写 Project 模型**

Write `api/models.py`:
```python
from django.db import models


class Project(models.Model):
    name = models.CharField('项目名称', max_length=100, unique=True)
    description = models.TextField('项目描述', blank=True, default='')
    created_by = models.CharField('创建人', max_length=50, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Module(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='所属项目', related_name='modules')
    name = models.CharField('模块名称', max_length=100)
    description = models.TextField('模块描述', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '模块'
        verbose_name_plural = verbose_name
        ordering = ['project', 'name']
        unique_together = [['project', 'name']]

    def __str__(self):
        return f'{self.project.name} / {self.name}'


class Config(models.Model):
    ENV_CHOICES = [
        ('DEV', '开发环境'),
        ('QA', '测试环境'),
        ('PROD', '生产环境'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name='所属模块', related_name='configs')
    name = models.CharField('配置名称', max_length=100)
    variables = models.JSONField('全局变量', default=dict, blank=True)
    parameters = models.JSONField('公共请求参数', default=dict, blank=True)
    request_hooks = models.JSONField('请求Hooks', default=dict, blank=True)
    response_hooks = models.JSONField('响应Hooks', default=dict, blank=True)
    env_type = models.CharField('环境类型', max_length=10, choices=ENV_CHOICES, default='DEV')
    created_by = models.CharField('创建人', max_length=50, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '配置'
        verbose_name_plural = verbose_name
        ordering = ['module', 'name']

    def __str__(self):
        return f'{self.module} / {self.name}'
```

- [ ] **Step 4: 注册 Admin**

Write `api/admin.py`:
```python
from django.contrib import admin
from .models import Project, Module, Config


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_by', 'created_at', 'updated_at']
    search_fields = ['name', 'description']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'description', 'created_at', 'updated_at']
    list_filter = ['project']
    search_fields = ['name', 'description']


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'env_type', 'created_by', 'created_at', 'updated_at']
    list_filter = ['env_type', 'module__project']
    search_fields = ['name']
```

- [ ] **Step 5: 运行迁移并验证**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py makemigrations api
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py migrate
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: add Project, Module, Config models"
```

---

### Task 3: 基础模板和静态文件

**Files:**
- Create: `templates/base.html`
- Create: `static/css/style.css`
- Create: `static/js/main.js`

- [ ] **Step 1: 创建目录结构**

Run:
```bash
mkdir -p f:/work/openAItest/templates f:/work/openAItest/static/css f:/work/openAItest/static/js
```

- [ ] **Step 2: 编写基础布局模板**

Write `templates/base.html`:
```html
{% load static %}
<!DOCTYPE html>
<html lang="zh-hans">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Pytest 测试平台{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
</head>
<body>
    <!-- 顶部导航 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'dashboard' %}">
                <i class="bi bi-clipboard-check"></i> Pytest 测试平台
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link {% block nav_dashboard %}{% endblock %}" href="{% url 'dashboard' %}">
                            <i class="bi bi-speedometer2"></i> 首页概览
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% block nav_project %}{% endblock %}" href="{% url 'project_list' %}">
                            <i class="bi bi-folder"></i> 项目管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% block nav_module %}{% endblock %}" href="{% url 'module_list' %}">
                            <i class="bi bi-diagram-3"></i> 模块管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% block nav_config %}{% endblock %}" href="{% url 'config_list' %}">
                            <i class="bi bi-gear"></i> 配置管理
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- 主内容 -->
    <div class="container-fluid mt-3">
        {% if messages %}
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
        {% endif %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.7.0/dist/jquery.min.js"></script>
    <script src="{% static 'js/main.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

- [ ] **Step 3: 编写自定义样式**

Write `static/css/style.css`:
```css
body {
    background-color: #f5f5f5;
}

.navbar-brand {
    font-weight: 600;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border: none;
}

.card-header {
    background-color: #fff;
    border-bottom: 1px solid #eee;
    font-weight: 600;
}

.table th {
    font-weight: 600;
    background-color: #f8f9fa;
}

.btn-group .btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.stat-card {
    text-align: center;
    padding: 1.5rem;
}

.stat-card .stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: #0d6efd;
}

.stat-card .stat-label {
    color: #6c757d;
    font-size: 0.9rem;
}

/* 高亮当前导航 */
.nav-link.active {
    color: #fff !important;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 0.25rem;
}
```

- [ ] **Step 4: 编写基础 JS**

Write `static/js/main.js`:
```javascript
// 通用删除确认
function confirmDelete(url, name) {
    if (confirm('确定要删除 "' + name + '" 吗？此操作不可恢复。')) {
        $.ajax({
            url: url,
            method: 'POST',
            data: { csrfmiddlewaretoken: getCookie('csrftoken') },
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                alert('删除失败: ' + (xhr.responseJSON?.error || '未知错误'));
            }
        });
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add base template and static files"
```

---

### Task 4: 项目管理视图和模板

**Files:**
- Create: `api/views/__init__.py`
- Create: `api/views/project.py`
- Create: `templates/project/list.html`
- Create: `templates/project/form.html`

- [ ] **Step 1: 创建视图目录结构**

Run:
```bash
mkdir -p f:/work/openAItest/api/views f:/work/openAItest/templates/project
```

- [ ] **Step 2: 编写项目管理视图**

Write `api/views/__init__.py`:
```python
from .project import *
from .module import *
from .config import *
from .dashboard import *
```

Write `api/views/project.py`:
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Project


def project_list(request):
    """项目列表"""
    search = request.GET.get('search', '')
    projects = Project.objects.all()
    if search:
        projects = projects.filter(name__icontains=search)
    projects = projects.prefetch_related('modules')
    return render(request, 'project/list.html', {
        'projects': projects,
        'search': search,
        'nav_project': 'active',
    })


def project_create(request):
    """创建项目"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()

        if not name:
            messages.error(request, '项目名称不能为空')
            return render(request, 'project/form.html', {
                'nav_project': 'active',
                'form_data': request.POST,
            })

        if Project.objects.filter(name=name).exists():
            messages.error(request, f'项目 "{name}" 已存在')
            return render(request, 'project/form.html', {
                'nav_project': 'active',
                'form_data': request.POST,
            })

        Project.objects.create(name=name, description=description, created_by=created_by)
        messages.success(request, f'项目 "{name}" 创建成功')
        return redirect('project_list')

    return render(request, 'project/form.html', {'nav_project': 'active'})


def project_update(request, pk):
    """编辑项目"""
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()

        if not name:
            messages.error(request, '项目名称不能为空')
            return render(request, 'project/form.html', {
                'project': project,
                'nav_project': 'active',
                'form_data': request.POST,
            })

        if Project.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, f'项目 "{name}" 已存在')
            return render(request, 'project/form.html', {
                'project': project,
                'nav_project': 'active',
                'form_data': request.POST,
            })

        project.name = name
        project.description = description
        project.created_by = created_by
        project.save()
        messages.success(request, f'项目 "{name}" 更新成功')
        return redirect('project_list')

    return render(request, 'project/form.html', {
        'project': project,
        'nav_project': 'active',
    })


def project_delete(request, pk):
    """删除项目"""
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'项目 "{name}" 已删除')
        return redirect('project_list')

    return render(request, 'project/list.html', {'nav_project': 'active'})
```

- [ ] **Step 3: 编写项目列表模板**

Write `templates/project/list.html`:
```html
{% extends "base.html" %}

{% block title %}项目管理 - Pytest 测试平台{% endblock %}
{% block nav_project %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4><i class="bi bi-folder"></i> 项目管理</h4>
    </div>
</div>

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <span>项目列表</span>
        <div class="d-flex gap-2">
            <form method="get" class="d-flex">
                <input type="text" name="search" class="form-control form-control-sm" placeholder="搜索项目..." value="{{ search }}">
                <button type="submit" class="btn btn-sm btn-outline-secondary ms-1">
                    <i class="bi bi-search"></i>
                </button>
            </form>
            <a href="{% url 'project_create' %}" class="btn btn-sm btn-primary">
                <i class="bi bi-plus-lg"></i> 新增项目
            </a>
        </div>
    </div>
    <div class="card-body">
        <table class="table table-hover table-striped mb-0">
            <thead>
                <tr>
                    <th width="5%">#</th>
                    <th width="20%">项目名称</th>
                    <th width="25%">描述</th>
                    <th width="10%">创建人</th>
                    <th width="10%">模块数</th>
                    <th width="15%">更新时间</th>
                    <th width="15%">操作</th>
                </tr>
            </thead>
            <tbody>
                {% for project in projects %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ project.name }}</td>
                    <td>{{ project.description|default:"-"|truncatechars:30 }}</td>
                    <td>{{ project.created_by|default:"-" }}</td>
                    <td>{{ project.modules.count }}</td>
                    <td>{{ project.updated_at|date:"Y-m-d H:i" }}</td>
                    <td>
                        <div class="btn-group">
                            <a href="{% url 'project_update' project.pk %}" class="btn btn-sm btn-outline-primary" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <button type="button" class="btn btn-sm btn-outline-danger" title="删除"
                                    onclick="confirmDelete('{% url 'project_delete' project.pk %}', '{{ project.name }}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">暂无项目，点击上方按钮新增</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 编写项目表单模板**

Write `templates/project/form.html`:
```html
{% extends "base.html" %}

{% block title %}{% if project %}编辑项目{% else %}新增项目{% endif %} - Pytest 测试平台{% endblock %}
{% block nav_project %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4>
            <i class="bi bi-folder"></i>
            {% if project %}编辑项目{% else %}新增项目{% endif %}
        </h4>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            <div class="mb-3">
                <label for="name" class="form-label">项目名称 <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="name" name="name"
                       value="{% if form_data %}{{ form_data.name }}{% elif project %}{{ project.name }}{% endif %}"
                       required>
            </div>
            <div class="mb-3">
                <label for="description" class="form-label">项目描述</label>
                <textarea class="form-control" id="description" name="description" rows="3">{% if form_data %}{{ form_data.description }}{% elif project %}{{ project.description }}{% endif %}</textarea>
            </div>
            <div class="mb-3">
                <label for="created_by" class="form-label">创建人</label>
                <input type="text" class="form-control" id="created_by" name="created_by"
                       value="{% if form_data %}{{ form_data.created_by }}{% elif project %}{{ project.created_by }}{% endif %}">
            </div>
            <div class="d-flex gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
                <a href="{% url 'project_list' %}" class="btn btn-secondary">
                    <i class="bi bi-x-lg"></i> 取消
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add project management views and templates"
```

---

### Task 5: 模块管理视图和模板

**Files:**
- Create: `api/views/module.py`
- Create: `templates/module/list.html`
- Create: `templates/module/form.html`

- [ ] **Step 1: 创建模板目录**

Run:
```bash
mkdir -p f:/work/openAItest/templates/module
```

- [ ] **Step 2: 编写模块管理视图**

Write `api/views/module.py`:
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Module, Project


def module_list(request):
    """模块列表"""
    project_id = request.GET.get('project', '')
    search = request.GET.get('search', '')
    modules = Module.objects.select_related('project').all()

    if project_id:
        modules = modules.filter(project_id=project_id)
    if search:
        modules = modules.filter(name__icontains=search)

    projects = Project.objects.all()
    return render(request, 'module/list.html', {
        'modules': modules,
        'projects': projects,
        'current_project': project_id,
        'search': search,
        'nav_module': 'active',
    })


def module_create(request):
    """创建模块"""
    projects = Project.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not project_id or not name:
            messages.error(request, '项目 和模块名称不能为空')
            return render(request, 'module/form.html', {
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })

        project = get_object_or_404(Project, pk=project_id)

        if Module.objects.filter(project=project, name=name).exists():
            messages.error(request, f'模块 "{name}" 在该项目下已存在')
            return render(request, 'module/form.html', {
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })

        Module.objects.create(project=project, name=name, description=description)
        messages.success(request, f'模块 "{name}" 创建成功')
        return redirect('module_list')

    return render(request, 'module/form.html', {
        'projects': projects,
        'nav_module': 'active',
    })


def module_update(request, pk):
    """编辑模块"""
    module = get_object_or_404(Module, pk=pk)
    projects = Project.objects.all()

    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not project_id or not name:
            messages.error(request, '项目和模块名称不能为空')
            return render(request, 'module/form.html', {
                'module': module,
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })

        project = get_object_or_404(Project, pk=project_id)

        if Module.objects.filter(project=project, name=name).exclude(pk=pk).exists():
            messages.error(request, f'模块 "{name}" 在该项目下已存在')
            return render(request, 'module/form.html', {
                'module': module,
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })

        module.project = project
        module.name = name
        module.description = description
        module.save()
        messages.success(request, f'模块 "{name}" 更新成功')
        return redirect('module_list')

    return render(request, 'module/form.html', {
        'module': module,
        'projects': projects,
        'nav_module': 'active',
    })


def module_delete(request, pk):
    """删除模块"""
    module = get_object_or_404(Module, pk=pk)

    if request.method == 'POST':
        name = module.name
        module.delete()
        messages.success(request, f'模块 "{name}" 已删除')
        return redirect('module_list')

    return redirect('module_list')
```

- [ ] **Step 3: 编写模块列表模板**

Write `templates/module/list.html`:
```html
{% extends "base.html" %}

{% block title %}模块管理 - Pytest 测试平台{% endblock %}
{% block nav_module %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4><i class="bi bi-diagram-3"></i> 模块管理</h4>
    </div>
</div>

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <span>模块列表</span>
        <div class="d-flex gap-2">
            <form method="get" class="d-flex">
                <select name="project" class="form-select form-select-sm" onchange="this.form.submit()">
                    <option value="">全部项目</option>
                    {% for p in projects %}
                    <option value="{{ p.pk }}" {% if current_project == p.pk|stringformat:"s" %}selected{% endif %}>
                        {{ p.name }}
                    </option>
                    {% endfor %}
                </select>
                <input type="text" name="search" class="form-control form-control-sm ms-1" placeholder="搜索模块..." value="{{ search }}">
                <button type="submit" class="btn btn-sm btn-outline-secondary ms-1">
                    <i class="bi bi-search"></i>
                </button>
            </form>
            <a href="{% url 'module_create' %}" class="btn btn-sm btn-primary">
                <i class="bi bi-plus-lg"></i> 新增模块
            </a>
        </div>
    </div>
    <div class="card-body">
        <table class="table table-hover table-striped mb-0">
            <thead>
                <tr>
                    <th width="5%">#</th>
                    <th width="20%">模块名称</th>
                    <th width="20%">所属项目</th>
                    <th width="25%">描述</th>
                    <th width="15%">更新时间</th>
                    <th width="15%">操作</th>
                </tr>
            </thead>
            <tbody>
                {% for module in modules %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ module.name }}</td>
                    <td><a href="{% url 'project_update' module.project.pk %}">{{ module.project.name }}</a></td>
                    <td>{{ module.description|default:"-"|truncatechars:30 }}</td>
                    <td>{{ module.updated_at|date:"Y-m-d H:i" }}</td>
                    <td>
                        <div class="btn-group">
                            <a href="{% url 'module_update' module.pk %}" class="btn btn-sm btn-outline-primary" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <button type="button" class="btn btn-sm btn-outline-danger" title="删除"
                                    onclick="confirmDelete('{% url 'module_delete' module.pk %}', '{{ module.name }}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">暂无模块，点击上方按钮新增</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 编写模块表单模板**

Write `templates/module/form.html`:
```html
{% extends "base.html" %}

{% block title %}{% if module %}编辑模块{% else %}新增模块{% endif %} - Pytest 测试平台{% endblock %}
{% block nav_module %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4>
            <i class="bi bi-diagram-3"></i>
            {% if module %}编辑模块{% else %}新增模块{% endif %}
        </h4>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            <div class="mb-3">
                <label for="project" class="form-label">所属项目 <span class="text-danger">*</span></label>
                <select class="form-select" id="project" name="project" required>
                    <option value="">请选择项目</option>
                    {% for p in projects %}
                    <option value="{{ p.pk }}"
                            {% if form_data and form_data.project == p.pk|stringformat:"s" %}selected
                            {% elif module and module.project.pk == p.pk %}selected{% endif %}>
                        {{ p.name }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            <div class="mb-3">
                <label for="name" class="form-label">模块名称 <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="name" name="name"
                       value="{% if form_data %}{{ form_data.name }}{% elif module %}{{ module.name }}{% endif %}"
                       required>
            </div>
            <div class="mb-3">
                <label for="description" class="form-label">模块描述</label>
                <textarea class="form-control" id="description" name="description" rows="3">{% if form_data %}{{ form_data.description }}{% elif module %}{{ module.description }}{% endif %}</textarea>
            </div>
            <div class="d-flex gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
                <a href="{% url 'module_list' %}" class="btn btn-secondary">
                    <i class="bi bi-x-lg"></i> 取消
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add module management views and templates"
```

---

### Task 6: 配置管理视图和模板

**Files:**
- Create: `api/views/config.py`
- Create: `templates/config/list.html`
- Create: `templates/config/form.html`

- [ ] **Step 1: 创建模板目录**

Run:
```bash
mkdir -p f:/work/openAItest/templates/config
```

- [ ] **Step 2: 编写配置管理视图**

Write `api/views/config.py`:
```python
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from ..models import Config, Module, Project


def config_list(request):
    """配置列表"""
    module_id = request.GET.get('module', '')
    project_id = request.GET.get('project', '')
    search = request.GET.get('search', '')
    configs = Config.objects.select_related('module', 'module__project').all()

    if module_id:
        configs = configs.filter(module_id=module_id)
    if project_id:
        configs = configs.filter(module__project_id=project_id)
    if search:
        configs = configs.filter(name__icontains=search)

    projects = Project.objects.all()
    modules = Module.objects.all()
    if project_id:
        modules = modules.filter(project_id=project_id)

    return render(request, 'config/list.html', {
        'configs': configs,
        'projects': projects,
        'modules': modules,
        'current_project': project_id,
        'current_module': module_id,
        'search': search,
        'nav_config': 'active',
    })


def config_create(request):
    """创建配置"""
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()

    if request.method == 'POST':
        module_id = request.POST.get('module', '')
        name = request.POST.get('name', '').strip()
        env_type = request.POST.get('env_type', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        variables = request.POST.get('variables', '{}')
        parameters = request.POST.get('parameters', '{}')
        request_hooks = request.POST.get('request_hooks', '{}')
        response_hooks = request.POST.get('response_hooks', '{}')

        if not module_id or not name:
            messages.error(request, '模块和配置名称不能为空')
            return render(request, 'config/form.html', {
                'projects': projects,
                'modules': modules,
                'nav_config': 'active',
                'form_data': request.POST,
            })

        module = get_object_or_404(Module, pk=module_id)

        try:
            variables_json = json.loads(variables) if variables else {}
            parameters_json = json.loads(parameters) if parameters else {}
            request_hooks_json = json.loads(request_hooks) if request_hooks else {}
            response_hooks_json = json.loads(response_hooks) if response_hooks else {}
        except json.JSONDecodeError as e:
            messages.error(request, f'JSON 格式错误: {e}')
            return render(request, 'config/form.html', {
                'projects': projects,
                'modules': modules,
                'nav_config': 'active',
                'form_data': request.POST,
            })

        Config.objects.create(
            module=module, name=name, env_type=env_type, created_by=created_by,
            variables=variables_json, parameters=parameters_json,
            request_hooks=request_hooks_json, response_hooks=response_hooks_json,
        )
        messages.success(request, f'配置 "{name}" 创建成功')
        return redirect('config_list')

    return render(request, 'config/form.html', {
        'projects': projects,
        'modules': modules,
        'nav_config': 'active',
    })


def config_update(request, pk):
    """编辑配置"""
    config = get_object_or_404(Config, pk=pk)
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()

    if request.method == 'POST':
        module_id = request.POST.get('module', '')
        name = request.POST.get('name', '').strip()
        env_type = request.POST.get('env_type', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        variables = request.POST.get('variables', '{}')
        parameters = request.POST.get('parameters', '{}')
        request_hooks = request.POST.get('request_hooks', '{}')
        response_hooks = request.POST.get('response_hooks', '{}')

        if not module_id or not name:
            messages.error(request, '模块和配置名称不能为空')
            return render(request, 'config/form.html', {
                'config': config,
                'projects': projects,
                'modules': modules,
                'nav_config': 'active',
                'form_data': request.POST,
            })

        module = get_object_or_404(Module, pk=module_id)

        try:
            variables_json = json.loads(variables) if variables else {}
            parameters_json = json.loads(parameters) if parameters else {}
            request_hooks_json = json.loads(request_hooks) if request_hooks else {}
            response_hooks_json = json.loads(response_hooks) if response_hooks else {}
        except json.JSONDecodeError as e:
            messages.error(request, f'JSON 格式错误: {e}')
            return render(request, 'config/form.html', {
                'config': config,
                'projects': projects,
                'modules': modules,
                'nav_config': 'active',
                'form_data': request.POST,
            })

        config.module = module
        config.name = name
        config.env_type = env_type
        config.created_by = created_by
        config.variables = variables_json
        config.parameters = parameters_json
        config.request_hooks = request_hooks_json
        config.response_hooks = response_hooks_json
        config.save()
        messages.success(request, f'配置 "{name}" 更新成功')
        return redirect('config_list')

    return render(request, 'config/form.html', {
        'config': config,
        'projects': projects,
        'modules': modules,
        'nav_config': 'active',
    })


def config_delete(request, pk):
    """删除配置"""
    config = get_object_or_404(Config, pk=pk)

    if request.method == 'POST':
        name = config.name
        config.delete()
        messages.success(request, f'配置 "{name}" 已删除')
        return redirect('config_list')

    return redirect('config_list')


def load_modules(request):
    """根据项目ID加载模块列表（AJAX）"""
    project_id = request.GET.get('project_id', '')
    modules = Module.objects.filter(project_id=project_id).values('id', 'name') if project_id else []
    return JsonResponse(list(modules), safe=False)
```

- [ ] **Step 3: 编写配置列表模板**

Write `templates/config/list.html`:
```html
{% extends "base.html" %}

{% block title %}配置管理 - Pytest 测试平台{% endblock %}
{% block nav_config %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4><i class="bi bi-gear"></i> 配置管理</h4>
    </div>
</div>

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <span>配置列表</span>
        <div class="d-flex gap-2">
            <form method="get" class="d-flex">
                <select name="project" class="form-select form-select-sm" id="filter-project">
                    <option value="">全部项目</option>
                    {% for p in projects %}
                    <option value="{{ p.pk }}" {% if current_project == p.pk|stringformat:"s" %}selected{% endif %}>
                        {{ p.name }}
                    </option>
                    {% endfor %}
                </select>
                <select name="module" class="form-select form-select-sm ms-1" id="filter-module">
                    <option value="">全部模块</option>
                    {% for m in modules %}
                    <option value="{{ m.pk }}" {% if current_module == m.pk|stringformat:"s" %}selected{% endif %}>
                        {{ m.name }}
                    </option>
                    {% endfor %}
                </select>
                <button type="submit" class="btn btn-sm btn-outline-secondary ms-1">
                    <i class="bi bi-search"></i>
                </button>
            </form>
            <a href="{% url 'config_create' %}" class="btn btn-sm btn-primary">
                <i class="bi bi-plus-lg"></i> 新增配置
            </a>
        </div>
    </div>
    <div class="card-body">
        <table class="table table-hover table-striped mb-0">
            <thead>
                <tr>
                    <th width="5%">#</th>
                    <th width="15%">配置名称</th>
                    <th width="15%">所属模块</th>
                    <th width="10%">所属项目</th>
                    <th width="10%">环境</th>
                    <th width="10%">创建人</th>
                    <th width="15%">更新时间</th>
                    <th width="15%">操作</th>
                </tr>
            </thead>
            <tbody>
                {% for config in configs %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ config.name }}</td>
                    <td>{{ config.module.name }}</td>
                    <td>{{ config.module.project.name }}</td>
                    <td><span class="badge bg-{% if config.env_type == 'PROD' %}danger{% elif config.env_type == 'QA' %}warning{% else %}info{% endif %}">{{ config.get_env_type_display }}</span></td>
                    <td>{{ config.created_by|default:"-" }}</td>
                    <td>{{ config.updated_at|date:"Y-m-d H:i" }}</td>
                    <td>
                        <div class="btn-group">
                            <a href="{% url 'config_update' config.pk %}" class="btn btn-sm btn-outline-primary" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <button type="button" class="btn btn-sm btn-outline-danger" title="删除"
                                    onclick="confirmDelete('{% url 'config_delete' config.pk %}', '{{ config.name }}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">暂无配置，点击上方按钮新增</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// 项目筛选联动模块
$('#filter-project').change(function() {
    const projectId = $(this).val();
    const moduleSelect = $('#filter-module');
    moduleSelect.empty().append('<option value="">全部模块</option>');
    if (projectId) {
        $.get('{% url "load_modules" %}', {project_id: projectId}, function(data) {
            data.forEach(function(m) {
                moduleSelect.append('<option value="' + m.id + '">' + m.name + '</option>');
            });
        });
    }
});
</script>
{% endblock %}
```

- [ ] **Step 4: 编写配置表单模板**

Write `templates/config/form.html`:
```html
{% extends "base.html" %}

{% block title %}{% if config %}编辑配置{% else %}新增配置{% endif %} - Pytest 测试平台{% endblock %}
{% block nav_config %}active{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col">
        <h4>
            <i class="bi bi-gear"></i>
            {% if config %}编辑配置{% else %}新增配置{% endif %}
        </h4>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <form method="post" id="config-form">
            {% csrf_token %}

            <!-- 基本信息 -->
            <ul class="nav nav-tabs mb-3" role="tablist">
                <li class="nav-item">
                    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#basic" type="button">基本信息</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#vars" type="button">全局变量</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#hooks" type="button">Hooks</button>
                </li>
            </ul>

            <div class="tab-content">
                <!-- 基本信息 Tab -->
                <div class="tab-pane fade show active" id="basic">
                    <div class="mb-3">
                        <label for="project" class="form-label">所属项目 <span class="text-danger">*</span></label>
                        <select class="form-select" id="project-select">
                            <option value="">请选择项目</option>
                            {% for p in projects %}
                            <option value="{{ p.pk }}"
                                    {% if config and config.module.project.pk == p.pk %}selected
                                    {% elif form_data and form_data.project == p.pk|stringformat:"s" %}selected{% endif %}>
                                {{ p.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="module" class="form-label">所属模块 <span class="text-danger">*</span></label>
                        <select class="form-select" id="module" name="module" required>
                            <option value="">请先选择项目</option>
                            {% for m in modules %}
                            <option value="{{ m.pk }}" data-project="{{ m.project.pk }}"
                                    {% if config and config.module.pk == m.pk %}selected
                                    {% elif form_data and form_data.module == m.pk|stringformat:"s" %}selected{% endif %}>
                                {{ m.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="name" class="form-label">配置名称 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="name" name="name"
                               value="{% if form_data %}{{ form_data.name }}{% elif config %}{{ config.name }}{% endif %}"
                               required>
                    </div>
                    <div class="mb-3">
                        <label for="env_type" class="form-label">环境类型</label>
                        <select class="form-select" id="env_type" name="env_type">
                            <option value="DEV" {% if config and config.env_type == 'DEV' %}selected{% elif form_data and form_data.env_type == 'DEV' %}selected{% endif %}>开发环境</option>
                            <option value="QA" {% if config and config.env_type == 'QA' %}selected{% elif form_data and form_data.env_type == 'QA' %}selected{% endif %}>测试环境</option>
                            <option value="PROD" {% if config and config.env_type == 'PROD' %}selected{% elif form_data and form_data.env_type == 'PROD' %}selected{% endif %}>生产环境</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="created_by" class="form-label">创建人</label>
                        <input type="text" class="form-control" id="created_by" name="created_by"
                               value="{% if form_data %}{{ form_data.created_by }}{% elif config %}{{ config.created_by }}{% endif %}">
                    </div>
                </div>

                <!-- 全局变量 Tab -->
                <div class="tab-pane fade" id="vars">
                    <div class="mb-3">
                        <label for="variables" class="form-label">全局变量 (JSON)</label>
                        <textarea class="form-control font-monospace" id="variables" name="variables" rows="8">{% if form_data %}{{ form_data.variables }}{% elif config %}{{ config.variables|default:"{}" }}{% else %}{}{% endif %}</textarea>
                        <small class="text-muted">例: {"base_url": "http://api.example.com", "timeout": 30}</small>
                    </div>
                    <div class="mb-3">
                        <label for="parameters" class="form-label">公共请求参数 (JSON)</label>
                        <textarea class="form-control font-monospace" id="parameters" name="parameters" rows="8">{% if form_data %}{{ form_data.parameters }}{% elif config %}{{ config.parameters|default:"{}" }}{% else %}{}{% endif %}</textarea>
                        <small class="text-muted">例: {"headers": {"Content-Type": "application/json"}}</small>
                    </div>
                </div>

                <!-- Hooks Tab -->
                <div class="tab-pane fade" id="hooks">
                    <div class="mb-3">
                        <label for="request_hooks" class="form-label">请求 Hooks (JSON)</label>
                        <textarea class="form-control font-monospace" id="request_hooks" name="request_hooks" rows="8">{% if form_data %}{{ form_data.request_hooks }}{% elif config %}{{ config.request_hooks|default:"{}" }}{% else %}{}{% endif %}</textarea>
                        <small class="text-muted">例: {"setup": ["hook.add_token(request)"]}</small>
                    </div>
                    <div class="mb-3">
                        <label for="response_hooks" class="form-label">响应 Hooks (JSON)</label>
                        <textarea class="form-control font-monospace" id="response_hooks" name="response_hooks" rows="8">{% if form_data %}{{ form_data.response_hooks }}{% elif config %}{{ config.response_hooks|default:"{}" }}{% else %}{}{% endif %}</textarea>
                        <small class="text-muted">例: {"teardown": ["hook.log_response(response)"]}</small>
                    </div>
                </div>
            </div>

            <div class="d-flex gap-2 mt-3">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
                <a href="{% url 'config_list' %}" class="btn btn-secondary">
                    <i class="bi bi-x-lg"></i> 取消
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// 项目→模块联动
$('#project-select').change(function() {
    const projectId = $(this).val();
    const moduleSelect = $('#module');
    moduleSelect.empty().append('<option value="">请选择模块</option>');
    if (projectId) {
        $.get('{% url "load_modules" %}', {project_id: projectId}, function(data) {
            data.forEach(function(m) {
                moduleSelect.append('<option value="' + m.id + '">' + m.name + '</option>');
            });
        });
    }
});

// JSON 格式化
$('#config-form').submit(function() {
    ['variables', 'parameters', 'request_hooks', 'response_hooks'].forEach(function(field) {
        const el = $('#' + field);
        try {
            const parsed = JSON.parse(el.val());
            el.val(JSON.stringify(parsed, null, 2));
        } catch(e) {
            // 提交时由后端验证
        }
    });
});
</script>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add config management views and templates"
```

---

### Task 7: Dashboard 视图和 URL 配置

**Files:**
- Create: `api/views/dashboard.py`
- Create: `templates/dashboard.html`
- Modify: `api/urls.py`
- Modify: `pytest_platform/urls.py`

- [ ] **Step 1: 编写 Dashboard 视图**

Write `api/views/dashboard.py`:
```python
from django.shortcuts import render
from ..models import Project, Module, Config


def dashboard(request):
    """首页概览"""
    project_count = Project.objects.count()
    module_count = Module.objects.count()
    config_count = Config.objects.count()
    recent_projects = Project.objects.order_by('-updated_at')[:5]

    return render(request, 'dashboard.html', {
        'project_count': project_count,
        'module_count': module_count,
        'config_count': config_count,
        'recent_projects': recent_projects,
        'nav_dashboard': 'active',
    })
```

- [ ] **Step 2: 编写 Dashboard 模板**

Write `templates/dashboard.html`:
```html
{% extends "base.html" %}

{% block title %}首页概览 - Pytest 测试平台{% endblock %}
{% block nav_dashboard %}active{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col">
        <h4><i class="bi bi-speedometer2"></i> 首页概览</h4>
    </div>
</div>

<!-- 统计卡片 -->
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card stat-card">
            <div class="stat-number">{{ project_count }}</div>
            <div class="stat-label">项目总数</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card stat-card">
            <div class="stat-number">{{ module_count }}</div>
            <div class="stat-label">模块总数</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card stat-card">
            <div class="stat-number">{{ config_count }}</div>
            <div class="stat-label">配置总数</div>
        </div>
    </div>
</div>

<!-- 快捷操作 -->
<div class="row mb-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">快捷操作</div>
            <div class="card-body">
                <div class="d-flex flex-wrap gap-2">
                    <a href="{% url 'project_create' %}" class="btn btn-primary">
                        <i class="bi bi-plus-lg"></i> 新增项目
                    </a>
                    <a href="{% url 'module_create' %}" class="btn btn-outline-primary">
                        <i class="bi bi-plus-lg"></i> 新增模块
                    </a>
                    <a href="{% url 'config_create' %}" class="btn btn-outline-secondary">
                        <i class="bi bi-plus-lg"></i> 新增配置
                    </a>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">最近更新的项目</div>
            <div class="card-body">
                {% for project in recent_projects %}
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <a href="{% url 'project_update' project.pk %}">{{ project.name }}</a>
                    <small class="text-muted">{{ project.updated_at|date:"Y-m-d H:i" }}</small>
                </div>
                {% empty %}
                <p class="text-muted mb-0">暂无项目</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 3: 编写 api URL 配置**

Write `api/urls.py`:
```python
from django.urls import path
from .views import dashboard, project, module, config

app_name = 'api'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard, name='dashboard'),

    # 项目管理
    path('projects/', project.project_list, name='project_list'),
    path('projects/create/', project.project_create, name='project_create'),
    path('projects/<int:pk>/update/', project.project_update, name='project_update'),
    path('projects/<int:pk>/delete/', project.project_delete, name='project_delete'),

    # 模块管理
    path('modules/', module.module_list, name='module_list'),
    path('modules/create/', module.module_create, name='module_create'),
    path('modules/<int:pk>/update/', module.module_update, name='module_update'),
    path('modules/<int:pk>/delete/', module.module_delete, name='module_delete'),

    # 配置管理
    path('configs/', config.config_list, name='config_list'),
    path('configs/create/', config.config_create, name='config_create'),
    path('configs/<int:pk>/update/', config.config_update, name='config_update'),
    path('configs/<int:pk>/delete/', config.config_delete, name='config_delete'),
    path('configs/load-modules/', config.load_modules, name='load_modules'),
]
```

- [ ] **Step 4: 配置根 URL**

Modify `pytest_platform/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
]
```

- [ ] **Step 5: 验证所有 URL 可加载**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: add dashboard view and URL configuration"
```

---

### Task 8: 创建超级用户并验证功能

**Files:**
- None (verification only)

- [ ] **Step 1: 创建超级用户**

Run:
```bash
cd f:/work/openAItest && echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'admin123')" | .venv/Scripts/python.exe manage.py shell
```

- [ ] **Step 2: 启动开发服务器验证**

Run:
```bash
cd f:/work/openAItest && .venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000
```

验证以下功能:
- 访问 http://127.0.0.1:8000/ 可看到 Dashboard
- 项目列表页可正常显示
- 可创建/编辑/删除项目
- 模块列表页可按项目筛选
- 可创建/编辑/删除模块
- 配置列表页可按项目/模块筛选
- 可创建/编辑/删除配置
- 配置表单中项目→模块联动正常

- [ ] **Step 3: 通过 Admin 后台添加测试数据**

访问 http://127.0.0.1:8000/admin/ 登录后，添加一些测试数据验证列表展示。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: complete phase 1 - project, module, config CRUD"
```
