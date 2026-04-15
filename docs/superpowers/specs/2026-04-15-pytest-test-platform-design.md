# Pytest 测试平台设计文档

> 创建日期：2026-04-15  
> 状态：待审核  
> 作者：Qwen Code

## 概述

本项目参考 HttpRunnerManager 的功能设计和页面风格，基于 Django + pytest 构建的接口自动化测试平台。使用 pytest 作为测试引擎，支持 DDT 参数化，采用 Docker Compose 部署。

## 核心目标

1. 提供完整的接口自动化测试管理能力
2. 使用 pytest 作为核心测试引擎（替代 HttpRunner）
3. 支持 DDT 数据驱动测试（JSON/YAML/CSV/数据库）
4. 支持异步任务执行和定时调度
5. 提供美观的 Web 管理界面
6. 支持 Docker Compose 一键部署

## 技术栈

| 层级 | 技术 | 版本 |
|-----|------|------|
| Web 框架 | Django | 4.x |
| 数据库 | SQLite / MySQL | 8.0 |
| 测试引擎 | pytest | 7.x |
| DDT 插件 | pytest-ddt | latest |
| 报告插件 | pytest-html | latest |
| 异步任务 | Celery | 5.x |
| 消息中间件 | Redis | 7.x |
| 定时任务 | django-celery-beat | latest |
| 前端 | Bootstrap + jQuery | 5.x / 3.x |
| 部署 | Docker Compose | latest |
| Web 服务器 | Nginx | alpine |

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 层 (Django)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │项目管理  │  │用例管理  │  │场景编排  │  │报告查看 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │配置管理  │  │模块管理  │  │定时任务  │  │环境管理 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │用例解析引擎  │  │场景编排引擎  │  │DDT参数化引擎  │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │环境变量注入  │  │Hook处理器    │  │断言验证引擎   │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  测试执行层 (pytest)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │pytest 核心   │  │pytest-ddt    │  │pytest-html    │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │自定义fixtures│  │插件扩展      │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                异步任务层 (Celery)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │异步执行  │  │定时任务  │  │任务监控  │  │邮件通知 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   数据层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │SQLite/   │  │Redis/    │  │测试报告  │  │日志文件 │ │
│  │MySQL     │  │RabbitMQ  │  │          │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 功能模块设计

### 1. 项目管理

**功能：**
- 项目 CRUD（创建、查看、编辑、删除）
- 项目列表展示（支持搜索、筛选）
- 批量导入导出用例（JSON/YAML）
- 项目级环境变量配置

**页面：**
- 项目列表页（表格展示、搜索框、新增按钮）
- 项目新增/编辑页（表单）
- 批量导入页（文件上传、格式选择）

### 2. 模块管理

**功能：**
- 模块归属项目
- 模块 CRUD
- 模块下管理用例和配置
- 支持用例跨模块引用

**页面：**
- 模块列表页（按项目筛选）
- 模块新增/编辑页

### 3. 配置管理（Config）

**功能：**
- 全局变量定义
- 公共请求参数/Header
- 全局 setup/teardown hooks
- 多环境配置（DEV/QA/PROD 等）
- 环境快速切换

**数据模型：**
```python
Config
├── id
├── module_id (FK -> Module)
├── name
├── variables (JSONField)
├── parameters (JSONField)
├── request_hooks (JSONField)
├── response_hooks (JSONField)
├── env_type (CharField: DEV/QA/PROD)
├── created_by
├── created_at
└── updated_at
```

**页面：**
- 配置列表页（按模块筛选）
- 配置新增/编辑页（Tab 切换：基本信息、变量、Hooks）

### 4. 用例管理（Test）

**功能：**
- 用例归属模块
- 请求定义（method、url、headers、params、body）
- 提取器（extractors）：支持 JSONPath、正则等
- 断言（assertions）：等于、包含、大于等
- 用例级 hooks（before/after）
- 用例参数化：通过 DDT 标记，引用数据源文件
- 单个用例运行

**数据模型：**
```python
TestCase
├── id
├── module_id (FK -> Module)
├── name
├── method (CharField: GET/POST/PUT/DELETE/PATCH)
├── url
├── headers (JSONField)
├── params (JSONField)
├── body (JSONField)
├── extractors (JSONField)
├── assertions (JSONField)
├── setup_hooks (JSONField)
├── teardown_hooks (JSONField)
├── ddt_source_id (FK -> DDTSource, nullable)
├── is_parameterized (BooleanField)
├── created_by
├── created_at
└── updated_at
```

