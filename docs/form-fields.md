# 表单字段开发指南

## 字段清单

| 字段名           | 标签           | 类型     | 约束              | 备注                       |
| ---------------- | -------------- | -------- | ----------------- | -------------------------- |
| employee_name    | 加班人员       | TEXT     | NOT NULL          | 可重复，用于模糊搜索       |
| employee_id      | 工号           | TEXT     | NOT NULL / UNIQUE | 唯一标识，联合唯一键       |
| company          | 合作公司       | TEXT     | NOT NULL          | 可模糊搜索                 |
| project_team     | 项目组         | TEXT     | NOT NULL          | 可模糊搜索                 |
| pm               | PM             | TEXT     | NOT NULL          | —                          |
| reason           | 加班事由       | TEXT     | NOT NULL          | textarea，多行             |
| overtime_date    | 计划加班日期   | DATE     | NOT NULL          | 格式 yyyy-mm-dd            |
| start_time       | 计划开始时间   | DATETIME | NOT NULL          | 格式 yyyy-mm-dd HH:MM:SS   |
| end_time         | 计划结束时间   | DATETIME | NOT NULL          | 必须晚于 start_time        |

自动字段：`id`（自增主键）、`created_at`、`updated_at`

## 添加新字段（6 层修改）

以新增字段 `overtime_type`（加班类型：工作日/周末/节假日）为例：

### 第 1 层：数据库 schema

**文件**: `db.py` — `init_db()`

在三套 SQL 的 `CREATE TABLE` 中各加一列：

```python
# SQLite
overtime_type TEXT NOT NULL DEFAULT '工作日',

# MySQL
overtime_type VARCHAR(20) NOT NULL DEFAULT '工作日',

# PostgreSQL  （同 SQLite 写法）
overtime_type TEXT NOT NULL DEFAULT '工作日',
```

### 第 2 层：数据库 CRUD

**文件**: `db.py`

`insert_record()` — `INSERT` 语句加列名和参数：

```python
sql = f"""
    INSERT INTO overtime_records
        (employee_name, employee_id, ..., overtime_type, created_at, updated_at)
    VALUES ({ph}, {ph}, ..., {ph}, {ph}, {ph})
"""
params = (
    data["employee_name"], ..., data["overtime_type"],
    now, now,
)
```

`update_record()` — `UPDATE` 语句同理：

```python
sql = f"""
    UPDATE overtime_records SET
        ..., overtime_type={ph}, updated_at={ph}
    WHERE id={ph}
"""
```

### 第 3 层：后端校验

**文件**: `server.py`

`_handle_create_record()` 和 `_handle_update_record()` 的 `required_fields` 列表加字段名。如需自定义校验，在"时间格式校验"附近追加：

```python
valid_types = ["工作日", "周末", "节假日"]
if data.get("overtime_type") not in valid_types:
    self._send_json({"error": "加班类型无效"}, 400)
    return
```

### 第 4 层：前端 HTML

**文件**: `static/index.html`

三处需修改：

**登记表单** — 在 `project_team` 和 `pm` 之间插入：

```html
<div class="form-group">
  <label>加班类型 <span class="required">*</span></label>
  <select id="overtime_type" name="overtime_type" required>
    <option value="工作日">工作日</option>
    <option value="周末">周末</option>
    <option value="节假日">节假日</option>
  </select>
  <span class="error-text" id="err_overtime_type"></span>
</div>
```

**编辑弹窗** — 在 `editForm` 中插入对应字段：

```html
<div class="form-group">
  <label>加班类型 <span class="required">*</span></label>
  <select id="edit_overtime_type" required>...</select>
</div>
```

**表格头** — `<thead>` 加一列 `<th>加班类型</th>`，`<tbody>` 的 `colspan` 加 1。

### 第 5 层：前端 JS

**文件**: `static/js/app.js`

**表单提交** — `data` 对象加字段：

```javascript
var data = {
  ...
  overtime_type: document.getElementById("overtime_type").value,
};
```

