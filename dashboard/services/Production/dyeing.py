from django.db import connection

def get_dyeing_data(request):
    target_date = request.GET.get('date', '22-10-2025') 
    
    with connection.cursor() as cursor:
        # 1. Previous Day Data (Added LENGTH check to avoid "07-2025" rows)
        query_prev = """
            SELECT 
                ROUND(SUM(OLD_DYEING) * 79.3 / 100),
                ROUND(SUM(NEW_DYEING) * 79.3 / 100)
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 7
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') = TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_prev, [target_date])
        row_prev = cursor.fetchone()
        v_old_prev = row_prev[0] or 0
        v_new_prev = row_prev[1] or 0

        # 2. Current Month Data (Added LENGTH check here too)
        query_month = """
            SELECT 
                ROUND(SUM(OLD_DYEING) * 79.3 / 100),
                ROUND(SUM(NEW_DYEING) * 79.3 / 100),
                ROUND(AVG(OLD_DYEING_SPD)), 
                ROUND(AVG(NEW_DYEING_SPD))
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 7
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') BETWEEN date_trunc('month', TO_DATE(%s, 'DD-MM-YYYY')) 
              AND TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_month, [target_date, target_date])
        row_month = cursor.fetchone()
        v_old_curr = row_month[0] or 0
        v_new_curr = row_month[1] or 0
        v_old_speed = row_month[2] or 0
        v_new_speed = row_month[3] or 0

        # 3. Projection Days
        cursor.execute("""
            SELECT 
                extract(day from (date_trunc('month', TO_DATE(%s, 'DD-MM-YYYY')) + interval '1 month - 1 day')),
                extract(day from TO_DATE(%s, 'DD-MM-YYYY'))
        """, [target_date, target_date])
        row_days = cursor.fetchone()
        v_m_days = float(row_days[0])
        v_p_days = float(row_days[1]) if row_days[1] > 0 else 1

    # Logic for Totals/Projections
    v_old_proj = round((v_old_curr / v_p_days) * v_m_days)
    v_new_proj = round((v_new_curr / v_p_days) * v_m_days)
    v_tot_curr = v_old_curr + v_new_curr
    v_tot_proj = round((v_tot_curr / v_p_days) * v_m_days)

    return {
            'dyeing_sections': [
                {
                    'title': 'OLD DYEING',
                    'prev': v_old_prev,
                    'rows': [
                        {'label': 'Current Month', 'val': v_old_curr, 'unit': 'Mtr'},
                        {'label': 'Avg Dye Speed', 'val': v_old_speed, 'unit': ''},
                        {'label': 'Projected Month', 'val': v_old_proj, 'unit': 'Mtr'},
                    ],
                    'prog': round((v_old_curr / v_old_proj * 100), 2) if v_old_proj > 0 else 0
                },
                {
                    'title': 'NEW DYEING',
                    'prev': v_new_prev,
                    'rows': [
                        {'label': 'Current Month', 'val': v_new_curr, 'unit': 'Mtr'},
                        {'label': 'Avg Dye Speed', 'val': v_new_speed, 'unit': ''},
                        {'label': 'Projected Month', 'val': v_new_proj, 'unit': 'Mtr'},
                    ],
                    'prog': round((v_new_curr / v_new_proj * 100), 2) if v_new_proj > 0 else 0
                },
                {
                    'title': 'TOTAL DYEING',
                    'prev': v_old_prev + v_new_prev,
                    'rows': [
                        {'label': 'Current Month', 'val': v_tot_curr, 'unit': 'Mtr'},
                        {'label': 'Avg Dye Speed', 'val': round((v_old_speed + v_new_speed)/2), 'unit': ''},
                        {'label': 'Projected Month', 'val': v_tot_proj, 'unit': 'Mtr'},
                    ],
                    'prog': round((v_tot_curr / v_tot_proj * 100), 2) if v_tot_proj > 0 else 0
                }
            ]
        }