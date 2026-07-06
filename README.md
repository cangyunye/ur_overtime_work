# 加班登记系统

简朴的加班登记 Web 系统，无需权限校验，方便同事登记加班信息与查看记录。

## 技术栈

| 层     | 选型                                               |
| ------ | -------------------------------------------------- |
| 后端   | Python 3 标准库 `http.server`（零依赖核心）          |
| 前端   | 原生 HTML + CSS + JavaScript（无框架）              |
| 数据库 | SQLite / MySQL / PostgreSQL （通过配置切换）         |
| 导出   | openpyxl（可选，仅导出 Excel 时需要）                |

## 目录结构

```
overtime_system/
├── server.py          # HTTP 服务 + API 路由
├── db.py              # 数据库操作层（三方言支持）
├── config.py          # 配置读取
├── start.sh           # 一键启动脚本（读取 .env）
├── .env               # 环境配置（不入库，参考 .env.example）
├── .env.example       # 配置模板
├── static/            # 前端静态文件
│   ├── index.html     # 主页面
│   ├── css/style.css  # 样式
│   └── js/app.js      # 前端逻辑
├── tests/
│   ├── test_e2e.py    # E2E 测试（38 个用例）
│   ├── test_data.sql  # 测试数据（34 条记录）
│   └── test_cases.md  # 手工测试用例文档
├── docs/
│   └── form-fields.md # 表单字段开发指南
└── logs/              # 运行时日志
```

## 快速启动

```bash
# 1. 克隆后复制环境配置
cp .env.example .env

# 2. 启动（SQLite 默认，零配置）
./start.sh

# 或直接
python3 server.py sqlite3 --port 8080
```

## 配置

编辑 `.env` 文件切换数据库类型，或通过命令行参数覆盖：

```bash
# SQLite（默认）
python3 server.py sqlite3 --db-path overtime.db --port 8080

# MySQL
python3 server.py mysql  --db-host 127.0.0.1 --db-user root --db-password pwd --db-database overtime_system

# PostgreSQL
python3 server.py pg  --db-host 127.0.0.1 --db-user postgres --db-password pwd --db-database overtime_system
```

## 测试数据

```bash
# 导入 34 条测试记录
sqlite3 overtime.db < tests/test_data.sql
```

## 运行测试

```bash
# 使用 uv 虚拟环境（推荐）
uv venv
source .venv/bin/activate
uv pip install openpyxl
python3 tests/test_e2e.py

# 或直接运行（不含 Excel 导出测试）
python3 tests/test_e2e.py
```

## API 一览

| 方法   | 路径                     | 说明             |
| ------ | ------------------------ | ---------------- |
| POST   | `/api/records`           | 创建加班记录     |
| GET    | `/api/records`           | 查询记录列表     |
| GET    | `/api/records/<id>`      | 获取单条记录     |
| PUT    | `/api/records/<id>`      | 更新记录         |
| DELETE | `/api/records/<id>`      | 删除记录         |
| GET    | `/api/records/export`    | 导出 Excel       |
| GET    | `/api/auto-fill`         | 自动关联员工信息 |

查询参数：`date_from` / `date_to` / `company` / `project_team` / `employee_id` / `employee_name` / `page` / `page_size`

## 文档

- [完整指南](docs/system-guide.md) - 用户使用、开发修改、前端设计
- [表单字段开发](docs/form-fields.md) - 添加/修改字段的 6 层修改流程
- [测试用例](tests/test_cases.md) - 手工测试用例文档
