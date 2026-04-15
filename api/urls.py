from django.urls import path
from .views import dashboard as dashboard_views
from .views import project as project_views
from .views import module as module_views
from .views import config as config_views
from .views import testcase as testcase_views
from .views import ddt as ddt_views
from .views import scene as scene_views

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

    # 用例管理
    path('testcases/', testcase_views.testcase_list, name='testcase_list'),
    path('testcases/create/', testcase_views.testcase_create, name='testcase_create'),
    path('testcases/<int:pk>/update/', testcase_views.testcase_update, name='testcase_update'),
    path('testcases/<int:pk>/delete/', testcase_views.testcase_delete, name='testcase_delete'),

    # DDT 数据源
    path('ddt/', ddt_views.ddt_list, name='ddt_list'),
    path('ddt/create/', ddt_views.ddt_create, name='ddt_create'),
    path('ddt/<int:pk>/update/', ddt_views.ddt_update, name='ddt_update'),
    path('ddt/<int:pk>/delete/', ddt_views.ddt_delete, name='ddt_delete'),
    path('ddt/<int:pk>/preview/', ddt_views.ddt_preview, name='ddt_preview'),
    path('ddt/api/list/', ddt_views.ddt_list_api, name='ddt_list_api'),

    # 场景编排
    path('scenes/', scene_views.scene_list, name='scene_list'),
    path('scenes/create/', scene_views.scene_create, name='scene_create'),
    path('scenes/<int:pk>/update/', scene_views.scene_update, name='scene_update'),
    path('scenes/<int:pk>/delete/', scene_views.scene_delete, name='scene_delete'),
    path('scenes/<int:pk>/orchestrate/', scene_views.scene_orchestrate, name='scene_orchestrate'),
    path('scenes/<int:pk>/add-case/', scene_views.scene_add_case, name='scene_add_case'),
    path('scenes/<int:pk>/remove-case/<int:case_pk>/', scene_views.scene_remove_case, name='scene_remove_case'),
    path('scenes/<int:pk>/reorder/', scene_views.scene_reorder, name='scene_reorder'),
    path('scenes/api/testcases/', scene_views.scene_testcases_api, name='scene_testcases_api'),
]
