from django.db import connection
from dashboard.utils.formatters import short_number


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
        "kpi_amount": short_number(amount),
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
            SELECT grade,
                SUM(total_meter) AS total_grades
            FROM (
                SELECT COALESCE(x.grade, 'BLANK') AS grade,
                        SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN')
                GROUP BY COALESCE(x.grade, 'BLANK')

                UNION ALL

                SELECT grade, 0 AS total_meter
                FROM (
                        SELECT 'A' AS grade
                        UNION ALL
                        SELECT 'B'
                        UNION ALL
                        SELECT 'C'
                ) AS g
            ) AS t
            GROUP BY grade
            ORDER BY grade;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [{"grade": g, "value": v, "pct": round(v/total*100, 2)} for g, v in rows]


def get_fresh_manager_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT 
                mkt_person,
                SUM(total_meter) AS total_fresh_mk
            FROM (
                SELECT 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END AS mkt_person,
                    SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt IN ('FRESH_A_O','FRESH_A_C','FRESH_A_X','RFAN')
                GROUP BY 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END

                UNION ALL

                SELECT DISTINCT 
                    CASE 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(m.mkt_person, 'BLANK')
                    END AS mkt_person,
                    0 AS total_meter
                FROM rpt_fabric_db_v2_po m
            ) AS t
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
                SELECT grade,
                SUM(total_meter) AS total_grades
            FROM (
                SELECT COALESCE(x.grade, 'BLANK') AS grade,
                        SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
                  AND system_remarks <> 'SOLD OUT'
                GROUP BY COALESCE(x.grade, 'BLANK')

                UNION ALL

                SELECT grade, 0 AS total_meter
                FROM (
                        SELECT 'A' AS grade
                        UNION ALL
                        SELECT 'B'
                        UNION ALL
                        SELECT 'C'
                ) AS g
            ) AS t
            GROUP BY grade
            ORDER BY grade;
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
                mkt_person,
                SUM(total_meter) AS total_fresh_mk
            FROM (
                SELECT 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END AS mkt_person,
                    SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt  IN ('STOCK_FRSH','STOCK_OTHERS')
              AND system_remarks <> 'SOLD OUT'
                GROUP BY 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END

                UNION ALL

                SELECT DISTINCT 
                    CASE 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(m.mkt_person, 'BLANK')
                    END AS mkt_person,
                    0 AS total_meter
                FROM rpt_fabric_db_v2_po m
            ) AS t
            GROUP BY mkt_person
            ORDER BY mkt_person;
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


# SAMPLE

def get_sample_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(CASE WHEN system_remarks24rpt = 'SAMPLE' THEN meter END), 0)
            FROM rpt_fabric_db_v2_po
        """)
        sample = cur.fetchone()[0]  

        cur.execute("SELECT COALESCE(SUM(meter),0) FROM rpt_fabric_db_v2_po")
        sum_meter = cur.fetchone()[0]

    overall_pct = round((sample / sum_meter) * 100, 1) if sum_meter else 0

    return {
        "sample": {
            "sample": sample,
            "overall_pct": overall_pct
        }
    }


def get_sample_grade_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT grade,
                SUM(total_meter) AS total_grades
            FROM (
                SELECT COALESCE(x.grade, 'BLANK') AS grade,
                        SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt = 'SAMPLE'
                GROUP BY COALESCE(x.grade, 'BLANK')

                UNION ALL

                SELECT grade, 0 AS total_meter
                FROM (
                        SELECT 'A' AS grade
                        UNION ALL
                        SELECT 'B'
                        UNION ALL
                        SELECT 'C'
                ) AS g
            ) AS t
            GROUP BY grade
            ORDER BY grade;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"grade": g, "value": v, "pct": round(v / total * 100, 2)}
        for g, v in rows
    ]


def get_sample_manager_data():
    with connection.cursor() as cur:
        cur.execute("""
                        SELECT 
                mkt_person,
                SUM(total_meter) AS total_fresh_mk
            FROM (
                SELECT 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END AS mkt_person,
                    SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt  IN ('SAMPLE')
                GROUP BY 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END

                UNION ALL

                SELECT DISTINCT 
                    CASE 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(m.mkt_person, 'BLANK')
                    END AS mkt_person,
                    0 AS total_meter
                FROM rpt_fabric_db_v2_po m
            ) AS t
            GROUP BY mkt_person
            ORDER BY mkt_person;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"manager": m, "value": v, "pct": round(v / total * 100, 2)}
        for m, v in rows
    ]


