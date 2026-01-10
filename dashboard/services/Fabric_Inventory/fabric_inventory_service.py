from django.db import connection

def get_fabric_inventory_kpis():
    with connection.cursor() as cursor:

        # 1️⃣ OIH Rate
        cursor.execute("""
            SELECT ROUND(AVG(
                CASE 
                    WHEN ordertype = 'E'
                    THEN (get_today_rate() * rate_in_mtr)
                    ELSE rate_in_mtr
                END
            ))
            FROM db_oih_stock
            WHERE COALESCE(ord_bal_mtr, 0) <> 0
        """)
        oih_rate = cursor.fetchone()[0] or 0

        # 2️⃣ Total Meters
        cursor.execute("""
            SELECT COALESCE(SUM(meter), 0)
            FROM rpt_fabric_db_v2_po
        """)
        total_meter = cursor.fetchone()[0] or 0

        # 3️⃣ Grade A
        cursor.execute("""
            SELECT COALESCE(SUM(meter), 0)
            FROM rpt_fabric_db_v2_po
            WHERE grade = 'A'
        """)
        grade_a = cursor.fetchone()[0] or 0

        # 4️⃣ Grade B
        cursor.execute("""
            SELECT COALESCE(SUM(meter), 0)
            FROM rpt_fabric_db_v2_po
            WHERE grade = 'B'
        """)
        grade_b = cursor.fetchone()[0] or 0

        # 5️⃣ Grade C
        cursor.execute("""
            SELECT COALESCE(SUM(meter), 0)
            FROM rpt_fabric_db_v2_po
            WHERE grade = 'C'
        """)
        grade_c = cursor.fetchone()[0] or 0

    amount = total_meter * oih_rate

    return {
        "kpi_meter": total_meter,
        "kpi_amount": amount,
        "kpi_grade_a": grade_a,
        "kpi_grade_b": grade_b,
        "kpi_grade_c": grade_c,
    }


def get_fresh_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_O' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_C' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_X' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt = 'RFAN' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN') THEN meter END)
            FROM rpt_fabric_db_v2_po
        """)
        v_open, v_close, v_cancel, v_rfan, v_total = cur.fetchone()

        cur.execute("SELECT COALESCE(SUM(meter),0) FROM rpt_fabric_db_v2_po")
        v_sum = cur.fetchone()[0]

    v_open = v_open or 0
    v_close = v_close or 0
    v_cancel = v_cancel or 0
    v_rfan = v_rfan or 0
    v_total = v_total or 0

    overall_pct = round((v_total / v_sum) * 100, 1) if v_sum else 0

    def pct(x):
        return round((x / v_total) * 100, 2) if v_total else 0

    return {
        "fresh": {
            "open": v_open,
            "close": v_close,
            "cancel": v_cancel,
            "rfan": v_rfan,
            "total": v_total,
            "overall_pct": overall_pct,
            "pct_open": pct(v_open),
            "pct_close": pct(v_close),
            "pct_cancel": pct(v_cancel),
            "pct_rfan": pct(v_rfan)
        }
    }

def get_fresh_grade_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(grade, 'BLANK') AS grade, SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN')
            GROUP BY grade
            ORDER BY grade;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [{"grade": g, "value": v, "pct": round(v/total*100, 2)} for g, v in rows]


def get_fresh_manager_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(mkt_person, 'BLANK') AS manager, SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN')
            GROUP BY mkt_person
            ORDER BY mkt_person;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [{"manager": m, "value": v, "pct": round(v/total*100, 2)} for m, v in rows]

def get_fresh_aging_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT age, SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN')
            GROUP BY age, age_ord
            ORDER BY age_ord;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [{"age": a, "value": v, "pct": round(v/total*100, 2)} for a, v in rows]



# STOCK

def get_stock_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                SUM(CASE WHEN system_remarks24rpt = 'STOCK_FRSH' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt = 'STOCK_OTHERS' THEN meter END),
                SUM(CASE WHEN system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS') THEN meter END),
                SUM(CASE WHEN system_remarks = 'SOLD OUT' THEN meter END),
                SUM(CASE 
                        WHEN system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
                         AND system_remarks <> 'SOLD OUT' 
                        THEN meter END)
            FROM rpt_fabric_db_v2_po
        """)
        st_fresh, st_others, st_total, st_sold, net_stock = cur.fetchone()

        cur.execute("SELECT COALESCE(SUM(meter),0) FROM rpt_fabric_db_v2_po")
        sum_meter = cur.fetchone()[0]

    # Defaults
    st_fresh = st_fresh or 0
    st_others = st_others or 0
    st_total = st_total or 0
    st_sold = st_sold or 0
    net_stock = net_stock or 0

    overall_pct = round((net_stock / sum_meter) * 100, 1) if sum_meter else 0

    def pct(x, base):
        return round((x / base) * 100, 2) if base else 0

    return {
        "stock": {
            "fresh": st_fresh,
            "others": st_others,
            "total": st_total,
            "sold": st_sold,
            "net": net_stock,
            "overall_pct": overall_pct,
            "pct_fresh": pct(st_fresh, net_stock),
            "pct_others": pct(st_others, net_stock),
            "pct_sold": pct(st_sold, st_total)
        }
    }

def get_stock_grade_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(grade,'BLANK'), SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
              AND system_remarks <> 'SOLD OUT'
            GROUP BY COALESCE(grade,'BLANK')
            ORDER BY 1
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"grade": g, "value": v, "pct": round(v/total*100, 2)}
        for g, v in rows
    ]

def get_stock_manager_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                CASE
                    WHEN NVL(mkt_person,'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF')
                        THEN 'FAYYAZ / ABDUL RAUF'
                    WHEN NVL(mkt_person,'BLANK') IN ('GHULAM NABI','KHALID')
                        THEN 'GHULAM NABI / KHALID'
                    ELSE NVL(mkt_person,'BLANK')
                END AS manager,
                SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
              AND system_remarks <> 'SOLD OUT'
            GROUP BY
                CASE
                    WHEN NVL(mkt_person,'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF')
                        THEN 'FAYYAZ / ABDUL RAUF'
                    WHEN NVL(mkt_person,'BLANK') IN ('GHULAM NABI','KHALID')
                        THEN 'GHULAM NABI / KHALID'
                    ELSE NVL(mkt_person,'BLANK')
                END
            ORDER BY 1
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"manager": m, "value": v, "pct": round(v/total*100, 2)}
        for m, v in rows
    ]

def get_stock_aging_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT age, SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
              AND system_remarks <> 'SOLD OUT'
            GROUP BY age, age_ord
            ORDER BY age_ord
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"age": a, "value": v, "pct": round(v/total*100, 2)}
        for a, v in rows
    ]
