from django.db import connection

def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def sample_first():

    with connection.cursor() as cur:

        # ---------------- RATE ----------------
        cur.execute("""
            SELECT COALESCE(ROUND(SUM(pkr_amt) / NULLIF(SUM(wt),0)),0)
            FROM gl_postage
            WHERE to_char(vdate,'YYYYMM') = to_char(current_date,'YYYYMM')
        """)
        rate = cur.fetchone()[0]

        # ---------------- TOTALS ----------------
        cur.execute("""
            SELECT COALESCE(SUM(gmsm_qnty),0)
            FROM db_sample_data
            WHERE to_char(gmsm_date,'YYYYMM') = to_char(current_date,'YYYYMM')
        """)
        month_total = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(gmsm_qnty),0)
            FROM db_sample_data
            WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
        """)
        prev_day_total = cur.fetchone()[0]

        # ---------------- PREVIOUS DAY : REASON ----------------
        cur.execute("""
            SELECT reason, SUM(qty) qty
            FROM (
                SELECT
                  CASE
                    WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                    WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                  END reason,
                  gmsm_qnty qty
                FROM db_sample_data
                WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
                  AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
            ) x
            GROUP BY reason
        """)
        prev_day_reason = dictfetchall(cur)

        # ---------------- PREVIOUS DAY : MANAGER ----------------
        cur.execute("""
            SELECT manager_name, SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
            GROUP BY manager_name
            ORDER BY manager_name
        """)
        prev_day_manager = dictfetchall(cur)

        # ---------------- PREVIOUS DAY : CATEGORY ----------------
        cur.execute("""
            SELECT
              CASE
                WHEN munit IN ('FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG')
                THEN munit ELSE 'OTHERS'
              END category,
              SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
            GROUP BY category
            ORDER BY category
        """)
        prev_day_category = dictfetchall(cur)

        # ---------------- CURRENT MONTH : REASON ----------------
        cur.execute("""
            SELECT reason, SUM(qty) qty
            FROM (
                SELECT
                  CASE
                    WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                    WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                  END reason,
                  gmsm_qnty qty
                FROM db_sample_data
                WHERE to_char(gmsm_date,'YYYYMM') = to_char(current_date,'YYYYMM')
                  AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
            ) x
            GROUP BY reason
        """)
        month_reason = dictfetchall(cur)

        # ---------------- CURRENT MONTH : MANAGER ----------------
        cur.execute("""
            SELECT manager_name, SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE to_char(gmsm_date,'YYYYMM') = to_char(current_date,'YYYYMM')
            GROUP BY manager_name
            ORDER BY manager_name
        """)
        month_manager = dictfetchall(cur)

        # ---------------- CURRENT MONTH : CATEGORY ----------------
        cur.execute("""
            SELECT
              CASE
                WHEN munit IN ('FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG')
                THEN munit ELSE 'OTHERS'
              END category,
              SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE to_char(gmsm_date,'YYYYMM') = to_char(current_date,'YYYYMM')
            GROUP BY category
            ORDER BY category
        """)
        month_category = dictfetchall(cur)

    # ---------- MANAGER & CATEGORY CALCULATIONS ----------
    for row in prev_day_manager:
        row["amount"] = round(row["qty"] * rate)
        row["per"] = round((row["qty"] / prev_day_total) * 100, 2) if prev_day_total else 0

    for row in prev_day_category:
        row["amount"] = round(row["qty"] * rate)
        row["per"] = round((row["qty"] / prev_day_total) * 100, 2) if prev_day_total else 0

    for row in month_manager:
        row["amount"] = round(row["qty"] * rate)
        row["per"] = round((row["qty"] / month_total) * 100, 2) if month_total else 0

    for row in month_category:
        row["amount"] = round(row["qty"] * rate)
        row["per"] = round((row["qty"] / month_total) * 100, 2) if month_total else 0

    return {
        "rate": rate,
        "prev_day_total": prev_day_total,
        "month_total": month_total,
        "prev_day_reason": prev_day_reason,
        "prev_day_manager": prev_day_manager,
        "prev_day_category": prev_day_category,
        "month_reason": month_reason,
        "month_manager": month_manager,
        "month_category": month_category,
    }