**页面：**
- 用例列表页（表格、搜索、筛选、批量操作）
- 用例新增/编辑页（Tab 切换：基本信息、请求配置、提取器、断言、Hooks、DDT 参数化）
- JSON 编辑器
- 实时预览

### 5. DDT 参数化引擎

**功能：**
- 支持数据源：JSON、YAML、CSV、数据库查询
- pytest.mark.parametrize 自动生成
- 数据源与用例关联管理
- 参数化用例组合执行
- 数据源预览

**数据模型：**
```python
DDTSource
├── id
├── name
├── source_type (CharField: JSON/YAML/CSV/DB)
├── file_path (CharField, nullable)
├── db_query (TextField, nullable)
├── description
├── created_at
└── updated_at
```

**数据源示例：**
```json
// login_test_data.json
[
  {"username": "admin", "password": "123456", "expected_token": "admin_token"},
  {"username": "user1", "password": "pass1", "expected_token": "user1_token"}
]
```

**pytest 执行时自动展开：**
```
test_login[case0] - username=admin
test_login[case1] - username=user1
```

### 6. 场景编排

**功能：**
- 跨项目/跨模块引用用例
- 拖拽式排序依赖
- 支持用例间数据传递（通过 extractors）
- 可视化展示执行链路
- 场景整体运行

**数据模型：**
```python
Scene
├── id
├── name
├── project_id (FK -> Project)
├── description
├── created_at
└── updated_at

SceneCase
├── id
├── scene_id (FK -> Scene)
├── testcase_id (FK -> TestCase)
└── order_index
```

**页面：**
- 场景列表页
- 场景编排页（拖拽排序、可视化链路、依赖关系）

### 7. 执行与调度

**功能：**
- 单用例/模块/项目运行
- 批量运行
- 同步/异步执行（Celery）
- Crontab 定时任务
- 执行环境选择
- 自定义报告名
- 完成后邮件通知

**数据模型：**
```python
Task
├── id
├── task_name
├── task_type (CharField: SYNC/ASYNC/SCHEDULE)
├── cron_expression
├── status
├── execute_env
├── email_notify (BooleanField)
├── created_at
└── updated_at

TaskResult
├── id
├── task_id (FK -> Task)
├── total_cases
├── passed
├── failed
├── error
├── duration
├── report_path
└── executed_at
```

**页面：**
- 任务列表页
- 任务创建页（选择执行范围、环境、调度方式）
- 定时任务配置页（Crontab 表达式）

### 8. 报告系统

**功能：**
- pytest 执行结果解析
- 在线报告展示
- 报告下载（HTML/PDF）
- 报告统计（通过率、趋势）
- 报告详情（用例级别详情、日志）

**页面：**
- 报告列表页（表格、筛选）
- 报告详情页（统计图表、用例详情、日志）

### 9. 首页 Dashboard

**功能：**
- 项目总数、用例总数、配置总数
- 今日执行统计
- 最近测试报告
- 快捷操作入口

**页面：**
- Dashboard 首页（数据卡片、图表、快捷入口）

## 数据库设计

完整的数据模型关系：

```
Project (1) ────< (N) Module (1) ────< (N) TestCase
                                             │
                                             ├────> DDTSource (N:1)
                                             │
Project (1) ────< (N) Scene (1) ────< (N) SceneCase ────> TestCase

Module (1) ────< (N) Config

Task (1) ────< (N) TaskResult
```

## DDT 参数化实现设计

### 数据加载器

```python
# tests/ddt_loader.py
import json
import yaml
import csv

class DDTLoader:
    @staticmethod
    def load_json(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def load_yaml(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def load_csv(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    @staticmethod
    def load_from_db(query):
        # 使用 Django ORM 执行查询
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

### pytest 集成

```python
# tests/conftest.py
import pytest
from tests.ddt_loader import DDTLoader

@pytest.fixture(scope="session")
def ddt_data(request):
    """加载 DDT 数据"""
    source_type = request.param.get('source_type')
    source_path = request.param.get('source_path')
    
    if source_type == 'json':
        return DDTLoader.load_json(source_path)
    elif source_type == 'yaml':
        return DDTLoader.load_yaml(source_path)
    elif source_type == 'csv':
        return DDTLoader.load_csv(source_path)
    elif source_type == 'db':
        return DDTLoader.load_from_db(source_path)
    return []