**编辑弹窗** — `openEdit()` 加赋值：

```javascript
document.getElementById("edit_overtime_type").value = result.overtime_type;
```

`saveEdit()` 的 `data` 对象同理。

**表格渲染** — `renderTable()` 加一列 `<td>`：

```javascript
+ "<td>" + escapeHtml(r.overtime_type) + "</td>"
```

### 第 6 层：导出 Excel

**文件**: `server.py` — `_handle_export()`

表头数组加标题：

```python
headers = ["序号", ..., "加班类型", "登记时间"]
```

数据行 `values` 对应加：

```python
record.get("overtime_type", ""),
```

列宽数组加一列宽度。

### 额外层：自动关联（如需）

如果新字段也需要 auto-fill 填充：

**文件**: `db.py` — `lookup_employee_info()`

`SELECT` 子句加字段：

```python
f"SELECT employee_name, employee_id, company, project_team, pm, overtime_type "
```

## 时段预设

时段预设是浏览器端功能，不涉及后端和数据库。两个预设按钮点击即填充时间，无 `<select>` 原生延迟。

### 添加预设

**文件**: `static/js/app.js` — `TIME_PRESETS` 对象加一项：

```javascript
var TIME_PRESETS = {
  day:   { start: "08:00:00", end: "17:30:00", label: "早班段" },
  night: { start: "09:00:00", end: "19:00:00", label: "晚班段" },
  // 添加：
  extra: { start: "18:00:00", end: "22:00:00", label: "加班段" },
};
```

**文件**: `static/index.html` — 两处 `.preset-group` 各加一个 `<button>`：

```html
<button type="button" class="btn preset-btn" data-preset="extra" onclick="setTimePreset('extra', this)">加班段 18:00~22:00</button>
<!-- 编辑弹窗同理，用 setEditTimePreset -->
```

键名 `data-preset` 必须与 JS 中的 `TIME_PRESETS` 属性名一致。

### 修改预设

直接修改 `TIME_PRESETS` 中的 `start` / `end` 值（格式 `HH:MM:SS`）或 `label` 即可，无需改 HTML。

### 原理

- `setTimePreset(key, btn)` → 切换按钮 active 态 → 调 `applyTimePreset(key)` 用当前日期拼接 `yyyy-mm-dd HH:MM:SS` 填入 start_time / end_time
- `syncTimeDates()` 在加班日期变更时，若时间字段为空则调用 `applyTimePresetFromCurrent()`（读取当前 active 按钮），保证新日期使用当前预设
- 编辑弹窗有独立的 `setEditTimePreset()` / `applyEditTimePreset()`，逻辑相同
- 每个预设按钮有独立的配色：`data-preset="day"` 日光黄，`data-preset="night"` 月白色，可在 CSS `.preset-btn[data-preset="..."]` 中自定义

## 修改现有字段

与添加流程相同，但注意：

1. **字段重命名** — 6 层所有引用同步改名，前后端一致
2. **约束变更** — 如从 NOT NULL 改为可空，移除 `required` 属性和 `strip()` 校验
3. **类型变更** — 如从 TEXT 改为 SELECT，前端 HTML 换标签，后端加枚举校验

## 测试策略

### 修改字段后的回归清单

| 测试项                 | 方法                                |
| ---------------------- | ----------------------------------- |
| 创建记录含新字段       | POST /api/records → 201             |
| 缺少必填新字段         | POST /api/records → 400             |
| 列表返回新字段         | GET /api/records → 字段存在          |
| 编辑弹窗加载新字段     | GET /api/records/<id> → 字段存在     |
| 更新记录含新字段       | PUT /api/records/<id> → 200          |
| 导出含新字段           | GET /api/records/export → xlsx       |
| 筛选（如可搜索）       | GET /api/records?overtime_type=xxx   |

### 运行 E2E

```bash
source .venv/bin/activate
python3 tests/test_e2e.py
```

新增字段后需要补充对应测试用例到 `tests/test_e2e.py`，遵循"一个测试验证一个行为"的原则。
