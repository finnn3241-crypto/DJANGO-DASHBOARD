from django.db import connection

def get_export_dispatch_kpis():
    with connection.cursor() as cur:

        # 1. BTD / DAYS / FIN  (MATCHES ORACLE)
        cur.execute("""
            SELECT
                COALESCE(SUM(setlen), 0),
                COALESCE(ROUND(SUM(setlen) / NULLIF(MAX(base_mtr), 0) * 26), 0),
                COALESCE(SUM(setlen), 0) - COALESCE(ROUND(SUM(setlen) * 0.24), 0)
            FROM db_monthly_schedule_dyeing
            WHERE UPPER(ord_type) = 'EXPORT';
        """)
        v_btd, v_day, v_fin = cur.fetchone()

        # 2. TODAY RATE
        cur.execute("SELECT get_today_rate();")
        v_d_rate = cur.fetchone()[0] or 281

        # 3. TOTAL PLAN  (MATCHES ORACLE)
        cur.execute("""
            SELECT COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)
            FROM rpt_fabord_status_el;
        """)
        v_total_plan = cur.fetchone()[0]

        # 4. CURRENT EXPORT DISPATCH + AMOUNTS  (MATCHES ORACLE)
        cur.execute("""
            SELECT
                COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0),
                ROUND((COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)) * AVG(rate_in_mtr)),
                ROUND((COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)) * AVG(rate_in_mtr) * %s)
            FROM rpt_fabord_status_el
            WHERE exp_loc = 'EXPORT';
        """, [v_d_rate])
        v_curr_dispatch, v_amt, v_amt_pkr = cur.fetchone()

        # 5. INVENTORY MATCH  (EXACT ORACLE TRANSLATION)
        cur.execute("""
            WITH ason AS (
                SELECT 
                    cust_seqno,
                    CASE ord_type WHEN 'E' THEN 'EXPORT' WHEN 'L' THEN 'LOCAL' END AS ord_type,
                    SUM(CASE WHEN ord_type = 'E'
                             THEN COALESCE(ason_meter,0) + COALESCE(mkt_close_po_o,0)
                                + COALESCE(fresh_meter,0) + COALESCE(net_stock,0)
                             ELSE 0 END) AS exp
                FROM (
                    SELECT
                        a.cust_seqno,
                        a.ord_type,
                        SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_O' THEN a.meter END) AS ason_meter,
                        SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_C' THEN a.meter END) AS mkt_close_po_o,
                        SUM(CASE WHEN system_remarks24rpt = 'STOCK_FRSH' THEN a.meter END) AS fresh_meter,
                        SUM(CASE WHEN system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
                                 AND system_remarks <> 'SOLD OUT' THEN a.meter END) AS net_stock
                    FROM rpt_fabric_db_v2_po a
                    WHERE a.cust_seqno IS NOT NULL
                    GROUP BY a.cust_seqno, a.ord_type
                ) x
                GROUP BY cust_seqno, ord_type
            ),
            oih AS (
                SELECT
                    cust_seqno,
                    exp_loc,
                    ROUND(COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)) AS oih_meter
                FROM rpt_fabord_status_el
                WHERE ROUND(COALESCE(ord_meter_mtr,0) - COALESCE(ship_qty_mtr,0)) <> 0
                GROUP BY cust_seqno, exp_loc
            )
            SELECT COALESCE(SUM(exp),0)
            FROM ason a
            JOIN oih b
            ON a.cust_seqno = b.cust_seqno::text
            AND a.ord_type  = b.exp_loc;

        """)
        v_inv = cur.fetchone()[0]

        # 6. MANAGER WISE DISPATCH  (MATCHES ORACLE)
        cur.execute("""
            SELECT COALESCE(manager_name,'BLANK'),
                   COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)
            FROM rpt_fabord_status_el
            WHERE exp_loc = 'EXPORT'
            GROUP BY manager_name
            ORDER BY manager_name;
        """)
        manager_rows = cur.fetchall()

    # FINAL METRICS (MATCHES PL/SQL)
    pct = round((v_curr_dispatch / v_total_plan) * 100, 1) if v_total_plan else 0
    avg_rate = round(v_amt / v_curr_dispatch, 2) if v_curr_dispatch else 0
    inv_pct = round((v_inv / v_curr_dispatch) * 100) if v_curr_dispatch else 0

    return {
        "dispatch": {
            "current": int(v_curr_dispatch),
            "total_plan": int(v_total_plan),
            "percentage": pct,
            "amount": int(v_amt),
            "amount_pkr": int(v_amt_pkr),
            "rate": avg_rate,
            "btd": int(v_btd),
            "days": int(v_day),
            "fin": int(v_fin),
            "inventory": int(v_inv),
            "inventory_pct": inv_pct,
            "today_rate": v_d_rate
        },
        "manager_dispatch": [
            {
                "manager": m,
                "value": int(v),
                "pct": round(v / v_curr_dispatch * 100, 1) if v_curr_dispatch else 0
            }
            for m, v in manager_rows
        ]
    }
