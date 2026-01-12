from django.db import connection

def fetchall(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

def top20_data():

    with connection.cursor() as cur:

        # -------- RATE --------
        cur.execute("""
            SELECT COALESCE(ROUND(SUM(pkr_amt)/NULLIF(SUM(wt),0)),0)
            FROM gl_postage
            WHERE to_char(vdate,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
        """)
        rate = cur.fetchone()[0]

        # -------- TOTALS --------
        cur.execute("""
            SELECT COALESCE(SUM(gmsm_qnty),0)
            FROM db_sample_data
            WHERE to_char(gmsm_date,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
            AND cust_rank <= 20
        """)
        month_total = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(gmsm_qnty),0)
            FROM db_sample_data
            WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
            AND cust_rank <= 20
        """)
        prev_day_total = cur.fetchone()[0]

        # -------- PREVIOUS DAY : REASON --------
        cur.execute("""
            SELECT reason, SUM(qty) qty FROM (
                SELECT
                    CASE
                        WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                        WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                    END reason,
                    gmsm_qnty qty
                FROM db_sample_data
                WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
                AND cust_rank <= 20
                AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
            ) x GROUP BY reason
        """)
        prev_reason = fetchall(cur)

        # -------- CURRENT MONTH : REASON --------
        cur.execute("""
            SELECT reason, SUM(qty) qty FROM (
                SELECT
                    CASE
                        WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                        WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                    END reason,
                    gmsm_qnty qty
                FROM db_sample_data
                WHERE to_char(gmsm_date,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
                AND cust_rank <= 20
                AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
            ) x GROUP BY reason
        """)
        curr_reason = fetchall(cur)

        # -------- PREVIOUS DAY : CUSTOMER --------
        cur.execute("""
            SELECT customer, SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
            AND cust_rank <= 20
            GROUP BY customer
            ORDER BY customer
        """)
        prev_customer = fetchall(cur)

        # -------- CURRENT MONTH : CUSTOMER --------
        cur.execute("""
            SELECT customer, SUM(gmsm_qnty) qty
            FROM db_sample_data
            WHERE to_char(gmsm_date,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
            AND cust_rank <= 20
            GROUP BY customer
            ORDER BY customer
        """)
        curr_customer = fetchall(cur)

        # -------- PREVIOUS DAY : CATEGORY --------
        cur.execute("""
            SELECT category, SUM(qty) qty FROM (
                SELECT
                    CASE
                        WHEN munit IN ('FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG')
                        THEN munit ELSE 'OTHERS'
                    END category,
                    gmsm_qnty qty
                FROM db_sample_data
                WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
                AND cust_rank <= 20
            ) x
            GROUP BY category
            ORDER BY category
        """)
        category_prev = fetchall(cur)

        # -------- ARTICLE / COLOR --------
        cur.execute("""
            SELECT customer, style_color, COUNT(DISTINCT gmsm_code) cnt
            FROM (
                SELECT customer, style || ' (' || color || ')' style_color, gmsm_code
                FROM db_sample_data
                WHERE to_char(gmsm_date,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
                AND cust_rank <= 20
            ) x
            GROUP BY customer, style_color
            HAVING COUNT(DISTINCT gmsm_code) > 1
            ORDER BY customer, style_color
        """)
        article_color = fetchall(cur)

        # -------- CATEGORY WISE : CURRENT MONTH --------
        cur.execute("""
            SELECT category, SUM(qty) qty FROM (
                SELECT
                    CASE
                        WHEN munit IN ('FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG')
                        THEN munit ELSE 'OTHERS'
                    END category,
                    gmsm_qnty qty
                FROM db_sample_data
                WHERE to_char(gmsm_date,'YYYYMM') = to_char(CURRENT_DATE,'YYYYMM')
                AND cust_rank <= 20
            ) x
            GROUP BY category
            ORDER BY category
        """)
        category_month = fetchall(cur)

    # -------- CALCULATIONS --------
    for r in prev_reason:
        r["per"] = round((r["qty"] / prev_day_total) * 100, 1) if prev_day_total else 0
        r["amount"] = round(r["qty"] * rate)

    for r in curr_reason:
        r["per"] = round((r["qty"] / month_total) * 100, 1) if month_total else 0
        r["amount"] = round(r["qty"] * rate)

    for c in prev_customer:
        c["per"] = round((c["qty"] / prev_day_total) * 100, 2) if prev_day_total else 0
        c["amount"] = round(c["qty"] * rate)

    for c in curr_customer:
        c["per"] = round((c["qty"] / month_total) * 100, 2) if month_total else 0
        c["amount"] = round(c["qty"] * rate)

    for c in category_prev:
        c["per"] = round((c["qty"] / prev_day_total) * 100, 2) if prev_day_total else 0
        c["amount"] = round(c["qty"] * rate)

    for c in category_month:
        c["per"] = round((c["qty"] / month_total) * 100, 2) if month_total else 0
        c["amount"] = round(c["qty"] * rate)

    return {
        "rate": rate,
        "month_total": month_total,
        "prev_day_total": prev_day_total,
        "prev_reason": prev_reason,
        "curr_reason": curr_reason,
        "prev_customer": prev_customer,
        "curr_customer": curr_customer,
        "category_prev": category_prev,
        "article_color": article_color,
        "category_month": category_month,
    }
