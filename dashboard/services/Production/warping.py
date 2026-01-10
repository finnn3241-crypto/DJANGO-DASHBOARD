from django.db import connection
from datetime import datetime

def get_warping_data(request):
    # 1. Get the date from request or default to today
    target_date_str = request.GET.get('p3100_wrp_date')
    if not target_date_str:
        target_date_str = datetime.now().strftime('%d-%m-%Y')
    
    with connection.cursor() as cursor:
        # 2. Previous Day Values
        # Using COALESCE ensures we show 0 instead of None if no data is found
        query_prev = """
            SELECT 
                COALESCE(ROUND(SUM(OLD_WRPING) * 79.3 / 100), 0) as old_prev,
                COALESCE(ROUND(SUM(NEW_WRPING) * 79.3 / 100), 0) as new_prev
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') = TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_prev, [target_date_str])
        row_prev = cursor.fetchone()
        v_old_prev = float(row_prev[0])
        v_new_prev = float(row_prev[1])
        v_tot_prev = v_old_prev + v_new_prev

        # 3. Current Month Values (Cumulative)
        query_month = """
            SELECT 
                COALESCE(ROUND(SUM(OLD_WRPING) * 79.3 / 100), 0) as old_curr,
                COALESCE(ROUND(SUM(NEW_WRPING) * 79.3 / 100), 0) as new_curr
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND TO_DATE(MONTHNO, 'DD-MM-YYYY') 
                  BETWEEN DATE_TRUNC('month', TO_DATE(%s, 'DD-MM-YYYY')) 
                  AND TO_DATE(%s, 'DD-MM-YYYY')
        """
        cursor.execute(query_month, [target_date_str, target_date_str])
        row_month = cursor.fetchone()
        v_old_curr = float(row_month[0])
        v_new_curr = float(row_month[1])
        v_tot_curr = v_old_curr + v_new_curr

        # 4. Days Calculation for Projection
        query_days = """
            SELECT 
                EXTRACT(DAY FROM (DATE_TRUNC('month', TO_DATE(%s, 'DD-MM-YYYY')) + INTERVAL '1 month - 1 day'))::int,
                EXTRACT(DAY FROM TO_DATE(%s, 'DD-MM-YYYY'))::int
        """
        cursor.execute(query_days, [target_date_str, target_date_str])
        row_days = cursor.fetchone()
        v_month_days = float(row_days[0])
        # Use (days elapsed - 1) to match production logic; default to 1 to prevent division by zero
        v_prod_days = float(row_days[1] - 1) if row_days[1] > 1 else 1.0

    # 5. Projections and Progress
    v_old_proj = round((v_old_curr / v_prod_days) * v_month_days)
    v_new_proj = round((v_new_curr / v_prod_days) * v_month_days)
    v_tot_proj = round((v_tot_curr / v_prod_days) * v_month_days)

    def calc_prog(curr, proj):
        return round((curr / proj * 100), 2) if proj > 0 else 0

    # 6. Return Data mapped to your HTML variables
    return {
        'old': {
            'prev': v_old_prev, 
            'curr': v_old_curr, 
            'proj': v_old_proj, 
            'prog': calc_prog(v_old_curr, v_old_proj)
        },
        'new': {
            'prev': v_new_prev, 
            'curr': v_new_curr, 
            'proj': v_new_proj, 
            'prog': calc_prog(v_new_curr, v_new_proj)
        },
        'tot': {
            'prev': v_tot_prev, 
            'curr': v_tot_curr, 
            'proj': v_tot_proj, 
            'prog': calc_prog(v_tot_curr, v_tot_proj)
        }
    }