def get_sample_aging_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                age,
                age_ord,
                SUM(total_sr_age) AS total_sr_age
            FROM (
                SELECT 
                    x.age,
                    x.age_ord,
                    SUM(x.meter) AS total_sr_age
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt = 'SAMPLE'
                GROUP BY x.age, x.age_ord

                UNION ALL

                SELECT DISTINCT 
                    m.age,
                    m.age_ord,
                    0 AS total_sr_age
                FROM rpt_fabric_db_v2_po m
            ) AS t
            GROUP BY age, age_ord
            ORDER BY age_ord;
        """)
        rows = cur.fetchall()

    # rows: (age, age_ord, value)
    total = sum(row[2] for row in rows) or 1

    return [
        {
            "age": row[0],
            "value": row[2],
            "pct": round(row[2] / total * 100, 2)
        }
        for row in rows
    ]
    
# SALES RETURN

def get_sales_return_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(CASE WHEN system_remarks24rpt = 'SALES RETURN' THEN meter END), 0)
            FROM rpt_fabric_db_v2_po
        """)
        sales_return = cur.fetchone()[0]   

        cur.execute("SELECT COALESCE(SUM(meter),0) FROM rpt_fabric_db_v2_po")
        sum_meter = cur.fetchone()[0]

    overall_pct = round((sales_return / sum_meter) * 100, 1) if sum_meter else 0

    return {
        "sr": {
            "sales_return": sales_return,
            "overall_pct": overall_pct
        }
    }


def get_sales_return_grade_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(grade,'BLANK'), SUM(meter)
            FROM rpt_fabric_db_v2_po
            WHERE system_remarks24rpt IN ('SALES RETURN')
            GROUP BY COALESCE(grade,'BLANK')
            ORDER BY 1
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"grade": g, "value": v, "pct": round(v / total * 100, 2)}
        for g, v in rows
    ]


def get_sales_return_manager_data():
    with connection.cursor() as cur:
        cur.execute("""
                        SELECT 
                mkt_person,
                SUM(total_meter) AS total_fresh_mk
            FROM (
                SELECT 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END AS mkt_person,
                    SUM(x.meter) AS total_meter
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt  IN ('SALES RETURN')
                GROUP BY 
                    CASE 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(x.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(x.mkt_person, 'BLANK')
                    END

                UNION ALL

                SELECT DISTINCT 
                    CASE 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('ABBAS,FAYYAZ','ABDUL RAUF') THEN
                            'FAYYAZ / ABDUL RAUF' 
                        WHEN COALESCE(m.mkt_person, 'BLANK') IN ('GHULAM NABI','KHALID') THEN
                            'GHULAM NABI / KHALID'
                        ELSE 
                            COALESCE(m.mkt_person, 'BLANK')
                    END AS mkt_person,
                    0 AS total_meter
                FROM rpt_fabric_db_v2_po m
            ) AS t
            GROUP BY mkt_person
            ORDER BY mkt_person;
        """)
        rows = cur.fetchall()

    total = sum(v for _, v in rows) or 1

    return [
        {"manager": m, "value": v, "pct": round(v / total * 100, 2)}
        for m, v in rows
    ]


def get_sales_return_aging_data():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                age,
                age_ord,
                SUM(total_sr_age) AS total_sr_age
            FROM (
                SELECT 
                    x.age,
                    x.age_ord,
                    SUM(x.meter) AS total_sr_age
                FROM rpt_fabric_db_v2_po x
                WHERE x.system_remarks24rpt = 'SALES RETURN'
                GROUP BY x.age, x.age_ord

                UNION ALL

                SELECT DISTINCT 
                    m.age,
                    m.age_ord,
                    0 AS total_sr_age
                FROM rpt_fabric_db_v2_po m
            ) AS t
            GROUP BY age, age_ord
            ORDER BY age_ord;
        """)
        rows = cur.fetchall()

    # rows: (age, age_ord, value)
    total = sum(row[2] for row in rows) or 1

    return [
        {
            "age": row[0],
            "value": row[2],
            "pct": round(row[2] / total * 100, 2)
        }
        for row in rows
    ]
