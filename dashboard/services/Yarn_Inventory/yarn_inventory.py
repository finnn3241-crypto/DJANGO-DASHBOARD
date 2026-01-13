from django.db import connection
from dashboard.utils.formatters import short_number


# =========================
# KPI SECTION
# =========================

def get_yarn_inventory_kpis():
    with connection.cursor() as cursor:

        cursor.execute("SELECT COALESCE(SUM(BALLBS),0) FROM YRN_ASON_TAB_WITH_VALUE")
        bal_lbs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COALESCE(SUM(BAL),0) FROM YRN_ASON_TAB_WITH_VALUE")
        bags = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COALESCE(SUM(AMT),0) FROM YRN_ASON_TAB_WITH_VALUE")
        amount = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE COALESCE(FOR_SALE,'N')='N'
        """)
        fresh = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE COALESCE(FOR_SALE,'Y')='Y'
        """)
        saleable = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT 
                COALESCE(SUM(B2R_LBS),0),
                COALESCE(SUM(B2R_AMOUNT),0)
            FROM YRN_PUR_TAB
            WHERE COALESCE(B2R_LBS,0) > 0
              AND COALESCE(FLAG,'N')='N'
              AND COALESCE(STATUS,'O')='O'
        """)
        b2r_lbs, b2r_amount = cursor.fetchone()

    return {
        "kpi_lbs": round(bal_lbs),
        "kpi_bags": round(bags),
        "kpi_amount": short_number(amount),
        "kpi_fresh": round(fresh),
        "kpi_saleable": round(saleable),
        "kpi_b2r_lbs": round(b2r_lbs),
        "kpi_b2r_amount": short_number(b2r_amount),
    }


# =========================
# AGING + FRESH SECTION
# =========================

def color_rule(pct):
    if pct >= 90: return "#4caf50"
    if pct >= 70: return "#2196f3"
    if pct >= 30: return "#ff9510"
    if pct > 0:  return "#e91e63"
    return "#999999"

def fmt_int(val):
    return f"{int(round(val)):,}"

def get_fresh_inventory_data():
    with connection.cursor() as cursor:

        cursor.execute("SELECT COALESCE(SUM(BALLBS),0) FROM YRN_ASON_TAB_WITH_VALUE")
        total_lbs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE AGE='0-6 Month'
        """)
        age_lbs = cursor.fetchone()[0] or 0

        stores = {
            "main": "DENIM YARN STORE",
            "rnd": "R & D YARN STORE",
            "loose": "DENIM LOOSE YARN STORE",
            "overhead": "OVERHEAD YARN STORE",
            "splice": "DENIM YARN SPLICER STORE",
        }

        results = {}

        for key, store in stores.items():
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'N')='N' THEN BALLBS ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'Y')='Y' THEN BALLBS ELSE 0 END),0)
                FROM YRN_ASON_TAB_WITH_VALUE
                WHERE STORE_DESC=%s AND AGE='0-6 Month'
            """, [store])

            fresh, sale = cursor.fetchone()

            pct_fresh = round((fresh / age_lbs) * 100, 2) if age_lbs else 0
            pct_sale  = round((sale  / age_lbs) * 100, 2) if age_lbs else 0

            results[key] = {
                "fresh": fmt_int(fresh),
                "sale": fmt_int(sale),
                "pct_fresh": pct_fresh,
                "pct_sale": pct_sale,
                "color_fresh": color_rule(pct_fresh),
                "color_sale": color_rule(pct_sale),
            }

    overall_pct = round((age_lbs / total_lbs) * 100, 1) if total_lbs else 0

    return {
        "total_lbs": round(total_lbs),
        "age_lbs": round(age_lbs),
        "overall_pct": overall_pct,
        "balance_lbs": round(total_lbs - age_lbs),
        "stores": results
    }





#############



def get_aging_6_12_data():
    with connection.cursor() as cursor:

        cursor.execute("SELECT COALESCE(SUM(BALLBS),0) FROM YRN_ASON_TAB_WITH_VALUE")
        total_lbs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE AGE='6 Month - 1 Year'
        """)
        age_lbs = cursor.fetchone()[0] or 0

        stores = {
            "main": "DENIM YARN STORE",
            "rnd": "R & D YARN STORE",
            "loose": "DENIM LOOSE YARN STORE",
            "overhead": "OVERHEAD YARN STORE",
            "splice": "DENIM YARN SPLICER STORE",
        }

        results = {}

        for key, store in stores.items():
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'N')='N' THEN BALLBS ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'Y')='Y' THEN BALLBS ELSE 0 END),0)
                FROM YRN_ASON_TAB_WITH_VALUE
                WHERE STORE_DESC=%s AND AGE='6 Month - 1 Year'
            """, [store])

            fresh, sale = cursor.fetchone()

            pct_fresh = round((fresh / age_lbs) * 100, 2) if age_lbs else 0
            pct_sale  = round((sale  / age_lbs) * 100, 2) if age_lbs else 0

            results[key] = {
                "fresh": fmt_int(fresh),
                "sale": fmt_int(sale),
                "pct_fresh": pct_fresh,
                "pct_sale": pct_sale,
                "color_fresh": color_rule(pct_fresh),
                "color_sale": color_rule(pct_sale),
            }

    overall_pct = round((age_lbs / total_lbs) * 100, 1) if total_lbs else 0

    return {
        "total_lbs": round(total_lbs),
        "age_lbs": round(age_lbs),
        "overall_pct": overall_pct,
        "balance_lbs": round(total_lbs - age_lbs),
        "stores": results
    }


##########

def get_aging_1_2_data():
    with connection.cursor() as cursor:

        cursor.execute("SELECT COALESCE(SUM(BALLBS),0) FROM YRN_ASON_TAB_WITH_VALUE")
        total_lbs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE AGE='1-2 Years'
        """)
        age_lbs = cursor.fetchone()[0] or 0

        stores = {
            "main": "DENIM YARN STORE",
            "rnd": "R & D YARN STORE",
            "loose": "DENIM LOOSE YARN STORE",
            "overhead": "OVERHEAD YARN STORE",
            "splice": "DENIM YARN SPLICER STORE",
        }

        results = {}

        for key, store in stores.items():
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'N')='N' THEN BALLBS ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'Y')='Y' THEN BALLBS ELSE 0 END),0)
                FROM YRN_ASON_TAB_WITH_VALUE
                WHERE STORE_DESC=%s AND AGE='1-2 Years'
            """, [store])

            fresh, sale = cursor.fetchone()

            pct_fresh = round((fresh / age_lbs) * 100, 2) if age_lbs else 0
            pct_sale  = round((sale  / age_lbs) * 100, 2) if age_lbs else 0

            results[key] = {
                "fresh": fmt_int(fresh),
                "sale": fmt_int(sale),
                "pct_fresh": pct_fresh,
                "pct_sale": pct_sale,
                "color_fresh": color_rule(pct_fresh),
                "color_sale": color_rule(pct_sale),
            }

    overall_pct = round((age_lbs / total_lbs) * 100, 1) if total_lbs else 0

    return {
        "total_lbs": round(total_lbs),
        "age_lbs": round(age_lbs),
        "overall_pct": overall_pct,
        "balance_lbs": round(total_lbs - age_lbs),
        "stores": results
    }




##########

def get_aging_2_data():
    with connection.cursor() as cursor:

        cursor.execute("SELECT COALESCE(SUM(BALLBS),0) FROM YRN_ASON_TAB_WITH_VALUE")
        total_lbs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(BALLBS),0)
            FROM YRN_ASON_TAB_WITH_VALUE
            WHERE AGE='2+ Years'
        """)
        age_lbs = cursor.fetchone()[0] or 0

        stores = {
            "main": "DENIM YARN STORE",
            "rnd": "R & D YARN STORE",
            "loose": "DENIM LOOSE YARN STORE",
            "overhead": "OVERHEAD YARN STORE",
            "splice": "DENIM YARN SPLICER STORE",
        }

        results = {}

        for key, store in stores.items():
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'N')='N' THEN BALLBS ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN COALESCE(FOR_SALE,'Y')='Y' THEN BALLBS ELSE 0 END),0)
                FROM YRN_ASON_TAB_WITH_VALUE
                WHERE STORE_DESC=%s AND AGE='2+ Years'
            """, [store])

            fresh, sale = cursor.fetchone()

            pct_fresh = round((fresh / age_lbs) * 100, 2) if age_lbs else 0
            pct_sale  = round((sale  / age_lbs) * 100, 2) if age_lbs else 0

            results[key] = {
                "fresh": fmt_int(fresh),
                "sale": fmt_int(sale),
                "pct_fresh": pct_fresh,
                "pct_sale": pct_sale,
                "color_fresh": color_rule(pct_fresh),
                "color_sale": color_rule(pct_sale),
            }

    overall_pct = round((age_lbs / total_lbs) * 100, 1) if total_lbs else 0

    return {
        "total_lbs": round(total_lbs),
        "age_lbs": round(age_lbs),
        "overall_pct": overall_pct,
        "balance_lbs": round(total_lbs - age_lbs),
        "stores": results
    }


