# Pytest 测试平台

基于 Django + Bootstrap 5 的 API 接口自动化测试管理平台，支持用例管理、场景编排、数据驱动、异步执行与定时调度。

## 功能特性

- **项目管理** — 项目 / 模块 / 配置三级层次结构，支持 DEV / QA / PROD 多环境配置
- **用例管理** — 定义 HTTP 测试用例，支持请求方法、URL、Headers、参数、Body、提取器（JSONPath / 正则）、断言（status_code / JSONPath，支持 eq / contains / gt / lt / not_eq / regex）及前后置钩子
- **数据驱动（DDT）** — 支持 JSON / YAML / CSV / 数据库四种数据源，自动生成 `pytest.mark.parametrize` 参数化用例
- **场景编排** — 拖拽排序组合多个用例为有序场景，支持用例间变量传递
- **任务执行** — 支持同步执行、Celery 异步执行、Crontab 定时调度
- **测试报告** — 查看执行结果、下载 pytest-html 报告、趋势图与通过率统计
- **仪表盘** — 项目/用例概览、7 天执行趋势（Chart.js）、快速操作入口

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 4.2, Celery 5.4, Redis |
| 前端 | Bootstrap 5.3, jQuery 3.7, Chart.js 4.4 |
| 测试引擎 | pytest 8.3, pytest-html 4.1, requests, jsonpath-ng |
| 数据库 | SQLite（开发）, Redis（Celery broker / backend / cache） |
| 定时调度 | django-celery-beat (DatabaseScheduler) |

## 环境要求

- Python 3.10+
- Redis Server（127.0.0.1:6379）

## 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd openAItest

# 2. 创建并激活虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 执行数据库迁移
python manage.py migrate

# 5. 创建管理员账户（可选）
python manage.py createsuperuser

# 6. 启动 Django 开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 启动 Celery（异步任务 & 定时调度）

```bash
# 启动 Celery Worker
celery -A pytest_platform worker -l info

# 启动 Celery Beat（定时任务调度）
celery -A pytest_platform beat -l info
```

### 访问地址

- 主应用：http://127.0.0.1:8000/
- Django Admin：http://127.0.0.1:8000/admin/

## 项目结构

```
openAItest/
├── api/                        # 主应用（业务逻辑）
│   ├── models.py               # 8 个数据模型
│   ├── views/                  # 视图模块（按功能拆分）
│   ├── tasks.py                # Celery 异步任务
│   ├── pytest_runner.py        # 测试执行引擎
│   ├── urls.py                 # URL 路由
│   └── templatetags/           # 自定义模板标签
├── pytest_platform/            # Django 项目配置
│   ├── settings.py             # 全局配置
│   ├── celery.py               # Celery 配置
│   └── urls.py                 # 根路由
├── templates/                  # 21 个 HTML 模板
├── static/                     # CSS / JS / 图标
├── docs/                       # 设计文档与实施计划
├── manage.py
└── requirements.txt
```

## 数据模型

```
Project (1) ────< Module (N) ────< Config (N)
                    │
                    └────< TestCase (N) ────> DDTSource (N:1)

Project (1) ────< Scene (N) ────< SceneCase (N) ────> TestCase

Task ────> Project / Module / TestCase / Scene
Task (1) ────< TaskResult (N)
```

## 依赖列表

| 包 | 版本 | 用途 |
|---|------|------|
| Django | 4.2.30 | Web 框架 |
| celery | 5.4.0 | 异步任务执行 |
| django-celery-beat | 2.7.0 | Crontab 定时调度 |
| redis | 5.2.1 | Celery broker / 结果后端 / 缓存 |
| requests | 2.32.3 | HTTP 请求客户端 |
| pyyaml | 6.0.2 | YAML 数据源解析 |
| pytest | 8.3.4 | 测试执行引擎 |
| pytest-html | 4.1.1 | HTML 测试报告 |
| jsonpath-ng | 1.7.0 | JSONPath 提取与断言 |

## Redis 配置

项目使用 Redis 的 3 个数据库：

| 数据库 | 用途 |
|--------|------|
| `/0` | Celery Broker |
| `/1` | Celery Result Backend |
| `/2` | Django Cache Backend |
