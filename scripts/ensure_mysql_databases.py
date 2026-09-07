"""Create the two MySQL databases required by the legacy services."""

from __future__ import annotations

import os
import sys

import pymysql


def main() -> int:
    required = ["MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print(f"Missing MySQL settings: {', '.join(missing)}")
        return 2
    try:
        connection = pymysql.connect(
            host=os.environ["MYSQL_HOST"],
            port=int(os.environ["MYSQL_PORT"]),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            autocommit=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS dataflow_canvas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("CREATE DATABASE IF NOT EXISTS highdim_region_vis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.close()
        print("MySQL databases are ready: dataflow_canvas, highdim_region_vis")
        return 0
    except Exception as error:
        print(f"MySQL initialization failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
