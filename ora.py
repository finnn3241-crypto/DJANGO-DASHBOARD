import oracledb
import psycopg2

# ---------- ORACLE ----------
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_19_28")

ORACLE_CONFIG = {
    "host": "172.16.121.210",
    "port": 1521,
    "sid": "smdb",
    "user": "cmpr",
    "password": "cmprsmcmpr",
}

def get_oracle_connection():
    dsn = oracledb.makedsn(
        ORACLE_CONFIG["host"],
        ORACLE_CONFIG["port"],
        sid=ORACLE_CONFIG["sid"]
    )
    return oracledb.connect(
        user=ORACLE_CONFIG["user"],
        password=ORACLE_CONFIG["password"],
        dsn=dsn
    )

# ---------- POSTGRES ----------
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "erp_db",
    "user": "postgres",
    "password": "moin123"
}

def get_pg_connection():
    
    return psycopg2.connect(**PG_CONFIG)

# ---------- TRANSFER DATA ----------
oracle_conn = get_oracle_connection()
oracle_cur = oracle_conn.cursor()

oracle_cur.execute("SELECT * FROM gl_postage")
rows = oracle_cur.fetchall()

# 🔹 Get column names dynamically
columns = [col[0].lower() for col in oracle_cur.description]

oracle_cur.close()
oracle_conn.close()

pg_conn = get_pg_connection()
pg_cur = pg_conn.cursor()

# 🔹 Build dynamic INSERT
columns_sql = ", ".join(columns)
placeholders = ", ".join(["%s"] * len(columns))

insert_sql = f"""
    INSERT INTO gl_postage ({columns_sql})
    VALUES ({placeholders})
"""

pg_cur.executemany(insert_sql, rows)
pg_conn.commit()

pg_cur.close()
pg_conn.close()

print(f"{len(rows)} rows inserted successfully")
