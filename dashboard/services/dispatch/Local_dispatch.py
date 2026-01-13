from django.db import connection
from datetime import date, timedelta
from calendar import monthrange


def get_dispatch_data_L():

    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    yesterday = today - timedelta(days=1)

    with connection.cursor() as cursor:

        # 1️⃣ Current Month Dispatch (LOCAL)
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE exp_loc = 'LOCAL'
              AND disp_min_date::date BETWEEN %s AND %s
        """, [first_day, today])
        curr_dispatch_L = cursor.fetchone()[0]

        # 2️⃣ Full Month LOCAL Plan (Corrected window)
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN t.exp_loc = 'LOCAL'
                    THEN COALESCE(r.req_qty,0) - COALESCE(r.ship_qty,0)
                    ELSE 0
                END
            ),0)
            FROM rpt_fabord_status_el t
            JOIN lc_ord_del_det_reschd r
              ON t.order_seqno = r.order_seqno
             AND t.serial_number = r.serial_number
            WHERE r.req_date BETWEEN %s AND %s
              AND COALESCE(r.req_qty,0) > 0
              AND (COALESCE(t.ord_meter_mtr,0) - COALESCE(t.ship_qty_mtr,0)) > 0
        """, [first_day, last_day])
        balance_plan_L = cursor.fetchone()[0]

        # 3️⃣ Previous Day Dispatch
        cursor.execute("""
            SELECT COALESCE(SUM(qty_mtr),0)
            FROM fab_disp_gmsm
            WHERE exp_loc = 'LOCAL'
              AND disp_min_date::date = %s
        """, [yesterday])
        prev_day_dispatch_L = cursor.fetchone()[0]

    # 4️⃣ Calculations
    total_plan_L = curr_dispatch_L + balance_plan_L
    percentage_L = round((curr_dispatch_L / total_plan_L) * 100, 1) if total_plan_L else 0

    days_passed = today.day
    days_in_month = last_day.day

    curr_day_plan_L = round(total_plan_L / days_in_month) if days_in_month else 0
    target_till_date_L = round((total_plan_L / days_in_month) * days_passed) if days_in_month else 0

    if target_till_date_L:
        behind_percent_L = round(100 - (curr_dispatch_L / target_till_date_L * 100))
        behind_percent_L = max(0, min(100, behind_percent_L))
    else:
        behind_percent_L = 0

    expected_dispatch_L = round((curr_dispatch_L / days_passed) * days_in_month) if days_passed else 0

    # 5️⃣ Manager-wise Dispatch (Corrected to match PL/SQL exactly)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COALESCE(p.manager_name, d.manager_name) AS manager_name,
                COALESCE(p.loc_mtr, 0) + COALESCE(d.loc_qty, 0) AS total_exp,
                COALESCE(d.loc_qty, 0) AS dispatch_exp
            FROM (
                SELECT
                    t.manager_name,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.exp_loc = 'LOCAL'
                                THEN COALESCE(r.req_qty, 0) - COALESCE(r.ship_qty, 0)
                                ELSE 0
                            END
                        ), 0
                    ) AS loc_mtr
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
                                WHEN exp_loc = 'LOCAL'
                                THEN qty_mtr
                                ELSE 0
                            END
                        ), 0
                    ) AS loc_qty
                FROM fab_disp_gmsm
                WHERE disp_min_date::date BETWEEN %s AND %s
                GROUP BY manager_name
            ) d
              ON p.manager_name = d.manager_name
            ORDER BY COALESCE(p.manager_name, d.manager_name);
        """, [first_day, last_day, first_day, today])

        manager_rows = cursor.fetchall()

    managers_L = []
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

        managers_L.append({
            "name": name,
            "total": total,
            "dispatch": dispatch,
            "percent": percent,
            "color": color,
        })

    return {
        "curr_dispatch_L": curr_dispatch_L,
        "balance_plan_L": balance_plan_L,
        "total_plan_L": total_plan_L,
        "percentage_L": percentage_L,
        "prev_day_dispatch_L": prev_day_dispatch_L,
        "curr_day_plan_L": curr_day_plan_L,
        "target_till_date_L": target_till_date_L,
        "behind_percent_L": behind_percent_L,
        "expected_dispatch_L": expected_dispatch_L,
        "managers_L": managers_L,
    }
