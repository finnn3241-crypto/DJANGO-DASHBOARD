from django.db import connection
from datetime import date

def fetchall_dict(cur):
    cols = [c[0].lower() for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


from django.db import connection
from datetime import date

def fetchall_dict(cur):
    cols = [c[0].lower() for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def machine_dashboard_data(ins_date):

    data = {}

    with connection.cursor() as cur:

        # ---- total month dispatch ----
        cur.execute("""
            SELECT COALESCE(SUM(mtr),0)
            FROM db_ins_data
            WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
        """)
        curr_month_dispatch = cur.fetchone()[0]
        data["curr_month_dispatch"] = curr_month_dispatch

        # ---- machines ----
        cur.execute("""
            SELECT DISTINCT machine_no
            FROM db_ins_data
            WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
            ORDER BY machine_no
        """)
        machines = [r[0] for r in cur.fetchall()]

        machine_list = []

        for machine in machines:

            cur.execute("""
                SELECT
                    COUNT(DISTINCT inspector_name) AS inspector_count,
                    COUNT(DISTINCT lot_no) AS lot_count,
                    SUM(mtr) AS mtr,
                    SUM(CASE WHEN rep_date = %s THEN mtr ELSE 0 END) AS prev_mtr
                FROM db_ins_data
                WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                  AND machine_no = %s
            """, [ins_date, machine])

            g = fetchall_dict(cur)[0]

            total_mtr = g["mtr"] or 0

            machine_percent = round((total_mtr / curr_month_dispatch) * 100, 1) \
                              if curr_month_dispatch else 0

            machine_rec = {
                "machine_no": machine,
                "inspector_count": g["inspector_count"],
                "lot_count": g["lot_count"],
                "mtr": total_mtr,
                "prev_mtr": g["prev_mtr"],
                "percent": machine_percent,
                "grade": [],
                "shift": []
            }

            # ---- grade wise ----
            cur.execute("""
                SELECT grade, SUM(mtr) AS mtr
                FROM db_ins_data
                WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                  AND machine_no = %s
                GROUP BY grade
                ORDER BY grade
            """, [machine])

            grade_rows = fetchall_dict(cur)
            for r in grade_rows:
                r["percent"] = round((r["mtr"] / total_mtr) * 100, 1) if total_mtr else 0
            machine_rec["grade"] = grade_rows

            # ---- shift wise ----
            cur.execute("""
                SELECT shift, SUM(mtr) AS mtr
                FROM db_ins_data
                WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
                  AND machine_no = %s
                GROUP BY shift
                ORDER BY mtr DESC
            """, [machine])

            shift_rows = fetchall_dict(cur)
            for r in shift_rows:
                r["percent"] = round((r["mtr"] / total_mtr) * 100, 1) if total_mtr else 0
            machine_rec["shift"] = shift_rows

            machine_list.append(machine_rec)

        data["machines"] = machine_list


        # ===============================
        # ===== Chart.js Data ===========
        # ===============================
        cur.execute("""
            SELECT machine_no, SUM(mtr) AS mtr
            FROM db_ins_data
            WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
            GROUP BY machine_no
            ORDER BY mtr DESC
        """)

        chart_rows = fetchall_dict(cur)

        data["chart_labels"] = [str(r["machine_no"]) for r in chart_rows]
        data["chart_values"] = [float(r["mtr"]) for r in chart_rows]

    return data

