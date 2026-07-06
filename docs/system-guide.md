# 加班登记系统 - 完整指南

本文档涵盖用户使用、开发修改和前端设计三个方面，方便查阅和支持后续开发。

---

## 一、用户指南

### 1.1 系统简介

加班登记系统是一个轻量级 Web 应用，用于同事间登记加班信息和查看记录。无需权限校验，打开即用。

**核心功能：**
- 登记加班信息（姓名、工号、公司、项目组、PM、事由、日期、时间）
- 查询和筛选加班记录
- 编辑和删除已有记录
- 导出 Excel 报表
- 支持 SQLite / MySQL / PostgreSQL 三种数据库

### 1.2 快速启动

```bash
# 1. 复制环境配置
cp .env.example .env

# 2. 启动服务（默认 SQLite，零配置）
./start.sh

# 或直接运行
python3 server.py sqlite3 --port 8080
```

启动后访问 `http://localhost:8080` 即可使用。

### 1.3 功能说明

#### 登记表单

填写以下必填字段后点击「提交登记」：

| 字段 | 说明 | 格式要求 |
|------|------|----------|
| 加班人员 | 姓名（可重复） | 文本 |
| 工号 | 唯一标识 | 文本 |
| 合作公司 | 公司名称 | 文本 |
| 项目组 | 项目组名称 | 文本 |
| PM | 项目经理姓名 | 文本 |
| 计划加班日期 | 加班日期 | yyyy-mm-dd |
| 计划开始时间 | 开始时间 | yyyy-mm-dd HH:MM:SS |
| 计划结束时间 | 结束时间 | 必须晚于开始时间 |
| 加班事由 | 加班原因 | 文本（多行） |

**智能填充：**
- 输入姓名或工号后，系统自动关联最近一次登记信息（公司、项目组、PM）
- 如果同名记录多条，会提示输入工号精确匹配

**时段预设：**
- 早班段：8:00~17:30
- 晚班段：9:00~19:00
- 点击按钮自动填充开始/结束时间

#### 记录列表

- 默认显示本周一至本周日的记录
- 支持按日期范围、公司、项目组、工号、姓名筛选
- 每页可显示 15 / 30 / 50 / 100 条记录
- 点击「编辑」修改记录，点击「删除」移除记录

#### 导出 Excel

- 点击「导出 Excel」按钮
- 导出当前筛选条件下的所有记录
- 需要安装 openpyxl（见安装说明）

### 1.4 安装依赖

系统核心零依赖，仅导出 Excel 需要 openpyxl：

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate
uv pip install openpyxl

# 或使用 pip
python3 -m venv .venv
source .venv/bin/activate
pip install openpyxl
```

### 1.5 数据库配置

编辑 `.env` 文件切换数据库：

```bash
# SQLite（默认，零配置）
DB_TYPE=sqlite
SQLITE_DB_PATH=overtime.db

# MySQL
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=overtime_system

# PostgreSQL
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DATABASE=overtime_system
```

或通过命令行参数覆盖：

```bash
# MySQL
python3 server.py mysql --db-host 127.0.0.1 --db-user root --db-password pwd --db-database overtime_system

# PostgreSQL
python3 server.py pg --db-host 127.0.0.1 --db-user postgres --db-password pwd --db-database overtime_system
```

---

## 二、开发指南

### 2.1 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 后端 | Python 3 标准库 `http.server` | 零依赖核心 |
| 前端 | 原生 HTML + CSS + JavaScript | 无框架 |
| 数据库 | SQLite / MySQL / PostgreSQL | 通过配置切换 |
| 导出 | openpyxl | 仅导出 Excel 时需要 |

### 2.2 目录结构

```
overtime_system/
├── server.py              # HTTP 服务 + API 路由
├── db.py                  # 数据库操作层（三方言支持）
├── config.py              # 配置读取
├── start.sh               # 一键启动脚本
├── .env                   # 环境配置（不入库）
├── .env.example           # 配置模板
├── static/                # 前端静态文件
│   ├── index.html         # 主页面
│   ├── css/style.css      # 样式
│   └── js/app.js          # 前端逻辑
├── tests/
│   ├── test_e2e.py        # E2E 测试（38 个用例）
│   ├── test_data.sql      # 测试数据（34 条记录）
│   └── test_cases.md      # 手工测试用例文档
├── docs/
│   ├── form-fields.md     # 表单字段开发指南
│   └── system-guide.md    # 本文档
└── logs/                  # 运行时日志
```

### 2.3 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/records` | 创建加班记录 |
| GET | `/api/records` | 查询记录列表（支持分页和筛选） |
| GET | `/api/records/<id>` | 获取单条记录 |
| PUT | `/api/records/<id>` | 更新记录 |
| DELETE | `/api/records/<id>` | 删除记录 |
| GET | `/api/records/export` | 导出 Excel |
| GET | `/api/auto-fill` | 自动关联员工信息 |

