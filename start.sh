#!/usr/bin/env bash
# ============================================================
#  加班登记系统 - 启动脚本
#
#  读取同级目录下的 .env 文件，自动构建 server.py 命令行参数并启动。
#  如需临时覆盖 .env 中的值，可传入环境变量：
#    PORT=9000 ./start.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# ---- 加载 .env（逐行解析，兼容 CRLF/BOM/引号） ----
if [[ -f "$ENV_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # 去除 UTF-8 BOM (\xEF\xBB\xBF)
        line="${line#$(printf '\xEF\xBB\xBF')}"
        # 去除行尾回车符 (CRLF -> LF)
        line="${line%$'\r'}"
        # 去除首尾空白
        line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        # 跳过空行和注释
        [[ -z "$line" || "$line" == '#'* ]] && continue
        # 提取键值对
        key="${line%%=*}"
        value="${line#*=}"
        # 去除值两侧的引号
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        # 去除值两侧的空白
        value="$(printf '%s' "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        export "$key=$value"
    done < "$ENV_FILE"
fi

# ---- 检查 Python ----
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] 未找到 python3"
    exit 1
fi

# ---- 根据 DB_TYPE 构建命令 ----
DB_TYPE="${DB_TYPE:-sqlite}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

case "$DB_TYPE" in
    sqlite)
        SQLITE_DB_PATH="${SQLITE_DB_PATH:-overtime.db}"
        exec python3 "${SCRIPT_DIR}/server.py" db \
            --db-path "$SQLITE_DB_PATH" \
            --host "$HOST" \
            --port "$PORT"
        ;;
    mysql)
        MYSQL_HOST="${MYSQL_HOST:-localhost}"
        MYSQL_PORT="${MYSQL_PORT:-3306}"
        MYSQL_USER="${MYSQL_USER:-root}"
        MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
        MYSQL_DATABASE="${MYSQL_DATABASE:-overtime_system}"
        MYSQL_CHARSET="${MYSQL_CHARSET:-utf8mb4}"
        exec python3 "${SCRIPT_DIR}/server.py" my \
            --db-host "$MYSQL_HOST" \
            --db-port "$MYSQL_PORT" \
            --db-user "$MYSQL_USER" \
            --db-password "$MYSQL_PASSWORD" \
            --db-database "$MYSQL_DATABASE" \
            --db-charset "$MYSQL_CHARSET" \
            --host "$HOST" \
            --port "$PORT"
        ;;
    postgresql)
        PG_HOST="${PG_HOST:-localhost}"
        PG_PORT="${PG_PORT:-5432}"
        PG_USER="${PG_USER:-postgres}"
        PG_PASSWORD="${PG_PASSWORD:-}"
        PG_DATABASE="${PG_DATABASE:-overtime_system}"
        exec python3 "${SCRIPT_DIR}/server.py" pg \
            --db-host "$PG_HOST" \
            --db-port "$PG_PORT" \
            --db-user "$PG_USER" \
            --db-password "$PG_PASSWORD" \
            --db-database "$PG_DATABASE" \
            --host "$HOST" \
            --port "$PORT"
        ;;
    *)
        echo "[ERROR] .env 中 DB_TYPE 必须是 sqlite / mysql / postgresql 之一"
        exit 1
        ;;
esac
