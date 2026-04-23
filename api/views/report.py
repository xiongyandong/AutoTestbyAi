import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from ..models import TaskResult, Task, Project


def report_list(request):
    """报告列表页"""
    results = TaskResult.objects.select_related(
        'task', 'task__project', 'task__module', 'task__testcase', 'task__scene'
    ).order_by('-executed_at')

    # 筛选
    project_id = request.GET.get('project', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if project_id:
        results = results.filter(task__project_id=project_id)
    if status == 'passed':
        results = results.filter(passed__gt=0, failed=0, error=0)
    elif status == 'failed':
        results = results.filter(failed__gt=0)
    elif status == 'error':
        results = results.filter(error__gt=0)
    if date_from:
        results = results.filter(executed_at__date__gte=date_from)
    if date_to:
        results = results.filter(executed_at__date__lte=date_to)

    projects = Project.objects.all()

    # 汇总统计 (on filtered queryset BEFORE pagination)
    summary = results.aggregate(
        total_runs=Count('id'),
        total_cases=Sum('total_cases'),
        total_passed=Sum('passed'),
        total_failed=Sum('failed'),
        total_error=Sum('error'),
        total_skipped=Sum('skipped'),
        avg_duration=Avg('duration'),
    )

    paginator = Paginator(results, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'report/list.html', {
        'page_obj': page_obj,
        'projects': projects,
        'current_project': project_id,
        'current_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'summary': summary,
        'nav_report': 'active',
    })


def report_detail(request, pk):
    """报告详情页"""
    result = get_object_or_404(
        TaskResult.objects.select_related(
            'task', 'task__project', 'task__module', 'task__testcase', 'task__scene'
        ),
        pk=pk
    )
    task = result.task

    # 计算通过率
    pass_rate = 0
    if result.total_cases > 0:
        pass_rate = round(result.passed / result.total_cases * 100, 1)

    # 趋势数据：同一项目最近 10 次执行结果
    trend_data = []
    if task.project:
        trend_results = TaskResult.objects.filter(
            task__project=task.project
        ).select_related('task').order_by('-executed_at')[:10]
        # 反转为时间正序
        for tr in reversed(list(trend_results)):
            rate = round(tr.passed / tr.total_cases * 100, 1) if tr.total_cases > 0 else 0
            trend_data.append({
                'label': tr.task.task_name[:20],
                'pass_rate': rate,
                'total': tr.total_cases,
                'passed': tr.passed,
                'failed': tr.failed,
                'error': tr.error,
                'skipped': tr.skipped,
                'duration': tr.duration,
                'executed_at': tr.executed_at.strftime('%m-%d %H:%M'),
            })

    # 读取 HTML 报告内容（如果存在）
    report_html = None
    if result.report_path and os.path.isfile(result.report_path):
        try:
            with open(result.report_path, 'r', encoding='utf-8') as f:
                report_html = f.read()
        except Exception:
            report_html = None

    return render(request, 'report/detail.html', {
        'result': result,
        'task': task,
        'pass_rate': pass_rate,
        'trend_data': trend_data,
        'report_html': report_html,
        'nav_report': 'active',
    })


def report_download(request, pk):
    """下载报告文件"""
    result = get_object_or_404(TaskResult, pk=pk)

    if not result.report_path or not os.path.isfile(result.report_path):
        raise Http404('报告文件不存在')

    file_path = result.report_path
    filename = os.path.basename(file_path)

    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=filename,
    )
    response['Content-Type'] = 'text/html; charset=utf-8'
    return response
