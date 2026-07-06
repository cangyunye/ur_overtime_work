"""
加班登记系统 - E2E 测试
测试所有公开 HTTP API 的行为，不依赖内部实现细节。

运行:
    python3 tests/test_e2e.py [--port PORT]
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PORT = 9191
PASS = 0
FAIL = 0


def section(name):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")


def ok(msg):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")


def fail(msg, detail=""):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"         {line}")


def request(method, path, body=None, expect_status=None):
    url = f"http://127.0.0.1:{SERVER_PORT}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8")
    except urllib.error.URLError as e:
        return None, None, str(e)

    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = raw

    if expect_status is not None and status != expect_status:
        return status, parsed, f"expected {expect_status}, got {status}: {raw[:200]}"

    return status, parsed, None


def assert_eq(label, actual, expected):
    if actual == expected:
        ok(label)
    else:
        fail(label, f"got: {json.dumps(actual, ensure_ascii=False)}\nexpected: {json.dumps(expected, ensure_ascii=False)}")


def assert_in(label, actual, expected_sub):
    if expected_sub in str(actual):
        ok(label)
    else:
        fail(label, f"expected substring: {expected_sub}\ngot: {json.dumps(actual, ensure_ascii=False)}")


def assert_true(label, condition, detail=""):
    if condition:
        ok(label)
    else:
        fail(label, detail)


# ---- Server Management ----

def start_server():
    global SERVER_PORT
    db_path = os.path.join(BASE_DIR, f"test_e2e_{SERVER_PORT}.db")
    # Remove old test db
    if os.path.exists(db_path):
        os.remove(db_path)
    cfg_path = os.path.join(BASE_DIR, "config.py")
    # Read config to set path
    server_script = os.path.join(BASE_DIR, "server.py")
    proc = subprocess.Popen(
        [sys.executable, server_script, "sqlite3", "--db-path", db_path, "--port", str(SERVER_PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    # Check if alive
    if proc.poll() is not None:
        print(f"[ERROR] Server failed to start (exit code {proc.returncode})")
        sys.exit(1)
    return proc, db_path


def stop_server(proc, db_path):
    proc.terminate()
    proc.wait()
    if os.path.exists(db_path):
        os.remove(db_path)


# ---- Test Cases ----

def test_create_record():
    section("1. 创建记录")

    # TC-CR-01: 正常创建
    status, data, err = request("POST", "/api/records", {
        "employee_name": "张三",
        "employee_id": "E2E001",
        "company": "测试科技有限公司",
        "project_team": "平台研发组",
        "pm": "李四",
        "reason": "项目上线前紧急修复",
        "overtime_date": "2026-07-11",
        "start_time": "2026-07-11 09:00:00",
        "end_time": "2026-07-11 18:00:00",
    }, 201)
    assert_true("POST 201 创建成功", status == 201 and data.get("id") == 1,
                f"status={status} data={data}")

    # TC-CR-02: 缺少必填字段
    status, data, err = request("POST", "/api/records", {"employee_name": ""}, 400)
    assert_in("POST 400 缺少必填字段", data.get("error", ""), "以下字段为必填项")

    # TC-CR-03: 时间格式错误
    status, data, err = request("POST", "/api/records", {
        "employee_name": "测试", "employee_id": "E003", "company": "c",
        "project_team": "p", "pm": "p", "reason": "r",
        "overtime_date": "2026-07-12", "start_time": "bad-time",
        "end_time": "2026-07-12 18:00:00",
    }, 400)
    assert_in("POST 400 时间格式错误", data.get("error", ""), "格式错误")

    # TC-CR-04: 结束时间早于开始时间
    status, data, err = request("POST", "/api/records", {
        "employee_name": "测试", "employee_id": "E004", "company": "c",
        "project_team": "p", "pm": "p", "reason": "r",
        "overtime_date": "2026-07-12",
        "start_time": "2026-07-12 18:00:00",
        "end_time": "2026-07-12 09:00:00",
    }, 400)
    assert_in("POST 400 结束时间早于开始时间", data.get("error", ""), "结束时间必须晚于开始时间")

    # TC-CR-05: 工号+日期重复 → 409
    status, data, err = request("POST", "/api/records", {
        "employee_name": "张三", "employee_id": "E2E001",
        "company": "测试科技有限公司", "project_team": "平台研发组",
        "pm": "李四", "reason": "重复提交",
        "overtime_date": "2026-07-11",
        "start_time": "2026-07-11 09:00:00",
        "end_time": "2026-07-11 18:00:00",
    }, 409)
    assert_in("POST 409 重复工号+日期", data.get("error", ""), "已存在登记记录")

    # 创建更多记录供后续测试
    extra = [
        ("张三", "E2E001", "测试科技有限公司", "平台研发组", "李四", "修复",
         "2026-07-12", "2026-07-12 09:00:00", "2026-07-12 18:00:00"),
        ("李四", "E2E002", "云技术公司", "基础设施组", "王五", "部署",
         "2026-07-13", "2026-07-13 10:00:00", "2026-07-13 20:00:00"),
        ("张三", "E2E003", "数据智能公司", "AI平台组", "赵六", "训练",
         "2026-07-14", "2026-07-14 09:00:00", "2026-07-14 18:00:00"),
    ]
    for name, eid, comp, team, pm, reason, date, start, end in extra:
        request("POST", "/api/records", {
            "employee_name": name, "employee_id": eid, "company": comp,
            "project_team": team, "pm": pm, "reason": reason,
            "overtime_date": date, "start_time": start, "end_time": end,
        }, 201)
    ok("4条测试记录创建完毕")


def test_get_single_record():
    section("2. 获取单条记录")

    status, data, err = request("GET", "/api/records/1", None, 200)
    assert_true("GET /api/records/1 200", status == 200 and data.get("id") == 1,
                f"got id={data.get('id')}")

    status, data, err = request("GET", "/api/records/99999", None, 404)
    assert_eq("GET 99999 404", data.get("error"), "记录不存在")

    status, data, err = request("GET", "/api/records/abc", None, 400)
    assert_eq("GET abc 400", data.get("error"), "无效的记录ID")


def test_list_records():
    section("3. 查询记录列表")

    # TC-LR-01: 查询全部（无筛选）
    status, data, err = request("GET", "/api/records?page=1&page_size=50", None, 200)
    assert_true("GET 全部记录", status == 200 and data.get("total", 0) == 4,
                f"total={data.get('total', 0)}")

    # TC-LR-02: 按日期范围筛选
    status, data, err = request(
        "GET", "/api/records?date_from=2026-07-13&date_to=2026-07-13&page=1&page_size=50",
        None, 200)
    assert_eq("GET 日期筛选 1条", data.get("total"), 1)

    # TC-LR-03: 合作公司模糊筛选
    status, data, err = request(
        "GET", "/api/records?company=%E6%8A%80%E6%9C%AF&page=1&page_size=50",
        None, 200)
    assert_true("GET 公司筛选", data.get("total", 0) >= 1, f"total={data.get('total', 0)}")

    # TC-LR-04: 项目组模糊筛选
    status, data, err = request(
        "GET", "/api/records?project_team=%E5%B9%B3%E5%8F%B0&page=1&page_size=50",
        None, 200)
    assert_true("GET 项目组筛选", data.get("total", 0) >= 1, f"total={data.get('total', 0)}")

    # TC-LR-05: 工号模糊筛选
    status, data, err = request(
        "GET", "/api/records?employee_id=E2E&page=1&page_size=50", None, 200)
    assert_eq("GET 工号筛选 4条", data.get("total"), 4)

    # TC-LR-06: 名称模糊筛选
    status, data, err = request(
        "GET", "/api/records?employee_name=%E5%BC%A0&page=1&page_size=50", None, 200)
    assert_eq("GET 名称筛选 3条", data.get("total"), 3)

    # TC-LR-07: 空结果
    status, data, err = request(
        "GET", "/api/records?company=__NONEXIST__&page=1&page_size=50", None, 200)
    assert_eq("GET 空结果 records", data.get("records"), [])

    # TC-LR-08: page_size 参数
    for ps in [15, 30, 50, 100]:
        status, data, err = request("GET", f"/api/records?page=1&page_size={ps}", None, 200)
        assert_eq(f"GET page_size={ps}", data.get("page_size"), ps)

    # TC-LR-09: total_pages
    status, data, err = request("GET", "/api/records?page=1&page_size=3", None, 200)
    assert_true("GET total_pages >=2", data.get("total_pages", 0) >= 2,
                f"total={data.get('total')} page_size=3 → pages={data.get('total_pages')}")


def test_auto_fill():
    section("4. 自动关联 auto-fill")

    # TC-AF-01: 按工号精确匹配
    status, data, err = request("GET", "/api/auto-fill?employee_id=E2E001", None, 200)
    assert_true("AF 工号匹配", data.get("match") is True,
                f"match={data.get('match')} data={data.get('data')}")

    # TC-AF-02: 按姓名匹配（唯一工号）
    request("POST", "/api/records", {
        "employee_name": "独孤求败", "employee_id": "E2E_UNIQUE",
        "company": "独家公司", "project_team": "独立组", "pm": "PM",
        "reason": "测试", "overtime_date": "2026-07-15",
        "start_time": "2026-07-15 09:00:00", "end_time": "2026-07-15 18:00:00",
    }, 201)
    status, data, err = request(
        "GET", "/api/auto-fill?name=%E7%8B%AC%E5%AD%A4%E6%B1%82%E8%B4%A5", None, 200)
    assert_true("AF 姓名唯一匹配", data.get("match") is True,
                f"match={data.get('match')}")

    # TC-AF-03: 姓名匹配多条 → multiple=True
    status, data, err = request(
        "GET", "/api/auto-fill?name=%E5%BC%A0%E4%B8%89", None, 200)
    assert_true("AF 姓名多条(multiple)",
                data.get("match") is False and data.get("multiple") is True,
                f"match={data.get('match')} multiple={data.get('multiple')}")
    assert_true("AF 员工列表 >=2",
                isinstance(data.get("employees"), list) and len(data["employees"]) >= 2,
                f"count={len(data.get('employees', []))}")

    # TC-AF-04: 姓名+工号消歧
    status, data, err = request(
        "GET", "/api/auto-fill?name=%E5%BC%A0%E4%B8%89&employee_id=E2E003", None, 200)
    assert_true("AF 姓名+工号消歧", data.get("match") is True,
                f"match={data.get('match')}")
    if data.get("data"):
        assert_eq("AF 消歧工号正确", data["data"].get("employee_id"), "E2E003")

    # TC-AF-05: 无匹配
    status, data, err = request(
        "GET", "/api/auto-fill?name=__NONEXIST__", None, 200)
    assert_eq("AF 无匹配 match=False", data.get("match"), False)

    # TC-AF-06: 缺少参数 → 400
    status, data, err = request("GET", "/api/auto-fill", None, 400)
    assert_in("AF 400 缺少参数", data.get("error", ""), "请提供姓名或工号")


def test_update_record():
    section("5. 更新记录")

    # TC-UP-01: 正常更新
    status, data, err = request("PUT", "/api/records/1", {
        "employee_name": "张三丰",
        "employee_id": "E2E001",
        "company": "新公司",
        "project_team": "新组",
        "pm": "新PM",
        "reason": "更新测试",
        "overtime_date": "2026-07-11",
        "start_time": "2026-07-11 10:00:00",
        "end_time": "2026-07-11 20:00:00",
    }, 200)
    assert_eq("PUT 200 更新成功", data.get("message"), "更新成功")

    # 验证持久化
    status, data, err = request("GET", "/api/records/1", None, 200)
    assert_eq("PUT 验证持久化 company", data.get("company"), "新公司")

    # TC-UP-02: 更新不存在的记录
    status, data, err = request("PUT", "/api/records/99999", {
        "employee_name": "x", "employee_id": "x",
        "company": "x", "project_team": "x", "pm": "x",
        "reason": "x", "overtime_date": "2026-07-11",
        "start_time": "2026-07-11 09:00:00", "end_time": "2026-07-11 18:00:00",
    }, 404)
    assert_eq("PUT 404 不存在", data.get("error"), "记录不存在")

    # TC-UP-03: 更新导致工号+日期冲突
    # Record 1 is E2E001 + 2026-07-11; E2E001 also has record 2 on 2026-07-12
    # Change record 2 to 2026-07-12 → record 2 itself, not a conflict
    # Change record 2 (E2E001, date=2026-07-12) to date=2026-07-11 → conflicts with record 1
    status, data, err = request("PUT", "/api/records/2", {
        "employee_name": "张三", "employee_id": "E2E001",
        "company": "x", "project_team": "x", "pm": "x",
        "reason": "x", "overtime_date": "2026-07-11",
        "start_time": "2026-07-11 09:00:00", "end_time": "2026-07-11 18:00:00",
    }, 409)
    assert_in("PUT 409 冲突", data.get("error", ""), "已存在登记记录")


def test_delete_record():
    section("6. 删除记录")

    # 创建待删记录
    request("POST", "/api/records", {
        "employee_name": "待删除", "employee_id": "E2E_DEL",
        "company": "c", "project_team": "p", "pm": "p",
        "reason": "r", "overtime_date": "2026-07-20",
        "start_time": "2026-07-20 09:00:00", "end_time": "2026-07-20 18:00:00",
    }, 201)

    # TC-DL-01: 正常删除 (record 6 = E2E_DEL)
    status, data, err = request("DELETE", "/api/records/6", None, 200)
    assert_eq("DELETE 200 删除成功", data.get("message"), "删除成功")

    # 验证已删除
    status, data, err = request("GET", "/api/records/6", None, 404)
    assert_eq("DELETE 验证已删除", data.get("error"), "记录不存在")

    # TC-DL-02: 删除不存在的记录
    status, data, err = request("DELETE", "/api/records/99999", None, 404)
    assert_eq("DELETE 404 不存在", data.get("error"), "记录不存在")


def test_export():
    section("7. 导出 Excel")

    if not HAS_OPENPYXL:
        print("  [SKIP] 需要安装 openpyxl: pip3 install openpyxl")
        return

    url = f"http://127.0.0.1:{SERVER_PORT}/api/records/export"
    with urllib.request.urlopen(url) as resp:
        content_type = resp.headers.get("Content-Type", "")
        assert_true("EX 导出 xlsx", resp.status == 200 and "openxml" in content_type,
                    f"status={resp.status} type={content_type}")

    url2 = f"http://127.0.0.1:{SERVER_PORT}/api/records/export?employee_id=E2E001"
    with urllib.request.urlopen(url2) as resp:
        assert_true("EX 筛选导出 200", resp.status == 200,
                    f"status={resp.status}")


# ---- Main ----

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="加班登记系统 E2E 测试")
    parser.add_argument("--port", type=int, default=9191, help="服务端口")
    args = parser.parse_args()
    SERVER_PORT = args.port

    print("=" * 50)
    print("  加班登记系统 - E2E 测试")
    print("=" * 50)

    proc, db_path = start_server()
    print(f"\n[INFO] 服务已启动 (port={SERVER_PORT})")

    try:
        test_create_record()
        test_get_single_record()
        test_list_records()
        test_auto_fill()
        test_update_record()
        test_delete_record()
        test_export()
    finally:
        stop_server(proc, db_path)

    total = PASS + FAIL
    print(f"\n{'='*50}")
    print(f"  结果: {PASS}/{total} 通过", end="")
    if FAIL > 0:
        print(f", {FAIL} 失败", end="")
    print()
    print(f"{'='*50}")

    sys.exit(1 if FAIL > 0 else 0)
