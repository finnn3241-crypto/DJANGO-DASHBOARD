from django.db import connection
from datetime import datetime

def get_weaving_data(request):
    target_date_str = request.GET.get('p3100_wft_date')
    if not target_date_str:
        target_date_str = datetime.now().strftime('%d-%m-%Y')

    with connection.cursor() as cursor:
        # 1. Previous Day Data (Shed 1, Shed 2 & Total)
        # PL/SQL logic ke mutabiq coefficients apply kiye hain (0.88 aur 0.86)
        query_prev = """
            SELECT 
                ROUND(SHED1 * 0.88) as shed1,
                ROUND(SHED2 * 0.86) as shed2,
                SHED1_LCT, INZ_AVG_RPM_S1, INZ_AVG_EFF_S1, INZ_AVG_PRD_S1, SHED1_APICK,
                SHED2_LCT, INZ_AVG_RPM_S2, INZ_AVG_EFF_S2, INZ_AVG_PRD_S2, SHED2_APICK,
                -- Standard Calculations
                ROUND((INZ_AVG_RPM_S1 * 1440 * INZ_AVG_EFF_S1 / NULLIF(SHED1_APICK, 0) / 39.37) * SHED1_LCT * 0.88) as std1,
                ROUND((INZ_AVG_RPM_S2 * 1440 * INZ_AVG_EFF_S2 / NULLIF(SHED2_APICK, 0) / 39.37) * SHED2_LCT * 0.88) as std2
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') = TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_prev, [target_date_str])
        row = cursor.fetchone()

        if not row:
            return {'weaving_sections': []} # No data found

        # Mapping data to variables
        v_shed1 = float(row[0] or 0)
        v_shed2 = float(row[1] or 0)
        v_std1 = float(row[11] or 0)
        v_std2 = float(row[12] or 0)

        # 2. Current Month Cumulative
        query_month = """
            SELECT 
                ROUND(SUM(SHED1) * 0.88),
                ROUND(SUM(SHED2) * 0.86)
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') 
                  BETWEEN DATE_TRUNC('month', TO_DATE(%s, 'DD-MM-YYYY')) 
                  AND TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_month, [target_date_str, target_date_str])
        m_row = cursor.fetchone()
        v_curr1 = float(m_row[0] or 0)
        v_curr2 = float(m_row[1] or 0)

        # 3. Days for Projection
        query_days = """
            SELECT 
                EXTRACT(DAY FROM (DATE_TRUNC('month', TO_DATE(%s, 'DD-MM-YYYY')) + INTERVAL '1 month - 1 day'))::int,
                EXTRACT(DAY FROM TO_DATE(%s, 'DD-MM-YYYY'))::int
        """
        cursor.execute(query_days, [target_date_str, target_date_str])
        d_row = cursor.fetchone()
        v_m_days = d_row[0]
        v_p_days = (d_row[1] - 1) if d_row[1] > 1 else 1

    # Projection Calculation
    def get_proj(curr):
        return round((curr / v_p_days) * v_m_days)

    def get_prog(curr, proj):
        return round((curr / proj * 100), 2) if proj > 0 else 0

    proj1 = get_proj(v_curr1)
    proj2 = get_proj(v_curr2)

    # Final Data Structure for HTML Loop
    return {
        'weaving_sections': [
            {
                'title': 'SHED 1',
                'prev': v_shed1, 'std': v_std1, 'diff': v_shed1 - v_std1,
                'looms': row[2], 'rpm': round(row[3] or 0), 'eff': row[4],
                'prod_eff': row[5], 'pick': row[6],
                'curr_month': v_curr1, 'proj_month': proj1, 'prog': get_prog(v_curr1, proj1)
            },
            {
                'title': 'SHED 2',
                'prev': v_shed2, 'std': v_std2, 'diff': v_shed2 - v_std2,
                'looms': row[7], 'rpm': round(row[8] or 0), 'eff': row[9],
                'prod_eff': row[10], 'pick': row[11],
                'curr_month': v_curr2, 'proj_month': proj2, 'prog': get_prog(v_curr2, proj2)
            },
            {
                'title': 'TOTAL SHED',
                'prev': v_shed1 + v_shed2, 
                'std': v_std1 + v_std2, 
                'diff': (v_shed1 + v_shed2) - (v_std1 + v_std2),
                'looms': (row[2] or 0) + (row[7] or 0),
                'rpm': round(((row[3] or 0) + (row[8] or 0)) / 2),
                'eff': round(((row[4] or 0) + (row[9] or 0)) / 2),
                'prod_eff': round(((row[5] or 0) + (row[10] or 0)) / 2),
                'pick': round(((row[6] or 0) + (row[11] or 0)) / 2),
                'curr_month': v_curr1 + v_curr2, 
                'proj_month': proj1 + proj2, 
                'prog': get_prog(v_curr1 + v_curr2, proj1 + proj2)
            }
        ]
    }