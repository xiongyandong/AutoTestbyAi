from django.urls import path
from .views import dashboard as dashboard_views
from .views import project as project_views
from .views import module as module_views
from .views import config as config_views

urlpatterns = [
    # Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),

    # 项目管理
    path('projects/', project_views.project_list, name='project_list'),
    path('projects/create/', project_views.project_create, name='project_create'),
    path('projects/<int:pk>/update/', project_views.project_update, name='project_update'),
    path('projects/<int:pk>/delete/', project_views.project_delete, name='project_delete'),

    # 模块管理
    path('modules/', module_views.module_list, name='module_list'),
    path('modules/create/', module_views.module_create, name='module_create'),
    path('modules/<int:pk>/update/', module_views.module_update, name='module_update'),
    path('modules/<int:pk>/delete/', module_views.module_delete, name='module_delete'),

    # 配置管理
    path('configs/', config_views.config_list, name='config_list'),
    path('configs/create/', config_views.config_create, name='config_create'),
    path('configs/<int:pk>/update/', config_views.config_update, name='config_update'),
    path('configs/<int:pk>/delete/', config_views.config_delete, name='config_delete'),
    path('configs/load-modules/', config_views.load_modules, name='load_modules'),
]
