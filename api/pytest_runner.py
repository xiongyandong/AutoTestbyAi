import os
import json
import time
import tempfile
import requests as http_requests
from pathlib import Path


def _ensure_dict(value, default=None):
    """确保 JSONField 值为 dict，处理双重编码的情况"""
    if value is None:
        return default or {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else (default or {})
        except (json.JSONDecodeError, TypeError):
            return default or {}
    return default or {}


def _ensure_list(value, default=None):
    """确保 JSONField 值为 list，处理双重编码的情况"""
    if value is None:
        return default or []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else (default or [])
        except (json.JSONDecodeError, TypeError):
            return default or []
    return default or []


class _ResultCollector:
    """pytest 插件：收集测试执行结果"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'error': 0,
            'skipped': 0,
            'total': 0,
        }
        self.log_lines = []

    def pytest_runtest_logreport(self, report):
        if report.when == 'setup':
            if report.failed:
                self.results['error'] += 1
                self.results['total'] += 1
                self.log_lines.append(f'ERROR: {report.nodeid} - setup failed')
            elif report.skipped:
                self.results['skipped'] += 1
                self.results['total'] += 1
        elif report.when == 'call':
            self.results['total'] += 1
            if report.passed:
                self.results['passed'] += 1
            elif report.failed:
                self.results['failed'] += 1
                self.log_lines.append(f'FAILED: {report.nodeid} - {report.longreprtext[:200]}')
            elif report.skipped:
                self.results['skipped'] += 1
        elif report.when == 'teardown':
            if report.failed:
                self.results['error'] += 1
                self.results['total'] += 1
                self.log_lines.append(f'ERROR: {report.nodeid} - teardown failed')


class PytestRunner:
    """测试执行引擎：动态生成 pytest 测试文件并执行"""

    @staticmethod
    def _generate_test_content(testcase, env_config=None, shared_vars=None):
        """根据 TestCase 模型动态生成 pytest 测试代码

        Args:
            testcase: TestCase 模型实例
            env_config: 环境配置 dict，含 variables 和 parameters
            shared_vars: 场景执行时用例间共享变量的变量名列表
        """
        method = testcase.method
        url = testcase.url
        headers = _ensure_dict(testcase.headers)
        params = _ensure_dict(testcase.params)
        body = _ensure_dict(testcase.body)
        extractors = _ensure_dict(testcase.extractors)
        assertions = _ensure_list(testcase.assertions)
        setup_hooks = _ensure_list(testcase.setup_hooks)
        teardown_hooks = _ensure_list(testcase.teardown_hooks)

        # 合并环境配置变量到 URL 中
        if env_config and env_config.get('variables'):
            variables = _ensure_dict(env_config['variables'])
            for key, val in variables.items():
                url = url.replace(f'${{{key}}}', str(val))
            # 合并 headers
            if env_config.get('parameters'):
                parameters = _ensure_dict(env_config['parameters'])
                env_headers = _ensure_dict(parameters.get('headers', {}))
                merged = {**env_headers, **headers}
                headers = merged

        # 生成代码
        lines = [
            'import pytest',
            'import requests',
            'import json',
            'import re',
            '',
            f'# Test: {testcase.name}',
            f'extracted_vars = {{}}',
            '',
        ]

        # 场景间变量注入：如果有共享变量，从 session 中读取
        if shared_vars:
            lines.append('# 共享变量注入（场景执行时用例间传递）')
            lines.append('def _inject_shared_vars(session_vars):')
            lines.append('    for k, v in session_vars.items():')
            lines.append('        globals()[k] = v')
            lines.append('')

        # 参数化支持
        if testcase.is_parameterized and testcase.ddt_source:
            ddt_content = testcase.ddt_source.content
            if testcase.ddt_source.source_type == 'JSON' and ddt_content:
                try:
                    ddt_data = json.loads(ddt_content)
                    if isinstance(ddt_data, list) and ddt_data:
                        param_ids = [f'case{i}' for i in range(len(ddt_data))]
                        lines.append(f'@pytest.mark.parametrize("ddt_params", {json.dumps(ddt_data)}, ids={json.dumps(param_ids)})')
                except json.JSONDecodeError:
                    pass

        # 测试函数
        has_param = testcase.is_parameterized and testcase.ddt_source
        func_args = []
        if has_param:
            func_args.append('ddt_params')
        if shared_vars:
            func_args.append('shared_session_vars')
        func_sig = f'def test_case({", ".join(func_args)}):'
        lines.append(func_sig)

        # 场景变量注入
        if shared_vars:
            lines.append('    _inject_shared_vars(shared_session_vars)')

        # 替换 URL 中的提取变量引用
        if extractors:
            for var_name in extractors:
                url = url.replace(f'${{{var_name}}}', f'" + str(globals().get("{var_name}", "")) + "')

        # 合并 DDT 参数到 body
        if has_param:
            lines.append('    body_data = {**' + json.dumps(body, ensure_ascii=False) + ', **ddt_params}')
        else:
            lines.append('    body_data = ' + json.dumps(body, ensure_ascii=False))

        lines.extend([
            '    # Send request',
            f'    response = requests.{method.lower()}(',
            f'        "{url}",',
            f'        headers={json.dumps(headers, ensure_ascii=False)},',
            f'        params={json.dumps(params, ensure_ascii=False)},',
        ])

        if method in ('POST', 'PUT', 'PATCH') and body:
            lines.append(f'        json=body_data,')
        lines.append('        timeout=30,')
        lines.append('    )')

        # 提取器
        if extractors:
            lines.append('')
            lines.append('    # Extractors')
            for var_name, extractor in extractors.items():
                if isinstance(extractor, dict):
                    ext_type = extractor.get('type', 'jsonpath')
                    if ext_type == 'jsonpath':
                        path = extractor.get('path', '')
                        lines.append(f'    try:')
                        lines.append(f'        import jsonpath_ng')
                        lines.append(f'        match = jsonpath_ng.parse("{path}").find(response.json())')
                        lines.append(f'        extracted_vars["{var_name}"] = match[0].value if match else None')
                        lines.append(f'        globals()["{var_name}"] = extracted_vars["{var_name}"]')
                        lines.append(f'    except Exception:')
                        lines.append(f'        extracted_vars["{var_name}"] = None')
                    elif ext_type == 'regex':
                        pattern = extractor.get('pattern', '')
                        lines.append(f'    match = re.search(r"{pattern}", response.text)')
                        lines.append(f'    extracted_vars["{var_name}"] = match.group(1) if match else None')
                        lines.append(f'    globals()["{var_name}"] = extracted_vars["{var_name}"]')

        # 断言
        if assertions:
            lines.append('')
            lines.append('    # Assertions')
            for assertion in assertions:
                if not isinstance(assertion, dict):
                    continue
                a_type = assertion.get('type', 'status_code')
                if a_type == 'status_code':
                    expected = assertion.get('expected', 200)
                    lines.append(f'    assert response.status_code == {expected}, f"Status code {{response.status_code}} != {expected}"')
                elif a_type == 'jsonpath':
                    path = assertion.get('path', '')
                    operator = assertion.get('operator', 'eq')
                    expected = assertion.get('expected')
                    lines.append(f'    json_data = response.json()')
                    lines.append(f'    try:')
                    lines.append(f'        import jsonpath_ng')
                    lines.append(f'        match = jsonpath_ng.parse("{path}").find(json_data)')
                    lines.append(f'        actual = match[0].value if match else None')
                    lines.append(f'    except Exception:')
                    lines.append(f'        actual = None')
                    if operator == 'eq':
                        lines.append(f'    assert actual == {json.dumps(expected)}, f"{{path}}: {{actual}} != {expected}"')
                    elif operator == 'contains':
                        lines.append(f'    assert {json.dumps(expected)} in str(actual), f"{{path}}: {{actual}} not contains {expected}"')
                    elif operator == 'not_eq':
                        lines.append(f'    assert actual != {json.dumps(expected)}, f"{{path}}: {{actual}} == {expected}"')
                    elif operator == 'gt':
                        lines.append(f'    assert actual > {expected}, f"{{path}}: {{actual}} not > {expected}"')
                    elif operator == 'lt':
                        lines.append(f'    assert actual < {expected}, f"{{path}}: {{actual}} not < {expected}"')
                    elif operator == 'regex':
                        pattern = assertion.get('pattern', '')
                        lines.append(f'    assert re.match(r"{pattern}", str(actual)), f"{{path}}: {{actual}} not match {pattern}"')

        # 场景执行时，将提取的变量写入 session
        if shared_vars and extractors:
            lines.append('')
            lines.append('    # 将提取的变量保存到 session 供后续用例使用')
            lines.append('    for k, v in extracted_vars.items():')
            lines.append('        shared_session_vars[k] = v')

        return '\n'.join(lines)

    @staticmethod
    def run_testcases(testcases, env_config=None, report_dir=None):
        """
        执行一组用例，返回 (total, passed, failed, error, skipped, duration, report_path, log)
        """
        if not testcases:
            return 0, 0, 0, 0, 0, 0, '', 'No test cases to run'

        if report_dir is None:
            report_dir = tempfile.mkdtemp(prefix='pytest_report_')
        os.makedirs(report_dir, exist_ok=True)

        # 生成测试文件（使用唯一文件名避免模块缓存冲突）
        test_file_path = os.path.join(report_dir, f'test_{os.path.basename(report_dir)}.py')
        contents = []
        for i, tc in enumerate(testcases):
            content = PytestRunner._generate_test_content(tc, env_config)
            # 重命名函数避免冲突
            content = content.replace('def test_case(', f'def test_case_{i}(')
            # 替换类级别变量
            content = content.replace('extracted_vars = {}', f'extracted_vars_{i} = {{}}')
            content = content.replace('extracted_vars[', f'extracted_vars_{i}[')
            content = content.replace('extracted_vars["', f'extracted_vars_{i}["')
            content = content.replace('extracted_vars.items()', f'extracted_vars_{i}.items()')
            content = content.replace('globals()["', f'globals()["')
            contents.append(content)

        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(contents))

        report_file = os.path.join(report_dir, 'report.html')

        start_time = time.time()

        import pytest
        collector = _ResultCollector()
        pytest.main([
            test_file_path,
            f'--html={report_file}',
            '--self-contained-html',
            '-v',
            '--tb=short',
            f'--rootdir={report_dir}',
            '--override-ini=collect_ignore_glob=*',
        ], plugins=[collector])

        duration = round(time.time() - start_time, 2)

        total = collector.results['total']
        passed = collector.results['passed']
        failed = collector.results['failed']
        error = collector.results['error']
        skipped = collector.results['skipped']

        log = '\n'.join(collector.log_lines) if collector.log_lines else \
            f'All {passed}/{total} passed. Duration: {duration}s'

        return total, passed, failed, error, skipped, duration, report_file, log

    @staticmethod
    def run_single_testcase(testcase, env_config=None):
        """运行单个用例"""
        return PytestRunner.run_testcases([testcase], env_config)

    @staticmethod
    def run_scene(scene_cases, env_config=None, report_dir=None):
        """
        执行场景（支持用例间变量传递）

        Args:
            scene_cases: SceneCase 查询集或列表（需按 order_index 排序）
            env_config: 环境配置
            report_dir: 报告目录

        Returns:
            (total, passed, failed, error, skipped, duration, report_path, log)
        """
        if not scene_cases:
            return 0, 0, 0, 0, 0, 0, '', 'No test cases in scene'

        if report_dir is None:
            report_dir = tempfile.mkdtemp(prefix='pytest_scene_')
        os.makedirs(report_dir, exist_ok=True)

        # 收集所有用例中需要共享的变量名
        all_extractors = set()
        for sc in scene_cases:
            tc = sc.testcase
            extractors = _ensure_dict(tc.extractors)
            if extractors:
                all_extractors.update(extractors.keys())
        shared_vars = list(all_extractors) if all_extractors else None

        # 生成测试文件
        test_file_path = os.path.join(report_dir, f'test_{os.path.basename(report_dir)}.py')

        # 在文件头部添加共享变量 session
        header_lines = [
            'import pytest',
            'import requests',
            'import json',
            'import re',
            '',
            '# 场景执行共享变量',
            'shared_session_vars = {}',
            '',
        ]

        contents = []
        for i, sc in enumerate(scene_cases):
            tc = sc.testcase
            content = PytestRunner._generate_test_content(tc, env_config, shared_vars=shared_vars)
            # 重命名函数避免冲突
            content = content.replace('def test_case(', f'def test_case_{i}(')
            # 替换类级别变量（每个测试函数内部有自己的 extracted_vars）
            content = content.replace('extracted_vars = {}', f'extracted_vars_{i} = {{}}')
            content = content.replace('extracted_vars[', f'extracted_vars_{i}[')
            content = content.replace('extracted_vars["', f'extracted_vars_{i}["')
            content = content.replace('extracted_vars.items()', f'extracted_vars_{i}.items()')
            contents.append(content)

        full_content = '\n'.join(header_lines) + '\n\n' + '\n\n'.join(contents)

        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        report_file = os.path.join(report_dir, 'report.html')

        start_time = time.time()

        import pytest
        collector = _ResultCollector()

        # 为场景执行添加 fixture，注入共享变量
        conftest_path = os.path.join(report_dir, 'conftest.py')
        conftest_content = '''
import pytest

@pytest.fixture
def shared_session_vars():
    return {}
'''
        with open(conftest_path, 'w', encoding='utf-8') as f:
            f.write(conftest_content)

        pytest.main([
            test_file_path,
            f'--html={report_file}',
            '--self-contained-html',
            '-v',
            '--tb=short',
            f'--rootdir={report_dir}',
            '--override-ini=collect_ignore_glob=*',
        ], plugins=[collector])

        duration = round(time.time() - start_time, 2)

        total = collector.results['total']
        passed = collector.results['passed']
        failed = collector.results['failed']
        error = collector.results['error']
        skipped = collector.results['skipped']

        log = '\n'.join(collector.log_lines) if collector.log_lines else \
            f'All {passed}/{total} passed. Duration: {duration}s'

        return total, passed, failed, error, skipped, duration, report_file, log
