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


def order_in_hand_exp():

    with connection.cursor() as cur:

        # ---------- BTD / DAYS / FIN ----------
        cur.execute("""
            SELECT
                COALESCE(SUM(setlen),0),
                ROUND(SUM(setlen) / NULLIF(MAX(base_mtr),0) * 26),
                COALESCE(SUM(setlen),0) - COALESCE(ROUND(SUM(setlen)*0.24),0)
            FROM db_monthly_schedule_dyeing
            WHERE UPPER(ORD_TYPE) = 'EXPORT';
        """)
        btd, days, fin = cur.fetchone() or (0, 0, 0)

        # ---------- INVENTORY (matches APEX) ----------
        cur.execute("""
        WITH base AS (
            SELECT  
                a.cust_seqno,
                a.ord_type,
                SUM(CASE WHEN system_remarks24rpt='FRESH_A_O' THEN a.meter END) ason_meter,
                SUM(CASE WHEN system_remarks24rpt='FRESH_A_C' THEN a.meter END) mkt_close_po_o,
                SUM(CASE WHEN system_remarks24rpt='STOCK_FRSH' THEN a.meter END) fresh_meter,
                SUM(CASE WHEN system_remarks24rpt IN ('STOCK_FRSH','STOCK_OTHERS')
                         AND system_remarks<>'SOLD OUT' THEN a.meter END) net_stock
            FROM rpt_fabric_db_v2_po a
            WHERE a.cust_seqno IS NOT NULL
            GROUP BY a.cust_seqno, a.ord_type
        ),
        ason AS (
            SELECT
                cust_seqno,
                CASE ord_type WHEN 'E' THEN 'EXPORT' WHEN 'L' THEN 'LOCAL' END ord_type,
                SUM(CASE WHEN ord_type='E'
                    THEN COALESCE(ason_meter,0)+COALESCE(mkt_close_po_o,0)+COALESCE(fresh_meter,0)+COALESCE(net_stock,0)
                    ELSE 0 END) exp
            FROM base
            GROUP BY cust_seqno, ord_type
        ),
        oih AS (
            SELECT cust_seqno, exp_loc,
                   ROUND(COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0)) oih_meter
            FROM rpt_fabord_status_el
            GROUP BY cust_seqno, exp_loc
        )
        SELECT COALESCE(SUM(exp),0)
        FROM ason a
        JOIN oih b 
          ON a.cust_seqno::TEXT = b.cust_seqno::TEXT
         AND a.ord_type = b.exp_loc
        """)
        inventory = int(cur.fetchone()[0] or 0)

        # ---------- TODAY RATE ----------
        cur.execute("SELECT get_today_rate()")
        d_rate = Decimal(cur.fetchone()[0])

        # ---------- TOTAL PLAN ----------
        cur.execute("""
            SELECT COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0)
            FROM rpt_fabord_status_el
        """)
        total_plan = int(cur.fetchone()[0] or 0)

        # ---------- EXPORT DISPATCH ----------
        cur.execute("""
            SELECT
                COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0),
                ROUND((COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0))*AVG(rate_in_mtr)),
                ROUND((COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0))*AVG(rate_in_mtr)*%s)
            FROM rpt_fabord_status_el
            WHERE exp_loc='EXPORT'
        """, [d_rate])
        curr_dispatch, amt, amt_pkr = cur.fetchone()

    # ---------- APEX rounding ----------
    curr_dispatch = int(curr_dispatch or 0)
    amt = int(amt or 0)
    amt_pkr = int(amt_pkr or 0)

    percentage = round((curr_dispatch / total_plan) * 100, 1) if total_plan else 0
    inv_per = round((inventory / curr_dispatch) * 100) if curr_dispatch else 0
    avg_rate = round(amt / curr_dispatch, 2) if curr_dispatch else 0

    # ---------- MANAGER WISE ----------
    with connection.cursor() as cur:
        cur.execute("""
            SELECT manager_name,
                   COALESCE(SUM(ord_meter_mtr),0)-COALESCE(SUM(ship_qty_mtr),0) dispatch_exp
            FROM rpt_fabord_status_el
            WHERE exp_loc='EXPORT'
            GROUP BY manager_name
            ORDER BY manager_name
        """)
        managers = []
        for name, val in cur.fetchall():
            val = int(val or 0)
            managers.append({
                "manager_name": name or "BLANK",
                "dispatch_exp": fmt_int(val),
                "per": round((val / curr_dispatch) * 100, 1) if curr_dispatch else 0
            })

    return {
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


