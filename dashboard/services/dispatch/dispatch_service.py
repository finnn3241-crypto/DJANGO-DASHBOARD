from django.db import connection
from datetime import date, timedelta
from calendar import monthrange

def get_dispatch_data():
    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    yesterday = today - timedelta(days=1)

    with connection.cursor() as cursor:

        # 1️⃣ Current Month Dispatch
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE exp_loc='EXPORT'
              AND disp_min_date::date BETWEEN %s AND %s
        """, [first_day, today])
        curr_dispatch = cursor.fetchone()[0]

        # 2️⃣ Balance Plan for Current Month
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN t.exp_loc='EXPORT'
                     THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0)
                     ELSE 0 END),0)
            FROM rpt_fabord_status_el t
            JOIN lc_ord_del_det_reschd r
              ON t.order_seqno = r.order_seqno
             AND t.serial_number = r.serial_number
            WHERE r.req_date BETWEEN %s AND %s
              AND COALESCE(r.req_qty,0) > 0
              AND (COALESCE(t.ord_meter_mtr,0) - COALESCE(t.ship_qty_mtr,0)) > 0
        """, [first_day, last_day])
        balance_plan = cursor.fetchone()[0]

        # 3️⃣ Previous Day Dispatch
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE exp_loc='EXPORT'
              AND disp_min_date::date = %s
        """, [yesterday])
        prev_day_dispatch = cursor.fetchone()[0]

    # 4️⃣ Calculations
    total_plan = curr_dispatch + balance_plan
    percentage = round((curr_dispatch / total_plan) * 100, 1) if total_plan else 0

    days_passed = today.day
    days_in_month = last_day.day

    curr_day_plan = round(total_plan / days_in_month) if days_in_month else 0
    target_till_date = round((total_plan / days_in_month) * days_passed) if days_in_month else 0

    behind_percent = round(100 - (curr_dispatch / target_till_date * 100)) if target_till_date else 0
    expected_dispatch = round((curr_dispatch / days_passed) * days_in_month) if days_passed else 0

    # 5️⃣ Manager-wise Dispatch (Verified SQL)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COALESCE(p.manager_name, d.manager_name) AS manager_name,
                COALESCE(p.exp_mtr, 0) + COALESCE(d.exp_qty, 0) AS total_exp,
                COALESCE(d.exp_qty, 0) AS dispatch_exp
            FROM (
                SELECT
                    t.manager_name,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.exp_loc = 'EXPORT'
                                THEN COALESCE(r.req_qty, 0) - COALESCE(r.ship_qty, 0)
                                ELSE 0
                            END
                        ), 0
                    ) AS exp_mtr
                FROM rpt_fabord_status_el t
                JOIN lc_ord_del_det_reschd r
                  ON t.order_seqno = r.order_seqno
                 AND t.serial_number = r.serial_number
                WHERE COALESCE(r.req_qty, 0) > 0
                  AND r.req_date BETWEEN %s AND %s
                  AND (COALESCE(t.ord_meter_mtr, 0) - COALESCE(t.ship_qty_mtr, 0)) > 0
                GROUP BY t.manager_name
            ) p
            FULL OUTER JOIN (
                SELECT
                    manager_name,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN exp_loc = 'EXPORT'
                                THEN qty_mtr
                                ELSE 0
                            END
                        ), 0
                    ) AS exp_qty
                FROM fab_disp_gmsm
                WHERE disp_min_date::date BETWEEN %s AND %s
                GROUP BY manager_name
            ) d
              ON p.manager_name = d.manager_name
            ORDER BY COALESCE(p.manager_name, d.manager_name);
        """, [first_day, last_day, first_day, today])

        manager_rows = cursor.fetchall()

    managers = []
    for name, total, dispatch in manager_rows:
        percent = round((dispatch / total) * 100, 1) if total else 0

        if percent >= 90:
            color = '#2ecc71'
        elif percent >= 70:
            color = '#f1c40f'
        elif percent > 0:
            color = '#e67e22'
        else:
            color = '#bdc3c7'

        managers.append({
            "name": name,
            "total": total,
            "dispatch": dispatch,
            "percent": percent,
            "color": color,
        })

    return {
        "curr_dispatch":curr_dispatch,
        "balance_plan": balance_plan,
        "total_plan": total_plan,
        "percentage": percentage,
        "prev_day_dispatch": prev_day_dispatch,
        "curr_day_plan": curr_day_plan,
        "target_till_date": target_till_date,
        "behind_percent": behind_percent,
        "expected_dispatch": expected_dispatch,
        "managers": managers,
    }
