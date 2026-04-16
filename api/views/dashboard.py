import json
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from ..models import Project, TestCase, TaskResult


def dashboard(request):
    # 核心统计（精简为4个）
    project_count = Project.objects.count()
    testcase_count = TestCase.objects.count()
    recent_results = TaskResult.objects.select_related(
        'task', 'task__project'
    ).order_by('-executed_at')[:5]

    # 最近7天执行趋势
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)
    daily_stats = []
    week_total = 0
    week_passed = 0
    week_failed = 0
    week_error = 0

    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_results = TaskResult.objects.filter(executed_at__date=day)
        day_total = sum(r.total_cases for r in day_results)
        day_passed = sum(r.passed for r in day_results)
        day_failed = sum(r.failed for r in day_results)
        day_error = sum(r.error for r in day_results)
        daily_stats.append({
            'date': day.strftime('%m-%d'),
            'date_full': day.strftime('%Y-%m-%d'),
            'total': day_total,
            'passed': day_passed,
            'failed': day_failed,
            'error': day_error,
            'is_today': day == today,
        })
        week_total += day_total
        week_passed += day_passed
        week_failed += day_failed
        week_error += day_error

    week_pass_rate = round(week_passed / week_total * 100, 1) if week_total > 0 else 0

    return render(request, 'dashboard.html', {
        'project_count': project_count,
        'testcase_count': testcase_count,
        'recent_results': recent_results,
        'daily_stats_json': json.dumps(daily_stats),
        'week_total': week_total,
        'week_passed': week_passed,
        'week_failed': week_failed,
        'week_error': week_error,
        'week_pass_rate': week_pass_rate,
        'nav_dashboard': 'active',
    })
