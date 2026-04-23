import ast
import re

from .models import Project, ScriptAsset


VAR_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')
FUNCTION_SIGNATURE_PATTERN = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$')
_SCRIPT_NAMESPACE_CACHE = {}


def extract_function_index(content):
    tree = ast.parse(content or '')
    signatures = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            arg_names = ', '.join(arg.arg for arg in node.args.args)
            signatures.append(f'{node.name}({arg_names})')
    return signatures


def validate_python_script(content):
    try:
        functions = extract_function_index(content)
        return {'ok': True, 'functions': functions}
    except SyntaxError as exc:
        return {
            'ok': False,
            'line': exc.lineno or 0,
            'column': exc.offset or 0,
            'message': exc.msg,
        }


def _script_cache_key(script):
    updated_at = getattr(script, 'updated_at', None)
    updated_marker = updated_at.isoformat() if updated_at else ''
    return (script.pk, updated_marker)


def _load_script_namespace(script):
    cache_key = _script_cache_key(script)
    namespace = _SCRIPT_NAMESPACE_CACHE.get(cache_key)
    if namespace is not None:
        return namespace

    namespace = {}
    exec(script.content or '', namespace, namespace)
    _SCRIPT_NAMESPACE_CACHE[cache_key] = namespace
    return namespace


def replace_context_vars(value, context):
    if not isinstance(value, str):
        return value

    def _replace(match):
        key = match.group(1)
        return str(context.get(key, ''))

    return VAR_PATTERN.sub(_replace, value)


def _split_args(raw_args):
    if not raw_args:
        return []
    args = []
    current = []
    quote = None
    depth = 0
    for char in raw_args:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
            current.append(char)
            continue
        if char == '(':
            depth += 1
            current.append(char)
            continue
        if char == ')':
            depth -= 1
            current.append(char)
            continue
        if char == ',' and depth == 0:
            args.append(''.join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        args.append(''.join(current).strip())
    return args


def parse_function_call(expression):
    inner = expression.strip()[2:-2].strip()
    if '(' not in inner or not inner.endswith(')'):
        raise ValueError(f'非法函数表达式: {expression}')
    function_name = inner.split('(', 1)[0].strip()
    raw_args = inner[len(function_name) + 1:-1].strip()
    return function_name, _split_args(raw_args)


def resolve_argument(raw_arg, context):
    rendered = replace_context_vars(raw_arg, context)
    if rendered == 'true':
        return True
    if rendered == 'false':
        return False
    try:
        return ast.literal_eval(rendered)
    except (ValueError, SyntaxError):
        return rendered


def load_script_functions(project=None):
    if project is not None and not hasattr(project, 'pk'):
        project = Project.objects.filter(pk=project).first()

    functions = {}
    public_script = ScriptAsset.objects.filter(scope_type=ScriptAsset.SCOPE_PUBLIC).first()
    if public_script and public_script.content.strip():
        namespace = _load_script_namespace(public_script)
        functions.update({key: value for key, value in namespace.items() if callable(value)})

    if project is not None:
        project_script = ScriptAsset.objects.filter(
            scope_type=ScriptAsset.SCOPE_PROJECT, project=project
        ).first()
        if project_script and project_script.content.strip():
            namespace = _load_script_namespace(project_script)
            functions.update({key: value for key, value in namespace.items() if callable(value)})

    return functions


def normalize_hook_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, dict):
        normalized = []
        for item in value.values():
            if isinstance(item, str) and item.strip():
                normalized.append(item)
        return normalized
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith('{{') and stripped.endswith('}}'):
            return [stripped]
        try:
            parsed = ast.literal_eval(stripped)
        except (ValueError, SyntaxError):
            return []
        return normalize_hook_list(parsed)
    return []


def parse_function_signature(signature):
    match = FUNCTION_SIGNATURE_PATTERN.match((signature or '').strip())
    if not match:
        return None
    return {
        'name': match.group(1),
        'signature': signature.strip(),
        'args': match.group(2).strip(),
    }


def execute_script_hooks(hooks, project=None, context=None):
    context = context or {}
    normalized_hooks = normalize_hook_list(hooks)
    executed = []
    for expression in normalized_hooks:
        try:
            result = render_runtime_value(expression, project, context)
        except Exception as exc:
            raise RuntimeError(f'{expression}: {exc}') from exc
        executed.append({
            'expression': expression,
            'result': result,
        })
    return executed


def render_runtime_value(value, project=None, context=None):
    context = context or {}
    if not isinstance(value, str):
        return value

    if value.startswith('{{') and value.endswith('}}'):
        function_name, args = parse_function_call(value)
        callable_map = load_script_functions(project)
        target = callable_map.get(function_name)
        if target is None:
            raise ValueError(f'函数不存在: {function_name}')
        resolved_args = [resolve_argument(arg, context) for arg in args]
        return target(*resolved_args)

    replaced = replace_context_vars(value, context)
    if isinstance(replaced, str) and replaced.startswith('{{') and replaced.endswith('}}'):
        return render_runtime_value(replaced, project, context)
    return replaced


def render_nested_value(value, project=None, context=None):
    if isinstance(value, dict):
        return {key: render_nested_value(item, project, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render_nested_value(item, project, context) for item in value]
    current = value
    for _ in range(3):
        rendered = render_runtime_value(current, project, context)
        if rendered == current:
            return rendered
        current = rendered
    return current
