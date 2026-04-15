import json
import yaml
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from ..models import DDTSource


def ddt_list(request):
    """数据源列表"""
    source_type = request.GET.get('source_type', '')
    search = request.GET.get('search', '')
    sources = DDTSource.objects.all()
    if source_type:
        sources = sources.filter(source_type=source_type)
    if search:
        sources = sources.filter(name__icontains=search)
    return render(request, 'ddt/list.html', {
        'sources': sources,
        'current_type': source_type,
        'search': search,
        'nav_ddt': 'active',
    })


def ddt_create(request):
    """创建数据源"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        source_type = request.POST.get('source_type', 'JSON')
        file_path = request.POST.get('file_path', '').strip()
        db_query = request.POST.get('db_query', '').strip()
        content = request.POST.get('content', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, '数据源名称不能为空')
            return render(request, 'ddt/form.html', {
                'nav_ddt': 'active', 'form_data': request.POST,
            })

        # 验证 content 格式
        if content and source_type in ('JSON', 'YAML'):
            try:
                if source_type == 'JSON':
                    json.loads(content)
                else:
                    yaml.safe_load(content)
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                messages.error(request, f'数据内容格式错误: {e}')
                return render(request, 'ddt/form.html', {
                    'nav_ddt': 'active', 'form_data': request.POST,
                })

        DDTSource.objects.create(
            name=name, source_type=source_type, file_path=file_path,
            db_query=db_query, content=content, description=description,
        )
        messages.success(request, f'数据源 "{name}" 创建成功')
        return redirect('ddt_list')

    return render(request, 'ddt/form.html', {'nav_ddt': 'active'})


def ddt_update(request, pk):
    """编辑数据源"""
    source = get_object_or_404(DDTSource, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        source_type = request.POST.get('source_type', 'JSON')
        file_path = request.POST.get('file_path', '').strip()
        db_query = request.POST.get('db_query', '').strip()
        content = request.POST.get('content', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, '数据源名称不能为空')
            return render(request, 'ddt/form.html', {
                'source': source, 'nav_ddt': 'active', 'form_data': request.POST,
            })

        if content and source_type in ('JSON', 'YAML'):
            try:
                if source_type == 'JSON':
                    json.loads(content)
                else:
                    yaml.safe_load(content)
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                messages.error(request, f'数据内容格式错误: {e}')
                return render(request, 'ddt/form.html', {
                    'source': source, 'nav_ddt': 'active', 'form_data': request.POST,
                })

        source.name = name
        source.source_type = source_type
        source.file_path = file_path
        source.db_query = db_query
        source.content = content
        source.description = description
        source.save()
        messages.success(request, f'数据源 "{name}" 更新成功')
        return redirect('ddt_list')

    return render(request, 'ddt/form.html', {'source': source, 'nav_ddt': 'active'})


def ddt_delete(request, pk):
    """删除数据源"""
    source = get_object_or_404(DDTSource, pk=pk)
    if request.method == 'POST':
        name = source.name
        source.delete()
        messages.success(request, f'数据源 "{name}" 已删除')
        return redirect('ddt_list')
    return redirect('ddt_list')


def ddt_preview(request, pk):
    """预览数据源内容"""
    source = get_object_or_404(DDTSource, pk=pk)

    try:
        if source.source_type == 'JSON':
            data = json.loads(source.content) if source.content else []
        elif source.source_type == 'YAML':
            data = yaml.safe_load(source.content) if source.content else []
        elif source.source_type == 'CSV':
            reader = csv.DictReader(io.StringIO(source.content))
            data = list(reader)
        elif source.source_type == 'DB':
            data = {'note': '数据库类型数据源将在执行时动态查询', 'query': source.db_query}
        else:
            data = []
    except Exception as e:
        data = {'error': str(e)}

    if isinstance(data, list) and len(data) > 0:
        columns = list(data[0].keys()) if isinstance(data[0], dict) else []
        rows = data[:50]  # 最多预览50条
    elif isinstance(data, dict):
        columns = list(data.keys())
        rows = [data]
    else:
        columns = []
        rows = []

    return render(request, 'ddt/preview.html', {
        'source': source,
        'columns': columns,
        'rows': rows,
        'total': len(data) if isinstance(data, list) else 1,
        'nav_ddt': 'active',
    })


def ddt_list_api(request):
    """AJAX: 获取数据源列表（供用例表单选择）"""
    sources = list(DDTSource.objects.values('id', 'name', 'source_type'))
    return JsonResponse(sources, safe=False)
