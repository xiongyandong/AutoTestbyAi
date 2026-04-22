from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Module, Project, Scene, SceneCase, Task, TaskResult, TestCase as ApiTestCase


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
        self.assertContains(response, '列表总览')
        self.assertContains(response, '筛选条件')
        self.assertContains(response, '数据列表')

    def test_testcase_form_uses_form_workspace_sections(self):
        user = User.objects.create_user(username='form_user', email='form@example.com', password='SecretPass123')
        project = Project.objects.create(name='交易平台', created_by='qa')
        Module.objects.create(project=project, name='网关模块')
        self.client.force_login(user)

        response = self.client.get(reverse('testcase_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '编辑面板')
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