**查询参数：**
- `date_from` / `date_to` - 日期范围
- `company` / `project_team` - 公司/项目组
- `employee_id` / `employee_name` - 工号/姓名
- `page` / `page_size` - 分页

### 2.4 添加新字段

详见 [form-fields.md](form-fields.md)，核心是 **6 层修改**：

1. **数据库 schema** - `db.py` 的 `init_db()` 三套 SQL 加列
2. **数据库 CRUD** - `db.py` 的 `insert_record()` / `update_record()` 加字段
3. **后端校验** - `server.py` 的 `required_fields` 列表加字段
4. **前端 HTML** - `index.html` 的表单、编辑弹窗、表格头各加一处
5. **前端 JS** - `app.js` 的提交数据、编辑赋值、表格渲染各加一处
6. **导出 Excel** - `server.py` 的 `_handle_export()` 表头和数据行加字段

### 2.5 测试

```bash
# 运行 E2E 测试
source .venv/bin/activate
python3 tests/test_e2e.py

# 导入测试数据
sqlite3 overtime.db < tests/test_data.sql
```

**测试覆盖：**
- 创建/读取/更新/删除记录
- 分页和筛选
- 自动关联（auto-fill）
- 日期/时间格式校验
- Excel 导出
- 共 38 个用例

### 2.6 常见问题

**Q: 如何切换数据库？**  
A: 编辑 `.env` 文件的 `DB_TYPE`，或通过命令行参数覆盖。

**Q: 导出 Excel 报错？**  
A: 需要安装 openpyxl，见 1.4 节安装说明。

**Q: 如何添加新的筛选条件？**  
A: 在 `server.py` 的 `_handle_list_records()` 加参数解析，在 `db.py` 的 `query_records()` 加 WHERE 条件，在前端 `index.html` 加筛选输入框。

**Q: 如何修改默认分页大小？**  
A: 编辑 `index.html` 的 `<select id="pagination_page_size">`，修改 `selected` 属性。

---

## 三、前端设计指南

### 3.1 设计语言

**风格：** 工业温暖风（Industrial Warmth）

- 暖色调为主，琥珀色点缀
- 简洁实用，无框架依赖
- 注重细节打磨和微交互

### 3.2 色彩系统

```css
:root {
  /* 背景 */
  --bg: #f5f2ed;           /* 暖象牙白 */
  --bg2: #ffffff;          /* 纯白卡片 */
  
  /* 文字 */
  --ink: #1c1917;          /* 暖近黑 */
  --muted: #78716c;        /* 暖灰 */
  
  /* 边框 */
  --rule: #e7e5e4;         /* 暖边框 */
  
  /* 主题色 - 琥珀 */
  --accent: #d97706;       /* 主色 */
  --accent-hover: #b45309; /* 悬停 */
  --accent-light: #fef3c7; /* 浅色 */
  
  /* 功能色 */
  --danger: #dc2626;       /* 红色 - 错误/删除 */
  --success: #059669;      /* 翡翠绿 - 成功 */
  --warning: #d97706;      /* 琥珀 - 警告 */
}
```

**时段预设按钮配色：**
- 早班段（日光黄）：`#fef9c3` → hover `#fef08a` → active `#fde047`
- 晚班段（月白色）：`#f0f9ff` → hover `#e0f2fe` → active `#bae6fd`

### 3.3 字体排版

```css
font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", 
             ui-sans-serif, system-ui, sans-serif;
```

**字号规范：**
- 导航标题：1.15rem / 700
- 卡片标题：1rem / 700
- 表单标签：0.85rem / 600
- 输入框：0.9rem / 400
- 表格内容：0.875rem / 400
- 表格表头：0.8rem / 600（大写 + 字间距）
- 按钮：0.9rem / 600（小按钮 0.8rem）
- 提示文字：0.75rem / 400

### 3.4 组件样式

#### 卡片

```css
.card {
  background: var(--bg2);
  border: 1px solid var(--rule);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(28,25,23,0.08);
  margin-bottom: 1.5rem;
  animation: cardFadeIn 0.5s ease both; /* 入场动画 */
}

.card:hover {
  box-shadow: 0 4px 12px rgba(28,25,23,0.08); /* 悬停提升 */
}
```

#### 按钮

```css
.btn {
  padding: 0.55rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn:active {
  transform: scale(0.97); /* 点击反馈 */
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: var(--accent-hover);
}
```

#### 输入框

```css
input, select, textarea {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--rule);
  border-radius: 6px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(217,119,6,0.15); /* 琥珀辉光 */
}
```

#### 表格

