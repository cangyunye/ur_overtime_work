# 加班登记系统 - 测试用例文档

## 一、API 接口测试用例

### 1.1 创建加班记录 (POST /api/records)

#### TC-001: 正常创建

- **请求**:
  ```bash
  curl -X POST http://localhost:8080/api/records \
    -H "Content-Type: application/json" \
    -d '{
      "employee_name": "张三",
      "employee_id": "EMP001",
      "company": "A科技公司",
      "project_team": "平台研发组",
      "pm": "李四",
      "reason": "项目上线前紧急修复",
      "overtime_date": "2026-07-11",
      "start_time": "2026-07-11 09:00:00",
      "end_time": "2026-07-11 18:00:00"
    }'
  ```
- **预期响应** (HTTP 201):
  ```json
  { "message": "登记成功", "id": 1 }
  ```

#### TC-002: 缺少必填字段

- **请求**:
  ```bash
  curl -X POST http://localhost:8080/api/records \
    -H "Content-Type: application/json" \
    -d '{"employee_name": ""}'
  ```
- **预期响应** (HTTP 400):
  ```json
  { "error": "以下字段为必填项: employee_name, employee_id, company, project_team, pm, reason, overtime_date, start_time, end_time" }
  ```

#### TC-003: 时间格式错误

- **请求**:
  ```bash
  curl -X POST http://localhost:8080/api/records \
    -H "Content-Type: application/json" \
    -d '{
      "employee_name": "测试", "employee_id": "E003", "company": "c",
      "project_team": "p", "pm": "p", "reason": "r",
      "overtime_date": "2026-07-12", "start_time": "bad-time",
      "end_time": "2026-07-12 18:00:00"
    }'
  ```
- **预期响应** (HTTP 400):
  ```json
  { "error": "start_time 格式错误，应为 yyyy-mm-dd hh24:mi:ss" }
  ```

#### TC-004: 结束时间早于开始时间

- **请求**:
  ```bash
  curl -X POST http://localhost:8080/api/records \
    -H "Content-Type: application/json" \
    -d '{
      "employee_name": "测试", "employee_id": "E004", "company": "c",
      "project_team": "p", "pm": "p", "reason": "r",
      "overtime_date": "2026-07-12",
      "start_time": "2026-07-12 18:00:00",
      "end_time": "2026-07-12 09:00:00"
    }'
  ```
- **预期响应** (HTTP 400):
  ```json
  { "error": "结束时间必须晚于开始时间" }
  ```

#### TC-005: 工号+日期重复提交

- **前提**: 已存在 EMP001 在 2026-07-11 的记录
- **请求**: 同 TC-001
- **预期响应** (HTTP 409):
  ```json
  { "error": "该工号在此日期已存在登记记录" }
  ```

---

### 1.2 查询记录列表 (GET /api/records)

#### TC-006: 查询全部记录

- **请求**:
  ```bash
  curl "http://localhost:8080/api/records?page=1&page_size=20"
  ```
- **预期响应** (HTTP 200):
  ```json
  {
    "records": [ { "id": 1, "employee_name": "张三", ... } ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```

#### TC-007: 按日期范围筛选

- **请求**:
  ```bash
  curl "http://localhost:8080/api/records?date_from=2026-07-12&date_to=2026-07-12"
  ```
- **预期**: 仅返回加班日期在 2026-07-12 的记录

#### TC-008: 按合作公司模糊筛选

- **请求**:
  ```bash
  curl "http://localhost:8080/api/records?company=科技"
  ```
- **预期**: 仅返回合作公司名称包含"科技"的记录

#### TC-009: 按项目组模糊筛选

- **请求**:
  ```bash
  curl "http://localhost:8080/api/records?project_team=研发"
  ```
- **预期**: 仅返回项目组名称包含"研发"的记录

#### TC-010: 空结果

- **请求**:
  ```bash
  curl "http://localhost:8080/api/records?company=不存在的公司"
  ```
- **预期响应**:
  ```json
  { "records": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0 }
  ```

---

### 1.3 更新记录 (PUT /api/records/:id)

#### TC-011: 正常更新

