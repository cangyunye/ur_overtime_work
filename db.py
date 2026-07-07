"""加班登记系统 - 数据库操作层 (SQLite/MySQL/PostgreSQL 三支持)"""

import sqlite3
import threading
from datetime import datetime, timedelta

import config

_local = threading.local()


def _get_placeholder(index):
    """根据数据库类型返回占位符 (SQLite用?, MySQL/PostgreSQL用%s)"""
    if config.DB_TYPE in ("mysql", "postgresql"):
        return "%s"
    return "?"


def _get_connection():
    """获取线程级数据库连接"""
    if not hasattr(_local, "connection") or _local.connection is None:
        if config.DB_TYPE == "sqlite":
            conn = sqlite3.connect(config.SQLITE_DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
        elif config.DB_TYPE == "mysql":
            try:
                import pymysql
            except ImportError:
                raise RuntimeError("使用 MySQL 需要先安装 pymysql: pip install pymysql")
            mc = config.MYSQL_CONFIG
            conn = pymysql.connect(
                host=mc["host"],
                port=mc["port"],
                user=mc["user"],
                password=mc["password"],
                database=mc["database"],
                charset=mc["charset"],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        else:  # postgresql
            try:
                import psycopg2
                import psycopg2.extras
            except ImportError:
                raise RuntimeError(
                    "使用 PostgreSQL 需要先安装 psycopg2: pip install psycopg2-binary"
                )
            pc = config.POSTGRESQL_CONFIG
            conn = psycopg2.connect(
                host=pc["host"],
                port=pc["port"],
                user=pc["user"],
                password=pc["password"],
                dbname=pc["database"],
            )
            conn.autocommit = True
        _local.connection = conn
    return _local.connection


def _ensure_dict_cursor(conn, cur):
    """确保游标返回字典格式结果（PostgreSQL 需要）"""
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        if not hasattr(cur, "rowcount") or cur.description is None:
            return
        # psycopg2 DictCursor 已在 connect 时设置
        pass


def init_db():
    """初始化数据库表结构"""
    conn = _get_connection()
    cur = conn.cursor()

    if config.DB_TYPE == "sqlite":
        cur.execute("""
            CREATE TABLE IF NOT EXISTS overtime_records (
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
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_overtime_date 
            ON overtime_records(overtime_date)
        """)
    elif config.DB_TYPE == "mysql":
        cur.execute("""
            CREATE TABLE IF NOT EXISTS overtime_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(100) NOT NULL,
                employee_id VARCHAR(50) NOT NULL,
                company VARCHAR(200) NOT NULL,
                project_team VARCHAR(200) NOT NULL,
                pm VARCHAR(100) NOT NULL,
                reason TEXT NOT NULL,
                overtime_date DATE NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_emp_date (employee_id, overtime_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    else:  # postgresql
        cur.execute("""
            CREATE TABLE IF NOT EXISTS overtime_records (
                id SERIAL PRIMARY KEY,
                employee_name VARCHAR(100) NOT NULL,
                employee_id VARCHAR(50) NOT NULL,
                company VARCHAR(200) NOT NULL,
                project_team VARCHAR(200) NOT NULL,
                pm VARCHAR(100) NOT NULL,
                reason TEXT NOT NULL,
                overtime_date DATE NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT LOCALTIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT LOCALTIMESTAMP,
                CONSTRAINT uk_emp_date UNIQUE (employee_id, overtime_date)
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_overtime_date 
            ON overtime_records(overtime_date)
        """)
        # 添加 updated_at 自动更新触发器
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = LOCALTIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_overtime_updated ON overtime_records
        """)
        cur.execute("""
            CREATE TRIGGER trg_overtime_updated
                BEFORE UPDATE ON overtime_records
                FOR EACH ROW EXECUTE FUNCTION update_timestamp()
        """)

    conn.commit()


def insert_record(data):
    """插入加班登记记录"""
    ph = _get_placeholder(0)
    sql = f"""
        INSERT INTO overtime_records
            (employee_name, employee_id, company, project_team, pm, reason,
             overtime_date, start_time, end_time, created_at, updated_at)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = (
        data["employee_name"], data["employee_id"], data["company"],
        data["project_team"], data["pm"], data["reason"],
        data["overtime_date"], data["start_time"], data["end_time"],
        now, now,
    )
    conn = _get_connection()
    cur = conn.cursor()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    if config.DB_TYPE == "sqlite":
        conn.commit()
        last_id = cur.lastrowid
    elif config.DB_TYPE == "mysql":
        last_id = cur.lastrowid
    else:
        conn.commit()
        cur.execute("SELECT lastval()")
        last_id = cur.fetchone()["lastval"]
    return last_id


def update_record(record_id, data):
    """更新加班登记记录"""
    ph = _get_placeholder(0)
    sql = f"""
        UPDATE overtime_records SET
            employee_name={ph}, employee_id={ph}, company={ph},
            project_team={ph}, pm={ph}, reason={ph},
            overtime_date={ph}, start_time={ph}, end_time={ph},
            updated_at={ph}
        WHERE id={ph}
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = (
        data["employee_name"], data["employee_id"], data["company"],
        data["project_team"], data["pm"], data["reason"],
        data["overtime_date"], data["start_time"], data["end_time"],
        now, record_id,
    )
    conn = _get_connection()
    cur = conn.cursor()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    conn.commit()
    return cur.rowcount


def delete_record(record_id):
    """删除加班登记记录"""
    ph = _get_placeholder(0)
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM overtime_records WHERE id={ph}", (record_id,))
    conn.commit()
    return cur.rowcount


def get_record(record_id):
    """获取单条记录"""
    ph = _get_placeholder(0)
    conn = _get_connection()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(f"SELECT * FROM overtime_records WHERE id={ph}", (record_id,))
    row = cur.fetchone()
    if row:
        return dict(row)
    return None


def query_records(date_from=None, date_to=None, company=None, project_team=None,
                  employee_id=None, employee_name=None,
                  page=1, page_size=50):
    """查询加班记录列表（支持分页和筛选）"""
    ph = _get_placeholder(0)
    conditions = []
    params = []

    if date_from:
        conditions.append(f"overtime_date >= {ph}")
        params.append(date_from)
    if date_to:
        conditions.append(f"overtime_date <= {ph}")
        params.append(date_to)
    if company:
        conditions.append(f"company LIKE {ph}")
        params.append(f"%{company}%")
    if project_team:
        conditions.append(f"project_team LIKE {ph}")
        params.append(f"%{project_team}%")
    if employee_id:
        conditions.append(f"employee_id LIKE {ph}")
        params.append(f"%{employee_id}%")
    if employee_name:
        conditions.append(f"employee_name LIKE {ph}")
        params.append(f"%{employee_name}%")

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    conn = _get_connection()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        count_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        count_cur = conn.cursor()

    count_cur.execute(f"SELECT COUNT(*) as total FROM overtime_records {where_clause}", params)
    total = dict(count_cur.fetchone())["total"]

    # 分页查询
    offset = (page - 1) * page_size
    paging = f"LIMIT {ph} OFFSET {ph}"
    params.extend([page_size, offset])
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()

    cur.execute(
        f"SELECT * FROM overtime_records {where_clause} ORDER BY overtime_date DESC, id DESC {paging}",
        params,
    )
    rows = cur.fetchall()
    records = [dict(r) for r in rows]

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def lookup_employee_info(name=None, employee_id=None):
    """根据姓名(模糊)或工号(精确)查询最近登记的关联信息"""
    ph = _get_placeholder(0)
    conn = _get_connection()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()

    if employee_id:
        cur.execute(
            f"SELECT employee_name, employee_id, company, project_team, pm "
            f"FROM overtime_records WHERE employee_id={ph} "
            f"ORDER BY id DESC LIMIT 1",
            (employee_id,)
        )
        row = cur.fetchone()
        if row:
            return {"match": True, "data": dict(row)}

    if name:
        cur.execute(
            f"SELECT employee_id, employee_name, company, project_team, pm "
            f"FROM overtime_records WHERE employee_name LIKE {ph} "
            f"ORDER BY id DESC",
            (f"%{name}%",)
        )
        rows = cur.fetchall()
        if rows:
            records = [dict(r) for r in rows]
            emp_ids = set(r["employee_id"] for r in records)
            if len(emp_ids) == 1:
                return {"match": True, "data": records[0]}
            else:
                seen = set()
                employees = []
                for r in records:
                    if r["employee_id"] not in seen:
                        seen.add(r["employee_id"])
                        employees.append({
                            "employee_name": r["employee_name"],
                            "employee_id": r["employee_id"],
                            "company": r["company"],
                            "project_team": r["project_team"],
                            "pm": r["pm"],
                        })
                return {"match": False, "multiple": True, "employees": employees}

    return {"match": False, "data": None}


def export_all_records(date_from=None, date_to=None, company=None, project_team=None,
                        employee_id=None, employee_name=None):
    """导出全部记录（不分页，用于Excel导出）"""
    ph = _get_placeholder(0)
    conditions = []
    params = []

    if date_from:
        conditions.append(f"overtime_date >= {ph}")
        params.append(date_from)
    if date_to:
        conditions.append(f"overtime_date <= {ph}")
        params.append(date_to)
    if company:
        conditions.append(f"company LIKE {ph}")
        params.append(f"%{company}%")
    if project_team:
        conditions.append(f"project_team LIKE {ph}")
        params.append(f"%{project_team}%")
    if employee_id:
        conditions.append(f"employee_id LIKE {ph}")
        params.append(f"%{employee_id}%")
    if employee_name:
        conditions.append(f"employee_name LIKE {ph}")
        params.append(f"%{employee_name}%")

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    conn = _get_connection()
    if config.DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()

    cur.execute(
        f"SELECT * FROM overtime_records {where_clause} ORDER BY overtime_date DESC, id DESC",
        params,
    )
    return [dict(r) for r in cur.fetchall()]


def get_stats():
    """获取概览统计数据"""
    conn = _get_connection()
    ph = _get_placeholder(0)

    stats = {"weekly_count": 0, "monthly_hours": 0, "total_count": 0}

    # 总数
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM overtime_records")
    stats["total_count"] = dict(cur.fetchone())["total"]

    # 本周人次
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.strftime("%Y-%m-%d")
    cur.execute(
        f"SELECT COUNT(*) as total FROM overtime_records WHERE overtime_date >= {ph}",
        (monday_str,),
    )
    stats["weekly_count"] = dict(cur.fetchone())["total"]

    # 本月总时长（小时）
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    cur.execute(
        f"SELECT start_time, end_time FROM overtime_records WHERE overtime_date >= {ph}",
        (month_start,),
    )
    total_hours = 0
    for row in cur.fetchall():
        d = dict(row)
        try:
            st_val = d["start_time"]
            et_val = d["end_time"]
            st = st_val if isinstance(st_val, datetime) else datetime.strptime(st_val, "%Y-%m-%d %H:%M:%S")
            et = et_val if isinstance(et_val, datetime) else datetime.strptime(et_val, "%Y-%m-%d %H:%M:%S")
            total_hours += (et - st).total_seconds() / 3600
        except (ValueError, KeyError, TypeError):
            pass
    stats["monthly_hours"] = round(total_hours, 1)

    return stats