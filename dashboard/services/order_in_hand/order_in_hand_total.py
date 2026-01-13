from django.db import connection
from decimal import Decimal


def fmt_int(val):
    return f"{int(round(val)):,}"


def fmt_short(val):
    val = float(val)
    if val >= 1_000_000:
        return f"{round(val/1_000_000)}M"
    elif val >= 1_000:
        return f"{round(val/1_000)}K"
    return str(int(val))


def order_in_hand_total():

    with connection.cursor() as cur:

        # ---------- BTD / DAYS ----------
        cur.execute("""
            SELECT
                COALESCE(SUM(setlen),0),
                ROUND(SUM(setlen) / NULLIF(MAX(base_mtr),0) * 26)
            FROM db_monthly_schedule_dyeing
        """)
        btd, days = cur.fetchone() or (0, 0)

        # ---------- INVENTORY ----------
        cur.execute("""
        WITH base AS (
            SELECT  
                a.cust_seqno,
                a.ord_type,
                SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_O'  THEN a.meter END) AS ason_meter,
                SUM(CASE WHEN system_remarks24rpt = 'FRESH_A_C'  THEN a.meter END) AS mkt_close_po_o,
                SUM(CASE WHEN system_remarks24rpt = 'STOCK_FRSH' THEN a.meter END) AS fresh_meter,
                SUM(CASE 
                        WHEN system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS') 
                         AND system_remarks <> 'SOLD OUT'
                        THEN a.meter END) AS net_stock
            FROM rpt_fabric_db_v2_po a
            WHERE a.cust_seqno IS NOT NULL
            GROUP BY a.cust_seqno, a.ord_type
        ),
        ASON AS (
            SELECT
                cust_seqno,
                SUM(COALESCE(ason_meter,0)+COALESCE(mkt_close_po_o,0)+COALESCE(fresh_meter,0)+COALESCE(net_stock,0)) AS tot
            FROM base
            GROUP BY cust_seqno
        ),
        OIH AS (
            SELECT cust_seqno,
                   ROUND(COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0)) AS oih_meter
            FROM rpt_fabord_status_el
            GROUP BY cust_seqno
        )
        SELECT COALESCE(SUM(A.tot),0)
        FROM ASON A
        JOIN OIH B ON CAST(A.cust_seqno AS TEXT) = CAST(B.cust_seqno AS TEXT)
        """)
        inventory = int(cur.fetchone()[0] or 0)

        # ---------- TODAY RATE ----------
        cur.execute("SELECT get_today_rate()")
        d_rate = Decimal(cur.fetchone()[0])

        # ---------- TOTAL PLAN ----------
        cur.execute("""
            SELECT COALESCE(SUM(ord_meter_mtr),0) - COALESCE(SUM(ship_qty_mtr),0)
            FROM rpt_fabord_status_el
        """)
        total_plan = int(cur.fetchone()[0])

        # ---------- CURRENT DISPATCH ----------
        cur.execute("""
                SELECT
        COALESCE(SUM(ord_meter_mtr), 0) - COALESCE(SUM(ship_qty_mtr), 0),
        SUM(
            CASE 
                WHEN exp_loc = 'LOCAL' THEN
                    ROUND( (COALESCE(ord_meter_mtr, 0) - COALESCE(ship_qty_mtr, 0)) * rate_in_mtr / get_today_rate() )
                ELSE
                    ROUND( (COALESCE(ord_meter_mtr, 0) - COALESCE(ship_qty_mtr, 0)) * rate_in_mtr )
            END
        ),
        SUM(
            CASE 
                WHEN exp_loc = 'LOCAL' THEN
                    ROUND( (COALESCE(ord_meter_mtr, 0) - COALESCE(ship_qty_mtr, 0)) * rate_in_mtr )
                ELSE
                    ROUND( (COALESCE(ord_meter_mtr, 0) - COALESCE(ship_qty_mtr, 0)) * rate_in_mtr * get_today_rate() )
            END
        )
    FROM rpt_fabord_status_el
        """, [d_rate])

        curr_dispatch, amt, amt_pkr = cur.fetchone()

    curr_dispatch = int(curr_dispatch)
    amt = int(amt)
    amt_pkr = int(amt_pkr)

    percentage = round((curr_dispatch / total_plan) * 100, 1) if total_plan else 0
    inv_per = round((inventory / curr_dispatch) * 100) if curr_dispatch else 0
    avg_rate = round(amt_pkr / curr_dispatch, 2) if curr_dispatch else 0

    # ---------- MANAGER WISE (MATCHES APEX) ----------

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                manager_name,
                SUM(dispatch_exp) AS dispatch_exp
            FROM
            (
                -- Actual data
                SELECT
                    COALESCE(manager_name, 'BLANK') AS manager_name,
                    COALESCE(SUM(ord_meter_mtr), 0) - COALESCE(SUM(ship_qty_mtr), 0) AS dispatch_exp
                FROM rpt_fabord_status_el
                GROUP BY COALESCE(manager_name, 'BLANK')

                UNION ALL

                -- Zero rows to force all managers to appear
                SELECT DISTINCT
                    COALESCE(manager_name, 'BLANK') AS manager_name,
                    0::NUMERIC AS dispatch_exp
                FROM rpt_fabord_status_el
            ) t
            GROUP BY manager_name
            ORDER BY manager_name;
        """)

        rows = cur.fetchall()

    managers = []

    curr_dispatch = curr_dispatch or 0  # safety

    for name, val in rows:
        val = int(val or 0)

        managers.append({
            "manager_name": name,
            "dispatch_exp": fmt_int(val),
            "per": round((val / curr_dispatch) * 100, 1) if curr_dispatch else 0
        })


    return {
        "title": "TOTAL",
        "curr_dispatch": fmt_int(curr_dispatch),
        "total_plan": fmt_int(total_plan),
        "percentage": percentage,
        "amt": fmt_short(amt),
        "amt_pkr": fmt_short(amt_pkr),
        "avg_rate": avg_rate,
        "btd": fmt_int(btd),
        "days": int(round(days)),
        "inventory": fmt_int(inventory),
        "inv_per": inv_per,
        "d_rate": int(round(d_rate)),
        "managers": managers
    }
