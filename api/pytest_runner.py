import os
import json
import time
import tempfile
import requests as http_requests
from pathlib import Path


class PytestRunner:
    """测试执行引擎：动态生成 pytest 测试文件并执行"""

    @staticmethod
    def _generate_test_content(testcase, env_config=None):
        """根据 TestCase 模型动态生成 pytest 测试代码"""
        method = testcase.method
        url = testcase.url
        headers = testcase.headers or {}
        params = testcase.params or {}
        body = testcase.body or {}
        extractors = testcase.extractors or {}
        assertions = testcase.assertions or []
        setup_hooks = testcase.setup_hooks or []
        teardown_hooks = testcase.teardown_hooks or []

        # 合并环境配置变量到 URL 中
        if env_config and env_config.get('variables'):
            variables = env_config['variables']
            for key, val in variables.items():
                url = url.replace(f'${{{key}}}', str(val))
            # 合并 headers
            if env_config.get('parameters'):
                env_headers = env_config['parameters'].get('headers', {})
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
        func_sig = 'def test_case(ddt_params):' if has_param else 'def test_case():'
        lines.append(func_sig)

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

        if method in ('POST', 'PUT', 'PATCH') and body_data != {}:
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
                        lines.append(f'    except Exception:')
                        lines.append(f'        extracted_vars["{var_name}"] = None')
                    elif ext_type == 'regex':
                        pattern = extractor.get('pattern', '')
                        lines.append(f'    match = re.search(r"{pattern}", response.text)')
                        lines.append(f'    extracted_vars["{var_name}"] = match.group(1) if match else None')

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

        # 生成测试文件
        test_file_path = os.path.join(report_dir, 'test_generated.py')
        contents = []
        for i, tc in enumerate(testcases):
            content = PytestRunner._generate_test_content(tc, env_config)
            # 重命名函数避免冲突
            content = content.replace('def test_case(', f'def test_case_{i}(')
            # 替换类级别变量
            content = content.replace('extracted_vars = {}', f'extracted_vars_{i} = {{}}')
            content = content.replace('extracted_vars[', f'extracted_vars_{i}[')
            contents.append(content)

        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(contents))

        report_file = os.path.join(report_dir, 'report.html')

        start_time = time.time()
        log_lines = []

        import pytest
        exit_code = pytest.main([
            test_file_path,
            f'--html={report_file}',
            '--self-contained-html',
            '-v',
            '--tb=short',
        ], plugins=[])

        duration = round(time.time() - start_time, 2)

        # 解析结果
        total = len(testcases)
        passed = total - exit_code if exit_code < total else 0
        failed = exit_code if exit_code <= total else 0
        error = max(0, exit_code - failed) if exit_code > total else 0
        skipped = 0

        # 尝试读取日志
        log = f'Exit code: {exit_code}\nDuration: {duration}s\nReport: {report_file}'

        return total, passed, failed, error, skipped, duration, report_file, log

    @staticmethod
    def run_single_testcase(testcase, env_config=None):
        """运行单个用例"""
        return PytestRunner.run_testcases([testcase], env_config)