```

### 用例执行器

```python
# tests/pytest_runner.py
import pytest
import os
import tempfile

class PytestRunner:
    @staticmethod
    def run_test(testcase, ddt_data=None):
        """运行单个用例"""
        # 动态生成测试文件
        test_content = generate_test_content(testcase, ddt_data)
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        # 执行 pytest
        result_file = test_file.replace('.py', '_result.html')
        exit_code = pytest.main([
            test_file,
            f'--html={result_file}',
            '--self-contained-html',
            '-v'
        ])
        
        # 解析结果
        return parse_result(result_file)
    
    @staticmethod
    def run_batch(testcases, ddt_sources=None):
        """批量运行用例"""
        # 类似逻辑，生成多个测试文件
        pass
```

## Celery 异步任务设计

### 任务定义

```python
# api/tasks.py
from celery import shared_task
from tests.pytest_runner import PytestRunner

@shared_task
def execute_test_task(task_id, test_ids, env):
    """异步执行测试"""
    # 加载测试用例
    # 加载环境配置
    # 执行测试
    # 保存结果
    pass

@shared_task
def send_report_email(task_result_id):
    """发送报告邮件"""
    pass
```

### Celery 配置

```python
# settings.py
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
```

## Docker Compose 部署

### 服务组成

- **web**: Django Web 应用
- **celery_worker**: Celery 工作进程
- **celery_beat**: Celery 定时任务调度器
- **db**: MySQL 数据库
- **redis**: Redis 消息中间件
- **nginx**: 反向代理

### 数据卷

- `mysql_data`: MySQL 数据持久化
- `static_data`: 静态文件
- `media_data`: 媒体文件
- `reports_data`: 测试报告

详见 `docker-compose.yml` 配置。

## 前端页面设计

### 整体风格

- 经典后台管理系统风格
- 左侧固定功能菜单
- 顶部快捷操作与数据统计
- 基于 Bootstrap 5 + jQuery
- 参考 HttpRunnerManager 的布局与交互

### 菜单结构

```
首页概览 (Dashboard)
├── 项目管理
│   ├── 项目列表
│   └── 批量导入
├── 模块管理
├── 配置管理
├── 用例管理
├── 场景编排
├── 定时任务
└── 测试报告
```

### 关键页面交互

**用例列表页：**
- 表格展示（用例名、所属模块、是否参数化、更新时间）
- 搜索/筛选功能
- 操作按钮（编辑、删除、运行、查看报告）

**用例编辑页：**
- Tab 切换：基本信息、请求配置、提取器、断言、Hooks、DDT 参数化
- 动态添加/删除字段
- JSON 编辑器
- 实时预览

**场景编排页：**
- 拖拽式排序
- 可视化用例链路
- 依赖关系展示

**报告页：**
- 报告列表
- 在线报告查看
- 统计图表（通过率、趋势）

## 错误处理设计

### 全局错误处理

```python
# api/exceptions.py
class TestCaseError(Exception):
    """用例执行错误"""
    pass

class DDTLoadError(Exception):
    """DDT 数据加载错误"""
    pass

class ConfigNotFoundError(Exception):
    """配置未找到错误"""
    pass
```

### Django 错误中间件

```python
# api/middleware.py
class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            # 记录日志
            # 返回统一错误格式
            pass
        return response
```

## 测试策略

### 单元测试

- 模型测试（models）
- 视图测试（views）
- 工具函数测试

### 集成测试

- API 接口测试
- Celery 任务测试
- DDT 参数化集成测试

### 端到端测试

- 使用 pytest + requests 模拟完整流程

## 安全设计

- Django CSRF 保护
- SQL 注入防护（ORM）
- XSS 防护（模板转义）
- 敏感信息加密存储
- 访问日志记录

## 性能优化

- 数据库查询优化（select_related、prefetch_related）
- 静态文件缓存
- Celery 异步处理耗时任务
- 分页查询
- 接口缓存（Redis）

## 开发规范

### 代码风格

- 遵循 PEP 8
- 使用 black 格式化
- 使用 flake8 检查

### Git 规范

- 分支管理（main/dev/feature）
- Commit message 规范
- PR 审核

## 未来扩展

- 支持分布式执行（pytest-xdist）
- 支持前后端分离架构
- 支持更多协议（gRPC、WebSocket）
- AI 智能断言
- 性能测试支持
