from django.db import connection

UNITS = ['FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG','OTHERS']

def fetchall(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

def unit_dashboard_data():

    with connection.cursor() as cur:

        # ---------- RATE ----------
        cur.execute("""
            SELECT COALESCE(ROUND(SUM(pkr_amt)/NULLIF(SUM(wt),0)),0)
            FROM gl_postage
            WHERE vdate BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
        """)
        rate = cur.fetchone()[0]

        # ---------- OVERALL MONTH TOTAL ----------
        cur.execute("""
            SELECT COALESCE(SUM(gmsm_qnty),0)
            FROM db_sample_data
            WHERE gmsm_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
        """)
        overall_month = cur.fetchone()[0]

        result = []

        for unit in UNITS:

            if unit == "OTHERS":
                unit_where = "munit NOT IN ('FABRIC','HEADERS','PANT','NEW HANGER','HALF LEG')"
                params = []
            else:
                unit_where = "munit = %s"
                params = [unit]

            # ---------- TOTALS ----------
            cur.execute(f"""
                SELECT COALESCE(SUM(gmsm_qnty),0)
                FROM db_sample_data
                WHERE {unit_where}
                AND gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
            """, params)
            prev_total = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COALESCE(SUM(gmsm_qnty),0)
                FROM db_sample_data
                WHERE {unit_where}
                AND gmsm_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
            """, params)
            curr_total = cur.fetchone()[0]

            percent_overall = round((curr_total / overall_month) * 100, 1) if overall_month else 0
            balance = overall_month - curr_total

            # ---------- WEIGHT → PKR ----------
            cur.execute(f"""
                SELECT COALESCE(SUM(parcel_wt),0)
                FROM (
                    SELECT DISTINCT gmsm_code, parcel_wt
                    FROM db_sample_data
                    WHERE parcel_wt > 0
                    AND gmsm_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                    AND {unit_where}
                ) x
            """, params)
            amount = round(cur.fetchone()[0] * rate)

            # ---------- PREVIOUS DAY : REASON ----------
            cur.execute(f"""
                SELECT reason, SUM(qty) qty FROM (
                    SELECT
                        CASE
                            WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                            WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                        END reason,
                        gmsm_qnty qty
                    FROM db_sample_data
                    WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
                    AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
                    AND {unit_where}
                ) x GROUP BY reason
            """, params)
            prev_reason = fetchall(cur)

            # ---------- PREVIOUS DAY : MANAGER ----------
            cur.execute(f"""
                SELECT manager_name, SUM(gmsm_qnty) qty
                FROM db_sample_data
                WHERE gmsm_date = (SELECT MAX(gmsm_date) FROM db_sample_data)
                AND {unit_where}
                GROUP BY manager_name
                ORDER BY manager_name
            """, params)
            prev_manager = fetchall(cur)

            # ---------- CURRENT MONTH : REASON ----------
            cur.execute(f"""
                SELECT reason, SUM(qty) qty FROM (
                    SELECT
                        CASE
                            WHEN reason IN ('F.O.C.','ADJUST IN DISPATCH') THEN 'A.I.D/F.O.C'
                            WHEN reason = 'INVOICE ON DELIVERY' THEN 'I.O.D'
                        END reason,
                        gmsm_qnty qty
                    FROM db_sample_data
                    WHERE gmsm_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                    AND reason IN ('F.O.C.','ADJUST IN DISPATCH','INVOICE ON DELIVERY')
                    AND {unit_where}
                ) x GROUP BY reason
            """, params)
            curr_reason = fetchall(cur)

            # ---------- CURRENT MONTH : MANAGER ----------
            cur.execute(f"""
                SELECT manager_name, SUM(gmsm_qnty) qty
                FROM db_sample_data
                WHERE gmsm_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                AND {unit_where}
                GROUP BY manager_name
                ORDER BY manager_name
            """, params)
            curr_manager = fetchall(cur)

            result.append({
                "unit": unit,
                "prev_total": prev_total,
                "curr_total": curr_total,
                "overall": overall_month,
                "percent": percent_overall,
                "balance": balance,
                "amount": amount,
                "rate": rate,
                "prev_reason": prev_reason,
                "prev_manager": prev_manager,
                "curr_reason": curr_reason,
                "curr_manager": curr_manager
            })

    # ---------- PERCENT CALCULATIONS ----------
    for u in result:
        for r in u["prev_reason"]:
            r["per"] = round((r["qty"] / u["prev_total"]) * 100, 2) if u["prev_total"] else 0
        for m in u["prev_manager"]:
            m["per"] = round((m["qty"] / u["prev_total"]) * 100, 2) if u["prev_total"] else 0
        for r in u["curr_reason"]:
            r["per"] = round((r["qty"] / u["curr_total"]) * 100, 2) if u["curr_total"] else 0
        for m in u["curr_manager"]:
            m["per"] = round((m["qty"] / u["curr_total"]) * 100, 2) if u["curr_total"] else 0

    return result
