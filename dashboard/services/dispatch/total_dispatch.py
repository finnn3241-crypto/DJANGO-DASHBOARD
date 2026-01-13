from django.db import connection
from datetime import date, timedelta
from calendar import monthrange


def get_dispatch_data_tot():

    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    yesterday = today - timedelta(days=1)

    with connection.cursor() as cursor:

        # 1️⃣ Current Month TOTAL Dispatch
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE disp_min_date::date BETWEEN %s AND %s
        """, [first_day, today])
        curr_dispatch = cursor.fetchone()[0]

        # 2️⃣ Current Month TOTAL Plan (EXPORT + LOCAL)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(exp_mtr),0) + COALESCE(SUM(loc_mtr),0)
            FROM (
                SELECT 
                    CASE WHEN t.exp_loc = 'EXPORT' THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0) ELSE 0 END AS exp_mtr,
                    CASE WHEN t.exp_loc = 'LOCAL'  THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0) ELSE 0 END AS loc_mtr
                FROM rpt_fabord_status_el t
                JOIN lc_ord_del_det_reschd r
                  ON t.order_seqno = r.order_seqno
                 AND t.serial_number = r.serial_number
                WHERE COALESCE(r.req_qty,0) > 0
                  AND r.req_date BETWEEN %s AND %s
                  AND (COALESCE(t.ord_meter_mtr,0) - COALESCE(t.ship_qty_mtr,0)) > 0
            ) x
        """, [first_day, last_day])
        balance_plan = cursor.fetchone()[0]

        # 3️⃣ Previous Day Dispatch
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE disp_min_date::date = %s
        """, [yesterday])
        prev_day_dispatch = cursor.fetchone()[0]

    # 4️⃣ Calculations
    total_plan = curr_dispatch + balance_plan
    percentage = round((curr_dispatch / total_plan) * 100, 1) if total_plan else 0

    days_passed = today.day
    days_in_month = last_day.day

    curr_day_plan = round(total_plan / days_in_month) if days_in_month else 0
    target_till_date = round((total_plan / days_in_month) * days_passed) if days_in_month else 0

    if target_till_date:
        behind_percent = round(100 - (curr_dispatch / target_till_date * 100))
        behind_percent = max(0, min(100, behind_percent))
    else:
        behind_percent = 0

    expected_dispatch = round((curr_dispatch / days_passed) * days_in_month) if days_passed else 0

    # 5️⃣ Manager-wise TOTAL Dispatch + TOTAL Plan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COALESCE(p.manager_name, d.manager_name) AS manager_name,
                COALESCE(p.loc_mtr,0) + COALESCE(d.loc_qty,0)
              + COALESCE(p.exp_mtr,0) + COALESCE(d.exp_qty,0) AS total_plan,
                COALESCE(d.loc_qty,0) + COALESCE(d.exp_qty,0) AS total_dispatch
            FROM (
                SELECT
                    t.manager_name,
                    COALESCE(SUM(CASE WHEN t.exp_loc = 'EXPORT' THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0) ELSE 0 END),0) AS exp_mtr,
                    COALESCE(SUM(CASE WHEN t.exp_loc = 'LOCAL'  THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0) ELSE 0 END),0) AS loc_mtr
                FROM rpt_fabord_status_el t
                JOIN lc_ord_del_det_reschd r
                  ON t.order_seqno = r.order_seqno
                 AND t.serial_number = r.serial_number
                WHERE COALESCE(r.req_qty,0) > 0
                  AND r.req_date BETWEEN %s AND %s
                  AND (COALESCE(t.ord_meter_mtr,0) - COALESCE(t.ship_qty_mtr,0)) > 0
                GROUP BY t.manager_name
            ) p
            FULL OUTER JOIN (
                SELECT
                    manager_name,
                    COALESCE(SUM(CASE WHEN exp_loc = 'EXPORT' THEN qty_mtr ELSE 0 END),0) AS exp_qty,
                    COALESCE(SUM(CASE WHEN exp_loc = 'LOCAL'  THEN qty_mtr ELSE 0 END),0) AS loc_qty
                FROM fab_disp_gmsm
                WHERE disp_min_date::date BETWEEN %s AND %s
                GROUP BY manager_name
            ) d
              ON p.manager_name = d.manager_name
            ORDER BY COALESCE(p.manager_name, d.manager_name)
        """, [first_day, last_day, first_day, today])

        manager_rows = cursor.fetchall()

    managers = []
    for name, total_plan_mtr, total_dispatch_mtr in manager_rows:
        percent = round((total_dispatch_mtr / total_plan_mtr) * 100, 1) if total_plan_mtr else 0

        if percent >= 90:
            color = '#ddd60a'
        elif percent >= 70:
            color = '#ddd60a'
        elif percent > 0:
            color = '#ddd60a'
        else:
            color = '#999'

        managers.append({
            "name": name,
            "total": total_plan_mtr,
            "dispatch": total_dispatch_mtr,
            "percent": percent,
            "color": color,
        })

    return {
        "curr_dispatch_tot": curr_dispatch,
        "balance_plan_tot": balance_plan,
        "total_plan_tot": total_plan,
        "percentage_tot": percentage,
        "prev_day_dispatch_tot": prev_day_dispatch,
        "curr_day_plan_tot": curr_day_plan,
        "target_till_date_tot": target_till_date,
        "behind_percent_tot": behind_percent,
        "expected_dispatch_tot": expected_dispatch,
        "managers_tot": managers,
    }