```css
th {
  background: #f5f2ed;
  font-weight: 600;
  letter-spacing: 0.03em;
  border-bottom: 2px solid var(--accent); /* 琥珀底边 */
}

tbody tr:hover {
  background: var(--accent-light); /* 琥珀浅底 */
}
```

### 3.5 动效设计

#### 卡片入场

```css
@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card:nth-child(2) {
  animation-delay: 0.1s; /* 错开 0.1s */
}
```

#### 按钮点击

```css
.btn:active {
  transform: scale(0.97);
}
```

#### Toast 提示

```css
.toast {
  transform: translateY(-10px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast.show {
  transform: translateY(0);
}
```

### 3.6 背景纹理

```css
body::after {
  content: "";
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* SVG 噪点 */
  opacity: 0.018;
  pointer-events: none;
  z-index: 9999;
}
```

### 3.7 自定义滚动条

```css
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-thumb {
  background: #d6d3d1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a29e;
}
```

### 3.8 响应式断点

```css
/* 平板 */
@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr; /* 单列 */
  }
  
  .filter-bar {
    flex-direction: column;
  }
}

/* 手机 */
@media (max-width: 480px) {
  .btn-group {
    width: 100%;
  }
  
  .btn-group .btn {
    flex: 1;
  }
}
```

### 3.9 修改指南

#### 修改主题色

编辑 `static/css/style.css` 的 `:root` 变量：

```css
:root {
  --accent: #d97706;       /* 改为你想要的颜色 */
  --accent-hover: #b45309; /* 悬停色（通常更深） */
  --accent-light: #fef3c7; /* 浅色（用于背景高亮） */
}
```

#### 修改时段预设按钮颜色

编辑 `static/css/style.css` 的 `.preset-btn[data-preset="..."]`：

```css
.preset-btn[data-preset="day"] {
  background: #fef9c3;     /* 改为你想要的颜色 */
  border-color: #fde047;
}

.preset-btn[data-preset="day"].active {
  background: #fde047;     /* active 状态更深 */
}
```

#### 添加新的时段预设

1. 编辑 `static/js/app.js` 的 `TIME_PRESETS`：

```javascript
var TIME_PRESETS = {
  day:   { start: "08:00:00", end: "17:30:00", label: "早班段" },
  night: { start: "09:00:00", end: "19:00:00", label: "晚班段" },
  extra: { start: "18:00:00", end: "22:00:00", label: "加班段" }, // 新增
};
```

2. 编辑 `static/index.html` 的两处 `.preset-group`：

```html
<button type="button" class="btn preset-btn" data-preset="extra" 
        onclick="setTimePreset('extra', this)">加班段 18:00~22:00</button>
```

3. 为新按钮添加配色（可选）：

```css
.preset-btn[data-preset="extra"] {
  background: #fce7f3;
  border-color: #f9a8d4;
}
```

#### 修改表单布局

编辑 `static/index.html` 的 `.form-grid`：

```html
<div class="form-group">
  <label>字段名 <span class="required">*</span></label>
  <input type="text" id="field_id" required>
  <span class="error-text" id="err_field_id"></span>
</div>
```

**注意：** 添加新字段需要同步修改 6 层代码，详见 [form-fields.md](form-fields.md)。

---

## 四、附录

### 4.1 数据库表结构

```sql
CREATE TABLE overtime_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    company TEXT NOT NULL,
    project_team TEXT NOT NULL,
    pm TEXT NOT NULL,
    reason TEXT NOT NULL,
    overtime_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(employee_id, overtime_date)
);
```

### 4.2 配置项一览

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DB_TYPE | sqlite | 数据库类型 (sqlite/mysql/postgresql) |
| SQLITE_DB_PATH | overtime.db | SQLite 文件路径 |
| MYSQL_HOST | localhost | MySQL 主机 |
| MYSQL_PORT | 3306 | MySQL 端口 |
| MYSQL_USER | root | MySQL 用户名 |
| MYSQL_PASSWORD | (空) | MySQL 密码 |
| MYSQL_DATABASE | overtime_system | MySQL 数据库名 |
| PG_HOST | localhost | PostgreSQL 主机 |
| PG_PORT | 5432 | PostgreSQL 端口 |
| PG_USER | postgres | PostgreSQL 用户名 |
| PG_PASSWORD | (空) | PostgreSQL 密码 |
| PG_DATABASE | overtime_system | PostgreSQL 数据库名 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8080 | 监听端口 |

### 4.3 相关文件索引

- [README.md](../README.md) - 项目概览和快速启动
- [form-fields.md](form-fields.md) - 表单字段开发指南（6 层修改）
- [test_cases.md](../tests/test_cases.md) - 手工测试用例
- [test_data.sql](../tests/test_data.sql) - 测试数据（34 条记录）

---

**文档版本：** 2024-01  
**最后更新：** 2024-01
