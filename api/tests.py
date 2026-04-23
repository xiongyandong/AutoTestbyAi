from django.contrib.auth import get_user_model
from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from .models import DDTSource, Module, Project, Scene, SceneCase, Task, TaskResult, TestCase as ApiTestCase


User = get_user_model()


class AuthFlowTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_dashboard_renders_command_center_sections(self):
        user = User.objects.create_user(username='dashboard_user', email='dashboard@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '质量总览')
        self.assertContains(response, '自动化平台总览')
        self.assertContains(response, '质量指标')
        self.assertContains(response, '最近7天执行趋势')
        self.assertContains(response, '结果速览')
        self.assertContains(response, '最新结果')
        self.assertContains(response, '最近测试报告')
        self.assertNotContains(response, '平台核心指标')

    def test_project_list_uses_shared_application_shell(self):
        user = User.objects.create_user(username='project_user', email='project@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('project_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-shell')
        self.assertContains(response, 'Automation Platform')
        self.assertContains(response, 'content-shell')

    def test_task_result_uses_dashboard_style_sections(self):
        user = User.objects.create_user(username='task_user', email='task@example.com', password='SecretPass123')
        project = Project.objects.create(name='订单平台', created_by='qa')
        module = Module.objects.create(project=project, name='支付模块')
        testcase = ApiTestCase.objects.create(
            module=module,
            name='支付成功',
            method='POST',
            url='https://example.com/pay',
        )
        task = Task.objects.create(
            task_name='支付回归',
            task_type='SYNC',
            status='COMPLETED',
            scope='TESTCASE',
            project=project,
            module=module,
            testcase=testcase,
            execute_env='QA',
        )
        TaskResult.objects.create(
            task=task,
            total_cases=10,
            passed=8,
            failed=1,
            error=1,
            skipped=0,
            duration=12.5,
            log='execution log',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('task_result', args=[task.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '任务总览')
        self.assertContains(response, '执行摘要')
        self.assertContains(response, '运行输出')

    def test_scene_orchestrate_uses_workspace_sections(self):
        user = User.objects.create_user(username='scene_user', email='scene@example.com', password='SecretPass123')
        project = Project.objects.create(name='会员平台', created_by='qa')
        module = Module.objects.create(project=project, name='登录模块')
        testcase = ApiTestCase.objects.create(
            module=module,
            name='登录成功',
            method='POST',
            url='https://example.com/login',
        )
        scene = Scene.objects.create(project=project, name='登录链路', created_by='qa')
        SceneCase.objects.create(scene=scene, testcase=testcase, order_index=1)
        self.client.force_login(user)

        response = self.client.get(reverse('scene_orchestrate', args=[scene.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '编排面板')
        self.assertContains(response, '候选用例')
        self.assertContains(response, '执行链路预览')

    def test_project_list_uses_list_workspace_sections(self):
        user = User.objects.create_user(username='list_user', email='list@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('project_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '项目管理')
        self.assertContains(response, '筛选')
        self.assertContains(response, '数据列表')

    def test_testcase_form_uses_form_workspace_sections(self):
        user = User.objects.create_user(username='form_user', email='form@example.com', password='SecretPass123')
        project = Project.objects.create(name='交易平台', created_by='qa')
        Module.objects.create(project=project, name='网关模块')
        self.client.force_login(user)

        response = self.client.get(reverse('testcase_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '新增用例')
        self.assertContains(response, '配置标签')
        self.assertContains(response, '保存当前用例配置')

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'tester',
            'email': 'tester@example.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        }, follow=True)

        self.assertTrue(User.objects.filter(username='tester', email='tester@example.com').exists())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_supports_email(self):
        User.objects.create_user(username='email_user', email='email@example.com', password='SecretPass123')
        response = self.client.post(reverse('login'), {
            'username': 'email@example.com',
            'password': 'SecretPass123',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_logout_clears_session(self):
        user = User.objects.create_user(username='logout_user', email='logout@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.post(reverse('logout'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class ScriptAssetModelTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def test_script_list_auto_creates_public_and_project_assets(self):
        user = User.objects.create_user(username='script_admin', email='script@example.com', password='SecretPass123')
        Project.objects.create(name='订单平台', created_by='qa')
        self.client.force_login(user)

        response = self.client.get(reverse('script_list'))

        ScriptAsset = self._script_model()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ScriptAsset.objects.filter(scope_type='PUBLIC', name='公共脚本配置').exists())
        self.assertTrue(ScriptAsset.objects.filter(scope_type='PROJECT', project__name='订单平台', name='订单平台脚本配置').exists())

    def test_project_create_also_creates_project_script_asset(self):
        user = User.objects.create_user(username='project_script_user', email='psu@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.post(reverse('project_create'), {
            'name': '会员平台',
            'description': 'desc',
            'created_by': 'qa',
        }, follow=True)

        ScriptAsset = self._script_model()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ScriptAsset.objects.filter(scope_type='PROJECT', project__name='会员平台', name='会员平台脚本配置').exists())


class ScriptListViewTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def setUp(self):
        self.user = User.objects.create_user(username='script_list_user', email='slu@example.com', password='SecretPass123')
        self.project_a = Project.objects.create(name='订单平台', created_by='qa')
        self.project_b = Project.objects.create(name='会员平台', created_by='qa')

    def test_script_list_renders_public_script_first(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('script_list'))

        self.assertEqual(response.status_code, 200)
        scripts = list(response.context['page_obj'].object_list)
        self.assertEqual(scripts[0].scope_type, 'PUBLIC')
        self.assertContains(response, '脚本管理')
        self.assertContains(response, '公共脚本配置')

    def test_script_list_can_filter_by_project_or_public(self):
        self.client.force_login(self.user)

        public_response = self.client.get(reverse('script_list'), {'project': 'PUBLIC'})
        project_response = self.client.get(reverse('script_list'), {'project': str(self.project_a.pk)})

        self.assertEqual(public_response.context['page_obj'].paginator.count, 1)
        self.assertEqual(project_response.context['page_obj'].paginator.count, 1)
        self.assertContains(project_response, '订单平台脚本配置')
        self.assertNotContains(project_response, '会员平台脚本配置')


class ScriptEngineTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def setUp(self):
        self.project = Project.objects.create(name='订单平台', created_by='qa')
        ScriptAsset = self._script_model()
        self.public_script = ScriptAsset.objects.create(
            scope_type='PUBLIC',
            name='公共脚本配置',
            content='def join_value(name, suffix):\n    return f"{name}-{suffix}"\n',
        )
        self.project_script = ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=self.project,
            name='订单平台脚本配置',
            content='def build_sign(token, env):\n    return f"{token}:{env}"\n',
        )

    def test_extract_function_index_returns_top_level_signatures(self):
        from .script_engine import extract_function_index

        signatures = extract_function_index(self.project_script.content)

        self.assertEqual(signatures, ['build_sign(token, env)'])

    def test_validate_python_script_reports_syntax_error(self):
        from .script_engine import validate_python_script

        result = validate_python_script('def broken(:\n    pass\n')

        self.assertFalse(result['ok'])
        self.assertEqual(result['line'], 1)

    def test_render_value_executes_project_function_before_public(self):
        from .script_engine import render_runtime_value

        context = {'token': 'abc', 'project_name': 'mall'}
        rendered = render_runtime_value('{{build_sign(${token}, "qa")}}', self.project, context)

        self.assertEqual(rendered, 'abc:qa')

    def test_render_nested_value_resolves_variable_values_that_contain_functions(self):
        from .script_engine import render_nested_value

        context = {
            'project_name': 'mall',
            'script_alias': '{{join_value(${project_name}, "qa")}}',
        }

        rendered = render_nested_value('${script_alias}', self.project, context)

        self.assertEqual(rendered, 'mall-qa')


class ScriptEditorViewTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def setUp(self):
        self.user = User.objects.create_user(username='script_editor_user', email='seu@example.com', password='SecretPass123')
        self.project = Project.objects.create(name='订单平台', created_by='qa')
        ScriptAsset = self._script_model()
        self.script = ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=self.project,
            name='订单平台脚本配置',
            content='def build_sign(token, env):\n    return f"{token}:{env}"\n',
        )

    def test_script_update_renders_dark_editor_workspace(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('script_update', args=[self.script.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '编辑脚本')
        self.assertContains(response, '函数预览')
        self.assertContains(response, 'CodeMirror')

    def test_script_validate_returns_syntax_error_json(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('script_validate', args=[self.script.pk]), {
            'content': 'def broken(:\n pass',
        })

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload['ok'])
        self.assertEqual(payload['line'], 1)


class ScriptRunnerIntegrationTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def test_render_request_fields_uses_project_and_runtime_variables(self):
        from .pytest_runner import PytestRunner

        project = Project.objects.create(name='订单平台', created_by='qa')
        module = Module.objects.create(project=project, name='支付模块')
        ScriptAsset = self._script_model()
        ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=project,
            name='订单平台脚本配置',
            content='def build_sign(token, env):\n    return f"{token}:{env}"\n',
        )
        testcase = ApiTestCase.objects.create(
            module=module,
            name='支付成功',
            method='POST',
            url='/pay/${token}',
            headers={'X-Sign': '{{build_sign(${token}, "QA")}}'},
            body={'request_id': '{{build_sign(${token}, "REQ")}}'},
        )

        rendered = PytestRunner._prepare_runtime_payload(
            testcase,
            env_config={'project_variables': {}, 'variables': {'token': 'abc'}, 'parameters': {}, 'base_url': 'https://example.com'},
            runtime_context={},
        )

        self.assertEqual(rendered['url'], 'https://example.com/pay/abc')
        self.assertEqual(rendered['headers']['X-Sign'], 'abc:QA')
        self.assertEqual(rendered['body']['request_id'], 'abc:REQ')

    def test_render_request_fields_resolves_env_variable_expressions(self):
        from .pytest_runner import PytestRunner

        project = Project.objects.create(name='商城平台', created_by='qa')
        module = Module.objects.create(project=project, name='登录模块')
        ScriptAsset = self._script_model()
        ScriptAsset.objects.create(
            scope_type='PUBLIC',
            name='公共脚本配置',
            content='def join_value(name, suffix):\n    return f"{name}-{suffix}"\n',
        )
        testcase = ApiTestCase.objects.create(
            module=module,
            name='登录成功',
            method='GET',
            url='/login',
            headers={'X-Env': '${script_alias}'},
        )

        rendered = PytestRunner._prepare_runtime_payload(
            testcase,
            env_config={
                'project_variables': {'project_name': 'mall'},
                'variables': {'script_alias': '{{join_value(${project_name}, "QA")}}'},
                'parameters': {},
                'base_url': 'https://example.com',
            },
            runtime_context={},
        )

        self.assertEqual(rendered['headers']['X-Env'], 'mall-QA')

    def test_generate_test_content_keeps_runtime_rendering_for_ddt_and_scene_vars(self):
        from .pytest_runner import PytestRunner

        project = Project.objects.create(name='履约平台', created_by='qa')
        module = Module.objects.create(project=project, name='下单模块')
        ScriptAsset = self._script_model()
        ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=project,
            name='履约平台脚本配置',
            content='def build_sign(token, env):\n    return f"{token}:{env}"\n',
        )
        testcase = ApiTestCase.objects.create(
            module=module,
            name='动态渲染',
            method='POST',
            url='/submit/${token}',
            headers={'X-Sign': '{{build_sign(${token}, "QA")}}'},
            body={'trace_id': '{{build_sign(${token}, "REQ")}}'},
            is_parameterized=True,
            ddt_source=DDTSource.objects.create(
                name='动态渲染数据',
                source_type='JSON',
                content='[{"token": "from-ddt"}]',
            ),
        )

        content = PytestRunner._generate_test_content(
            testcase,
            env_config={'project_variables': {}, 'variables': {}, 'parameters': {}, 'base_url': 'https://example.com'},
            shared_vars=['token'],
        )

        self.assertIn('from api.script_engine import render_nested_value', content)
        self.assertIn('runtime_context = {}', content)
        self.assertIn('runtime_context.update(shared_session_vars)', content)
        self.assertIn('runtime_context.update(ddt_params)', content)
        self.assertIn('url = render_nested_value', content)
        self.assertIn('headers = render_nested_value', content)
        self.assertIn('body_data = render_nested_value', content)

    def test_run_scene_shares_extracted_variables_between_cases(self):
        project = Project.objects.create(name='会员平台', created_by='qa')
        module = Module.objects.create(project=project, name='登录模块')
        first_case = ApiTestCase.objects.create(
            module=module,
            name='提取 token',
            method='GET',
            url='https://example.com/token',
            extractors={'token': {'type': 'regex', 'pattern': '"token":"(\\w+)"'}},
        )
        second_case = ApiTestCase.objects.create(
            module=module,
            name='使用 token',
            method='GET',
            url='https://example.com/use',
            headers={'X-Token': '${token}'},
        )
        scene = Scene.objects.create(project=project, name='登录链路', created_by='qa')
        first_scene_case = SceneCase.objects.create(scene=scene, testcase=first_case, order_index=1)
        second_scene_case = SceneCase.objects.create(scene=scene, testcase=second_case, order_index=2)

        calls = []

        class DummyResponse:
            def __init__(self, text):
                self.text = text
                self.status_code = 200

            def json(self):
                return {'token': 'abc123'}

        def fake_get(url, headers=None, params=None, timeout=30, **kwargs):
            calls.append({'url': url, 'headers': headers or {}, 'params': params or {}})
            if url.endswith('/token'):
                return DummyResponse('{"token":"abc123"}')
            return DummyResponse('ok')

        from unittest.mock import patch
        from .pytest_runner import PytestRunner

        with patch('requests.get', side_effect=fake_get):
            total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_scene(
                [first_scene_case, second_scene_case],
                env_config=None,
            )

        self.assertEqual((total, failed, error), (2, 0, 0))
        self.assertEqual(passed, 2)
        self.assertEqual(calls[1]['headers']['X-Token'], 'abc123')


class ScriptManagementRegressionTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def test_sidebar_includes_script_management_entry(self):
        user = User.objects.create_user(username='menu_user', email='menu@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, '脚本管理')

    def test_script_update_persists_function_index_after_save(self):
        user = User.objects.create_user(username='save_user', email='save@example.com', password='SecretPass123')
        project = Project.objects.create(name='商城平台', created_by='qa')
        ScriptAsset = self._script_model()
        script = ScriptAsset.objects.create(scope_type='PROJECT', project=project, name='商城平台脚本配置')
        self.client.force_login(user)

        response = self.client.post(reverse('script_update', args=[script.pk]), {
            'content': 'def create_code(prefix, num):\n    return f"{prefix}-{num}"\n',
        }, follow=True)

        script.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(script.function_index, ['create_code(prefix, num)'])


class CompactWorkspaceLayoutTests(TestCase):
    def test_project_list_uses_business_title_and_ten_per_page(self):
        user = User.objects.create_user(username='compact_project', email='cp@example.com', password='SecretPass123')
        for idx in range(12):
            Project.objects.create(name=f'项目{idx}', created_by='qa')
        self.client.force_login(user)

        response = self.client.get(reverse('project_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '项目管理')
        self.assertNotContains(response, '列表总览')
        self.assertEqual(response.context['page_obj'].paginator.per_page, 10)

    def test_task_list_uses_compact_business_title(self):
        user = User.objects.create_user(username='compact_list', email='cl@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('task_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '执行与调度')
        self.assertNotContains(response, '列表总览')

    def test_project_form_uses_real_action_title(self):
        user = User.objects.create_user(username='compact_form', email='cf@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('project_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '新增项目')
        self.assertNotContains(response, '编辑面板')

    def test_task_form_uses_real_action_title(self):
        user = User.objects.create_user(username='compact_task', email='ct@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('task_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '新建任务')
        self.assertNotContains(response, '编辑面板')

    def test_task_list_uses_ten_items_per_page(self):
        user = User.objects.create_user(username='compact_page_size', email='cps@example.com', password='SecretPass123')
        project = Project.objects.create(name='分页项目', created_by='qa')
        module = Module.objects.create(project=project, name='分页模块')
        for idx in range(12):
            Task.objects.create(
                task_name=f'任务{idx}',
                task_type='SYNC',
                status='PENDING',
                scope='MODULE',
                project=project,
                module=module,
                execute_env='QA',
            )
        self.client.force_login(user)

        response = self.client.get(reverse('task_list'))

        self.assertEqual(response.context['page_obj'].paginator.per_page, 10)
        self.assertEqual(len(response.context['page_obj'].object_list), 10)

    def test_target_list_pages_use_compact_search_button(self):
        user = User.objects.create_user(username='compact_search_btn', email='csb@example.com', password='SecretPass123')
        self.client.force_login(user)

        module_response = self.client.get(reverse('module_list'))
        task_response = self.client.get(reverse('task_list'))

        self.assertContains(module_response, 'compact-search-btn')
        self.assertContains(task_response, 'compact-search-btn')

    def test_task_list_filter_keeps_inline_search_layout(self):
        user = User.objects.create_user(username='task_filter_inline', email='tfi@example.com', password='SecretPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('task_list'))

        self.assertContains(response, 'task-filter-form')


class HookFunctionApiTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def setUp(self):
        self.user = User.objects.create_user(username='hook_api_user', email='hook-api@example.com', password='SecretPass123')
        self.project = Project.objects.create(name='Hook平台', created_by='qa')
        ScriptAsset = self._script_model()
        ScriptAsset.objects.create(
            scope_type='PUBLIC',
            name='公共脚本配置',
            function_index=['clear_cache()', 'seed_data(name, count)'],
        )
        ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=self.project,
            name='Hook平台脚本配置',
            function_index=['prepare_env(env)', 'cleanup_env()'],
        )
        self.client.force_login(self.user)

    def test_hook_function_options_include_public_and_project_functions(self):
        response = self.client.get(reverse('hook_function_options'), {'project_id': self.project.pk})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item['name'] for item in payload],
            ['clear_cache', 'seed_data', 'prepare_env', 'cleanup_env'],
        )
        self.assertEqual(payload[0]['scope'], 'PUBLIC')
        self.assertEqual(payload[-1]['scope'], 'PROJECT')


class HookFormSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hook_form_user', email='hook-form@example.com', password='SecretPass123')
        self.project = Project.objects.create(name='订单中心', created_by='qa')
        self.module = Module.objects.create(project=self.project, name='交易模块')
        self.client.force_login(self.user)

    def test_config_create_accepts_hook_expression_lists(self):
        response = self.client.post(reverse('config_create'), {
            'module': self.module.pk,
            'name': '测试环境',
            'base_url': 'https://example.com',
            'env_type': 'QA',
            'created_by': 'qa',
            'variables': '{}',
            'parameters': '{}',
            'request_hooks': '["{{prepare_env(\\"qa\\")}}"]',
            'response_hooks': '["{{cleanup_env()}}"]',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        config = self.module.configs.get(name='测试环境')
        self.assertEqual(config.request_hooks, ['{{prepare_env("qa")}}'])
        self.assertEqual(config.response_hooks, ['{{cleanup_env()}}'])

    def test_testcase_create_accepts_hook_expression_lists(self):
        response = self.client.post(reverse('testcase_create'), {
            'module': self.module.pk,
            'name': '登录成功',
            'method': 'GET',
            'url': 'https://example.com/login',
            'created_by': 'qa',
            'body_type': 'none',
            'headers': '{}',
            'params': '{}',
            'body': '{}',
            'extractors': '{}',
            'assertions': '[]',
            'setup_hooks': '["{{prepare_case(${token})}}"]',
            'teardown_hooks': '["{{cleanup_case()}}"]',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        testcase = self.module.testcases.get(name='登录成功')
        self.assertEqual(testcase.setup_hooks, ['{{prepare_case(${token})}}'])
        self.assertEqual(testcase.teardown_hooks, ['{{cleanup_case()}}'])


class HookExecutionTests(TestCase):
    def _script_model(self):
        return apps.get_model('api', 'ScriptAsset')

    def setUp(self):
        self.project = Project.objects.create(name='执行平台', created_by='qa')
        self.module = Module.objects.create(project=self.project, name='执行模块')
        ScriptAsset = self._script_model()
        ScriptAsset.objects.create(
            scope_type='PROJECT',
            project=self.project,
            name='执行平台脚本配置',
            content=(
                'HOOK_LOG = []\n'
                'def env_before(env):\n'
                '    HOOK_LOG.append(f"env_before:{env}")\n'
                'def case_before(token):\n'
                '    HOOK_LOG.append(f"case_before:{token}")\n'
                'def case_after(name):\n'
                '    HOOK_LOG.append(f"case_after:{name}")\n'
                'def env_after(label):\n'
                '    HOOK_LOG.append(f"env_after:{label}")\n'
                'def explode():\n'
                '    raise RuntimeError("boom")\n'
            ),
        )

    def test_run_single_testcase_executes_env_and_case_hooks(self):
        from .pytest_runner import PytestRunner
        from .script_engine import load_script_functions
        testcase = ApiTestCase.objects.create(
            module=self.module,
            name='单用例 hooks',
            method='GET',
            url='https://example.com/run',
            setup_hooks=['{{case_before(${token})}}'],
            teardown_hooks=['{{case_after("single")}}'],
        )
        env_config = {
            'project_variables': {},
            'variables': {'token': 'abc'},
            'parameters': {},
            'base_url': '',
            'request_hooks': ['{{env_before("qa")}}'],
            'response_hooks': ['{{env_after("done")}}'],
        }

        class DummyResponse:
            status_code = 200
            text = 'ok'

            def json(self):
                return {}

        from unittest.mock import patch
        with patch('requests.get', return_value=DummyResponse()):
            total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_single_testcase(testcase, env_config)

        hook_log = load_script_functions(self.project)['env_before'].__globals__['HOOK_LOG']
        self.assertEqual((total, passed, failed, error, skipped), (1, 1, 0, 0, 0))
        self.assertEqual(hook_log, ['env_before:qa', 'case_before:abc', 'case_after:single', 'env_after:done'])

    def test_run_scene_executes_env_hooks_once_and_case_hooks_per_case(self):
        from .pytest_runner import PytestRunner
        from .script_engine import load_script_functions
        first_case = ApiTestCase.objects.create(
            module=self.module,
            name='提取 token',
            method='GET',
            url='https://example.com/token',
            extractors={'token': {'type': 'regex', 'pattern': '"token":"(\\w+)"'}},
            setup_hooks=['{{case_before("first")}}'],
            teardown_hooks=['{{case_after("first")}}'],
        )
        second_case = ApiTestCase.objects.create(
            module=self.module,
            name='使用 token',
            method='GET',
            url='https://example.com/use',
            headers={'X-Token': '${token}'},
            setup_hooks=['{{case_before(${token})}}'],
            teardown_hooks=['{{case_after("second")}}'],
        )
        scene = Scene.objects.create(project=self.project, name='hooks 场景', created_by='qa')
        first_scene_case = SceneCase.objects.create(scene=scene, testcase=first_case, order_index=1)
        second_scene_case = SceneCase.objects.create(scene=scene, testcase=second_case, order_index=2)
        env_config = {
            'project_variables': {},
            'variables': {},
            'parameters': {},
            'base_url': '',
            'request_hooks': ['{{env_before("scene")}}'],
            'response_hooks': ['{{env_after("scene_done")}}'],
        }

        class DummyResponse:
            def __init__(self, text):
                self.status_code = 200
                self.text = text

            def json(self):
                return {'token': 'abc123'}

        def fake_get(url, headers=None, params=None, timeout=30, **kwargs):
            if url.endswith('/token'):
                return DummyResponse('{"token":"abc123"}')
            return DummyResponse('ok')

        from unittest.mock import patch
        with patch('requests.get', side_effect=fake_get):
            total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_scene(
                [first_scene_case, second_scene_case],
                env_config=env_config,
            )

        hook_log = load_script_functions(self.project)['env_before'].__globals__['HOOK_LOG']
        self.assertEqual((total, passed, failed, error, skipped), (2, 2, 0, 0, 0))
        self.assertEqual(
            hook_log,
            ['env_before:scene', 'case_before:first', 'case_after:first', 'case_before:abc123', 'case_after:second', 'env_after:scene_done'],
        )

    def test_response_hooks_still_run_when_request_hooks_fail(self):
        from .pytest_runner import PytestRunner
        from .script_engine import load_script_functions
        testcase = ApiTestCase.objects.create(
            module=self.module,
            name='失败 hooks',
            method='GET',
            url='https://example.com/run',
        )
        env_config = {
            'project_variables': {},
            'variables': {},
            'parameters': {},
            'base_url': '',
            'request_hooks': ['{{explode()}}'],
            'response_hooks': ['{{env_after("cleanup")}}'],
        }

        total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_single_testcase(testcase, env_config)

        hook_log = load_script_functions(self.project)['env_before'].__globals__['HOOK_LOG']
        self.assertEqual((total, passed, failed, error, skipped), (0, 0, 0, 1, 0))
        self.assertIn('explode', log)
        self.assertEqual(hook_log, ['env_after:cleanup'])