- **请求**:
  ```bash
  curl -X PUT http://localhost:8080/api/records/1 \
    -H "Content-Type: application/json" \
    -d '{
      "employee_name": "张三丰", "employee_id": "EMP001",
      "company": "B科技有限公司", "project_team": "基础架构组",
      "pm": "王五", "reason": "系统架构升级",
      "overtime_date": "2026-07-11",
      "start_time": "2026-07-11 10:00:00",
      "end_time": "2026-07-11 20:00:00"
    }'
  ```
- **预期响应** (HTTP 200):
  ```json
  { "message": "更新成功" }
  ```

#### TC-012: 更新不存在的记录

- **请求**:
  ```bash
  curl -X PUT http://localhost:8080/api/records/9999 \
    -H "Content-Type: application/json" \
    -d '{"employee_name": "x", ...}'
  ```
- **预期响应** (HTTP 404):
  ```json
  { "error": "记录不存在" }
  ```

#### TC-013: 更新时工号日期冲突

- **前提**: 已有 EMP001 2026-07-11 和 EMP002 2026-07-12
- **请求**: 将 EMP002 的日期改为 2026-07-11
- **预期响应** (HTTP 409):
  ```json
  { "error": "该工号在此日期已存在登记记录" }
  ```

---

### 1.4 删除记录 (DELETE /api/records/:id)

#### TC-014: 正常删除

- **请求**:
  ```bash
  curl -X DELETE http://localhost:8080/api/records/1
  ```
- **预期响应** (HTTP 200):
  ```json
  { "message": "删除成功" }
  ```

#### TC-015: 删除不存在的记录

- **请求**:
  ```bash
  curl -X DELETE http://localhost:8080/api/records/9999
  ```
- **预期响应** (HTTP 404):
  ```json
  { "error": "记录不存在" }
  ```

---

### 1.5 导出 Excel (GET /api/records/export)

#### TC-016: 导出全部记录

- **请求**:
  ```bash
  curl -o export.xlsx "http://localhost:8080/api/records/export"
  ```
- **预期**: 下载 .xlsx 文件，包含表头和数据行

#### TC-017: 按筛选条件导出

- **请求**:
  ```bash
  curl -o export.xlsx "http://localhost:8080/api/records/export?date_from=2026-07-11&date_to=2026-07-12"
  ```
- **预期**: 仅导出符合筛选条件的记录

---

## 二、前端功能测试用例

### 2.1 表单默认值

#### TC-018: 加班日期默认为最近周六

- **操作**: 打开页面，查看"计划加班日期"字段
- **预期**: 自动填充为当前日期之后最近的周六日期 (yyyy-mm-dd)

#### TC-019: 日期联动填充时间

- **操作**: 修改加班日期字段
- **预期**: 如果开始/结束时间为空，自动填充为 `日期 09:00:00` 和 `日期 18:00:00`

### 2.2 表单校验

#### TC-020: 前端必填校验

- **操作**: 清空所有字段后点击"提交登记"
- **预期**: 各字段下方显示红色错误提示

#### TC-021: 前端格式校验

- **操作**: 输入格式错误的时间，如 `bad-time`
- **预期**: 显示"格式应为 yyyy-mm-dd hh24:mi:ss"错误提示

### 2.3 列表操作

#### TC-022: 编辑记录

- **操作**: 点击列表中某条记录的"编辑"按钮
- **预期**: 弹出编辑弹窗，字段预填当前值；修改后点击保存，列表刷新

#### TC-023: 删除记录

- **操作**: 点击"删除"按钮，确认弹窗
- **预期**: 记录被删除，列表刷新

#### TC-024: 分页

- **操作**: 当记录超过20条时查看分页
- **预期**: 底部显示分页按钮，点击可切换页码

### 2.4 Excel 导出

#### TC-025: 点击导出按钮

- **操作**: 点击"导出 Excel"按钮
- **预期**: 浏览器下载 .xlsx 文件

### 2.5 响应式布局

#### TC-026: 移动端适配

- **操作**: 缩小浏览器宽度至 768px 以下
- **预期**: 表单变为单列布局，表格可横向滚动

---

## 三、启动方式

```bash
# SQLite 模式 (默认)
cd overtime_system
python3 server.py --port 8080

# MySQL 模式
python3 server.py --db-type mysql \
  --mysql-host localhost \
  --mysql-port 3306 \
  --mysql-user root \
  --mysql-password yourpassword \
  --mysql-database overtime_system
```
