"""加班登记系统 - 配置文件"""

# 服务配置
HOST = "0.0.0.0"
PORT = 8080

# 数据库类型: 'sqlite' / 'mysql' / 'postgresql'
DB_TYPE = "sqlite"

# SQLite 配置
SQLITE_DB_PATH = "overtime.db"

# MySQL 配置 (DB_TYPE='mysql' 时生效)
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "overtime_system",
    "charset": "utf8mb4",
}

# PostgreSQL 配置 (DB_TYPE='postgresql' 时生效)
POSTGRESQL_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "",
    "database": "overtime_system",
}
