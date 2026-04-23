from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import auth as auth_views
from .views import dashboard as dashboard_views
from .views import project as project_views
from .views import module as module_views
from .views import config as config_views
from .views import testcase as testcase_views
from .views import ddt as ddt_views
from .views import scene as scene_views
from .views import task as task_views
from .views import report as report_views
from .views import script as script_views

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),

    # Dashboard
    path('', login_required(dashboard_views.dashboard), name='dashboard'),

    # 项目管理
    path('projects/', login_required(project_views.project_list), name='project_list'),
    path('projects/create/', login_required(project_views.project_create), name='project_create'),
    path('projects/<int:pk>/update/', login_required(project_views.project_update), name='project_update'),
    path('projects/<int:pk>/delete/', login_required(project_views.project_delete), name='project_delete'),
    path('projects/<int:pk>/project-configs/', login_required(project_views.project_config_list), name='project_config_list'),
    path('projects/<int:pk>/project-configs/create/', login_required(project_views.project_config_create), name='project_config_create'),
    path('projects/<int:pk>/project-configs/<int:cid>/update/', login_required(project_views.project_config_update), name='project_config_update'),
    path('projects/<int:pk>/project-configs/<int:cid>/delete/', login_required(project_views.project_config_delete), name='project_config_delete'),

    # 模块管理
    path('modules/', login_required(module_views.module_list), name='module_list'),
    path('modules/create/', login_required(module_views.module_create), name='module_create'),
    path('modules/<int:pk>/update/', login_required(module_views.module_update), name='module_update'),
    path('modules/<int:pk>/delete/', login_required(module_views.module_delete), name='module_delete'),

    # 配置管理
    path('configs/', login_required(config_views.config_list), name='config_list'),
    path('configs/create/', login_required(config_views.config_create), name='config_create'),
    path('configs/<int:pk>/update/', login_required(config_views.config_update), name='config_update'),
    path('configs/<int:pk>/delete/', login_required(config_views.config_delete), name='config_delete'),
    path('configs/load-modules/', login_required(config_views.load_modules), name='load_modules'),

    # 用例管理
    path('testcases/', login_required(testcase_views.testcase_list), name='testcase_list'),
    path('testcases/create/', login_required(testcase_views.testcase_create), name='testcase_create'),
    path('testcases/<int:pk>/update/', login_required(testcase_views.testcase_update), name='testcase_update'),
    path('testcases/<int:pk>/delete/', login_required(testcase_views.testcase_delete), name='testcase_delete'),

    # DDT 数据源
    path('ddt/', login_required(ddt_views.ddt_list), name='ddt_list'),
    path('ddt/create/', login_required(ddt_views.ddt_create), name='ddt_create'),
    path('ddt/<int:pk>/update/', login_required(ddt_views.ddt_update), name='ddt_update'),
    path('ddt/<int:pk>/delete/', login_required(ddt_views.ddt_delete), name='ddt_delete'),
    path('ddt/<int:pk>/preview/', login_required(ddt_views.ddt_preview), name='ddt_preview'),
    path('ddt/api/list/', login_required(ddt_views.ddt_list_api), name='ddt_list_api'),

    # 场景编排
    path('scenes/', login_required(scene_views.scene_list), name='scene_list'),
    path('scenes/create/', login_required(scene_views.scene_create), name='scene_create'),
    path('scenes/<int:pk>/update/', login_required(scene_views.scene_update), name='scene_update'),
    path('scenes/<int:pk>/delete/', login_required(scene_views.scene_delete), name='scene_delete'),
    path('scenes/<int:pk>/orchestrate/', login_required(scene_views.scene_orchestrate), name='scene_orchestrate'),
    path('scenes/<int:pk>/add-case/', login_required(scene_views.scene_add_case), name='scene_add_case'),
    path('scenes/<int:pk>/remove-case/<int:case_pk>/', login_required(scene_views.scene_remove_case), name='scene_remove_case'),
    path('scenes/<int:pk>/reorder/', login_required(scene_views.scene_reorder), name='scene_reorder'),
    path('scenes/api/testcases/', login_required(scene_views.scene_testcases_api), name='scene_testcases_api'),

    # 执行与调度
    path('tasks/', login_required(task_views.task_list), name='task_list'),
    path('tasks/create/', login_required(task_views.task_create), name='task_create'),
    path('tasks/<int:pk>/delete/', login_required(task_views.task_delete), name='task_delete'),
    path('tasks/<int:pk>/execute/', login_required(task_views.task_execute), name='task_execute'),
    path('tasks/<int:pk>/result/', login_required(task_views.task_result), name='task_result'),
    path('tasks/<int:pk>/status/', login_required(task_views.task_status), name='task_status'),
    path('testcases/<int:pk>/quick-run/', login_required(task_views.testcase_quick_run), name='testcase_quick_run'),

    # 报告中心
    path('reports/', login_required(report_views.report_list), name='report_list'),
    path('reports/<int:pk>/', login_required(report_views.report_detail), name='report_detail'),
    path('reports/<int:pk>/download/', login_required(report_views.report_download), name='report_download'),

    # 脚本管理
    path('scripts/', login_required(script_views.script_list), name='script_list'),
    path('scripts/functions/', login_required(script_views.hook_function_options), name='hook_function_options'),
    path('scripts/<int:pk>/edit/', login_required(script_views.script_update), name='script_update'),
    path('scripts/<int:pk>/validate/', login_required(script_views.script_validate), name='script_validate'),
]
