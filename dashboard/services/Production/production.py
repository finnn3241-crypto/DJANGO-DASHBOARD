from django.db import connection
from datetime import date

def fmt_int(val):
    return f"{int(round(val)):,}"


def fmt_short(val):
    val = float(val)
    if val >= 1_000_000:
        return f"{round(val/1_000_000)}M"
    elif val >= 1_000:
        return f"{round(val/1_000)}K"
    return str(int(val))


def warping_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
           SELECT
            ROUND((SUM(old_wrping)::numeric * 79.3) / 100),
            ROUND((SUM(new_wrping)::numeric * 79.3) / 100),
            COALESCE(ROUND((SUM(old_wrping)::numeric * 79.3) / 100), 0)
        + COALESCE(ROUND((SUM(new_wrping)::numeric * 79.3) / 100), 0)
        FROM rpt_mill_activity_v2_tab
        WHERE length(monthno) > 9
        AND (COALESCE(old_wrping,0) > 0 OR COALESCE(new_wrping,0) > 0)
        AND to_date(monthno,'DD-MM-YYYY') = (
                SELECT MAX(vdate)
                FROM rpt_mill_activity_v2_tab
                WHERE vdate IS NOT NULL
                AND (COALESCE(old_wrping,0) > 0 OR COALESCE(new_wrping,0) > 0)
        );
        """,)

        old_prev, new_prev, tot_prev = cur.fetchone()


        # ---------- CURRENT MONTH ----------
        cur.execute("""
        SELECT
            ROUND((SUM(old_wrping)::numeric * 79.3) / 100),
            ROUND((SUM(new_wrping)::numeric * 79.3) / 100),
            COALESCE(ROUND((SUM(old_wrping)::numeric * 79.3) / 100), 0)
        + COALESCE(ROUND((SUM(new_wrping)::numeric * 79.3) / 100), 0)
        FROM rpt_mill_activity_v2_tab
        WHERE length(monthno) > 9
        AND (COALESCE(old_wrping,0) > 0 OR COALESCE(new_wrping,0) > 0)
        AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
        AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);""",)

        old_cur, new_cur, tot_cur = cur.fetchone()  # ← Fixed: now unpacking 3 values

        old_cur = int(old_cur or 0)
        new_cur = int(new_cur or 0)
        tot_cur = int(tot_cur or 0)  # ← Also convert tot_cur to int
        # Remove: tot_cur = old_cur + new_cur


        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()


        # ---------- PROJECTIONS ----------
        old_proj = round((old_cur / prod_days) * month_days) if prod_days else 0
        new_proj = round((new_cur / prod_days) * month_days) if prod_days else 0
        tot_proj = round((tot_cur / prod_days) * month_days) if prod_days else 0


        # ---------- PROGRESS ----------
        old_prog = round((old_cur / old_proj) * 100, 2) if old_proj else 0
        new_prog = round((new_cur / new_proj) * 100, 2) if new_proj else 0
        tot_prog = round((tot_cur / tot_proj) * 100, 2) if tot_proj else 0


    # ---------- FORMAT OUTPUT ----------

    return {
        "title":"warp",
        "old_prev_day": fmt_int(old_prev or 0),
        "new_prev_day": fmt_int(new_prev or 0),
        "tot_prev_day": fmt_int(tot_prev or 0),

        "old_current_month": fmt_int(old_cur),
        "new_current_month": fmt_int(new_cur),
        "tot_current_month": fmt_int(tot_cur),

        "old_projected_month": fmt_int(old_proj),
        "new_projected_month": fmt_int(new_proj),
        "tot_projected_month": fmt_int(tot_proj),

        "old_progress": old_prog,
        "new_progress": new_prog,
        "tot_progress": tot_prog,
    }


def dyeing_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
           SELECT
                ROUND((SUM(OLD_DYEING)::numeric * 79.3) / 100) AS old_prev_day,
                ROUND((SUM(NEW_DYEING)::numeric * 79.3) / 100) AS new_prev_day,
                COALESCE(ROUND((SUM(OLD_DYEING)::numeric * 79.3) / 100), 0)
            + COALESCE(ROUND((SUM(NEW_DYEING)::numeric * 79.3) / 100), 0) AS tot_prev_day
            FROM rpt_mill_activity_v2_tab
            WHERE length(monthno) > 9
            AND (COALESCE(OLD_DYEING,0) > 0 OR COALESCE(NEW_DYEING,0) > 0)
            AND to_date(monthno,'DD-MM-YYYY') = (
                    SELECT MAX(vdate)
                    FROM rpt_mill_activity_v2_tab
                    WHERE vdate IS NOT NULL
                    AND COALESCE(OLD_DYEING,0) > 0
            );
        """,)

        old_prev, new_prev, tot_prev = cur.fetchone()


        # ---------- CURRENT MONTH ----------
        cur.execute("""
          SELECT
            ROUND((SUM(OLD_DYEING)::numeric * 79.3) / 100) ,
            ROUND((SUM(NEW_DYEING)::numeric * 79.3) / 100) ,
            COALESCE(ROUND((SUM(OLD_DYEING)::numeric * 79.3) / 100), 0)
        + COALESCE(ROUND((SUM(NEW_DYEING)::numeric * 79.3) / 100), 0) ,
        AVG(OLD_DYEING_SPD),
        AVG(NEW_DYEING_SPD),
        ROUND(AVG(COALESCE(OLD_DYEING_SPD,0)+COALESCE(NEW_DYEING_SPD,0))/2)
        FROM rpt_mill_activity_v2_tab
        WHERE length(monthno) > 9
        AND (COALESCE(OLD_DYEING,0) > 0 OR COALESCE(NEW_DYEING,0) > 0)
        AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
        AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);""",)

        old_cur, new_cur, tot_cur, old_avg, new_avg, tot_avg = cur.fetchone()    # ← Fixed: now unpacking 3 values

        old_cur = int(old_cur or 0)
        new_cur = int(new_cur or 0)
        tot_cur = int(tot_cur or 0)  
        old_avg = int(old_avg or 0)
        new_avg = int(new_avg or 0)
        tot_avg = int(tot_avg or 0) 

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()


        # ---------- PROJECTIONS ----------
        old_proj = round((old_cur / prod_days) * month_days) if prod_days else 0
        new_proj = round((new_cur / prod_days) * month_days) if prod_days else 0
        tot_proj = round((tot_cur / prod_days) * month_days) if prod_days else 0


        # ---------- PROGRESS ----------
        old_prog = round((old_cur / old_proj) * 100, 2) if old_proj else 0
        new_prog = round((new_cur / new_proj) * 100, 2) if new_proj else 0
        tot_prog = round((tot_cur / tot_proj) * 100, 2) if tot_proj else 0


    # ---------- FORMAT OUTPUT ----------

    return {
        "title":"dye",
        "old_prev_day": fmt_int(old_prev or 0),
        "new_prev_day": fmt_int(new_prev or 0),
        "tot_prev_day": fmt_int(tot_prev or 0),

        "old_current_month": fmt_int(old_cur),
        "new_current_month": fmt_int(new_cur),
        "tot_current_month": fmt_int(tot_cur),

        "old_avg": fmt_int(old_avg),
        "new_avg": fmt_int(new_avg),
        "tot_avg": fmt_int(tot_avg),

        "old_projected_month": fmt_int(old_proj),
        "new_projected_month": fmt_int(new_proj),
        "tot_projected_month": fmt_int(tot_proj),

        "old_progress": old_prog,
        "new_progress": new_prog,
        "tot_progress": tot_prog,
    }

def weaving_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            WITH latest_day AS (SELECT MAX(vdate) max_vdate 
            FROM rpt_mill_activity_v2_tab 
            WHERE vdate IS NOT NULL AND (shed1 > 0 OR shed2 > 0)),
            base AS (
            SELECT ROUND(shed1 * 0.88) shed1, ROUND(shed2 * 0.86) shed2,
            ROUND(((inz_avg_rpm_s1 * 1440 * inz_avg_eff_s1) / NULLIF(shed1_apick,0) / 39.37 * shed1_lct) * 0.0088) std_shed1,
            ROUND(((inz_avg_rpm_s2 * 1440 * inz_avg_eff_s2) / NULLIF(shed2_apick,0) / 39.37 * shed2_lct) * 0.0088) std_shed2,
            shed1_lct loom_count_shed1, shed2_lct loom_count_shed2,
            ROUND(inz_avg_rpm_s1) rpm_shed1, ROUND(inz_avg_rpm_s2) rpm_shed2,
            inz_avg_eff_s1 eff_shed1, inz_avg_eff_s2 eff_shed2,
            inz_avg_prd_s1 prod_eff_shed1, inz_avg_prd_s2 prod_eff_shed2,
            shed1_apick pick_shed1, shed2_apick pick_shed2
            FROM rpt_mill_activity_v2_tab r 
            JOIN latest_day d ON r.vdate = d.max_vdate 
            WHERE (shed1 > 0 OR shed2 > 0)
            )
            SELECT shed1, std_shed1, shed1-std_shed1 diff_shed1, loom_count_shed1, rpm_shed1, eff_shed1, prod_eff_shed1, pick_shed1,
            shed2, std_shed2, shed2-std_shed2 diff_shed2, loom_count_shed2, rpm_shed2, eff_shed2, prod_eff_shed2, pick_shed2,
            CASE WHEN shed1-std_shed1>0 THEN 'darkgreen' ELSE 'red' END diff_color1,
            CASE WHEN shed2-std_shed2>0 THEN 'darkgreen' ELSE 'red' END diff_color2,
            shed1+shed2 shed_t, std_shed1+std_shed2 std_shed_t, (shed1+shed2)-(std_shed1+std_shed2) diff_shed_t,
            loom_count_shed1+loom_count_shed2 loom_count_shed_t,
            ROUND((rpm_shed1+rpm_shed2)/2.0) rpm_shed_t, ROUND((eff_shed1+eff_shed2)/2.0) eff_shed_t,
            ROUND((prod_eff_shed1+prod_eff_shed2)/2.0) prod_eff_shed_t, ROUND((pick_shed1+pick_shed2)/2.0) pick_shed_t
            FROM base;""",)

        row = cur.fetchone()

        columns = [
            "shed1", "std_shed1", "diff_shed1", "loom_count_shed1",
            "rpm_shed1", "eff_shed1", "prod_eff_shed1", "pick_shed1",

            "shed2", "std_shed2", "diff_shed2", "loom_count_shed2",
            "rpm_shed2", "eff_shed2", "prod_eff_shed2", "pick_shed2",

            "diff_color1", "diff_color2",

            "shed_t", "std_shed_t", "diff_shed_t", "loom_count_shed_t",
            "rpm_shed_t", "eff_shed_t", "prod_eff_shed_t", "pick_shed_t"
        ]

        prev_data = dict(zip(columns, row))



        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
                ROUND((SUM(SHED1)::numeric * 88) / 100) AS old_current_month,
                ROUND((SUM(SHED2)::numeric * 86) / 100) AS new_current_month,
                COALESCE(ROUND((SUM(SHED1)::numeric * 88) / 100), 0)
            + COALESCE(ROUND((SUM(SHED2)::numeric * 86) / 100), 0) AS tot_current_month
            FROM rpt_mill_activity_v2_tab
            WHERE length(monthno) > 9
            AND (COALESCE(SHED1,0) > 0 OR COALESCE(SHED2,0) > 0)
            AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);""",)

        shed1_cur, shed2_cur, tot_shed_cur = cur.fetchone()    # ← Fixed: now unpacking 3 values

        shed1_cur = int(shed1_cur or 0)
        shed2_cur = int(shed2_cur or 0)
        tot_shed_cur = int(tot_shed_cur or 0)  

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)""")
        month_days, prod_days = cur.fetchone()


        # ---------- PROJECTIONS ----------
        shed1_proj = round((shed1_cur / prod_days) * month_days) if prod_days else 0
        shed2_proj = round((shed2_cur / prod_days) * month_days) if prod_days else 0
        tot_shed_proj = round((tot_shed_cur / prod_days) * month_days) if prod_days else 0


        # ---------- PROGRESS ----------
        shed1_prog = round((shed1_cur / shed1_proj) * 100, 2) if shed1_proj else 0
        shed2_prog = round((shed2_cur / shed2_proj) * 100, 2) if shed2_proj else 0
        tot_shed_prog = round((tot_shed_cur / tot_shed_proj) * 100, 2) if tot_shed_proj else 0


    # ---------- FORMAT OUTPUT ----------

    return {
        "title": "weaving",

        "shed1": fmt_int(prev_data.get("shed1", 0)),
        "std_shed1": fmt_int(prev_data.get("std_shed1", 0)),
        "diff_shed1": fmt_int(prev_data.get("diff_shed1", 0)),
        "loom_count_shed1": fmt_int(prev_data.get("loom_count_shed1", 0)),
        "rpm_shed1": fmt_int(prev_data.get("rpm_shed1", 0)),
        "eff_shed1": fmt_int(prev_data.get("eff_shed1", 0)),
        "prod_eff_shed1": fmt_int(prev_data.get("prod_eff_shed1", 0)),
        "pick_shed1": fmt_int(prev_data.get("pick_shed1", 0)),

        "shed2": fmt_int(prev_data.get("shed2", 0)),
        "std_shed2": fmt_int(prev_data.get("std_shed2", 0)),
        "diff_shed2": fmt_int(prev_data.get("diff_shed2", 0)),
        "loom_count_shed2": fmt_int(prev_data.get("loom_count_shed2", 0)),
        "rpm_shed2": fmt_int(prev_data.get("rpm_shed2", 0)),
        "eff_shed2": fmt_int(prev_data.get("eff_shed2", 0)),
        "prod_eff_shed2": fmt_int(prev_data.get("prod_eff_shed2", 0)),
        "pick_shed2": fmt_int(prev_data.get("pick_shed2", 0)),

        "diff_color1": prev_data.get("diff_color1", "red"),
        "diff_color2": prev_data.get("diff_color2", "red"),

        "shed_t": fmt_int(prev_data.get("shed_t", 0)),
        "std_shed_t": fmt_int(prev_data.get("std_shed_t", 0)),
        "diff_shed_t": fmt_int(prev_data.get("diff_shed_t", 0)),
        "loom_count_shed_t": fmt_int(prev_data.get("loom_count_shed_t", 0)),
        "rpm_shed_t": fmt_int(prev_data.get("rpm_shed_t", 0)),
        "eff_shed_t": fmt_int(prev_data.get("eff_shed_t", 0)),
        "prod_eff_shed_t": fmt_int(prev_data.get("prod_eff_shed_t", 0)),
        "pick_shed_t": fmt_int(prev_data.get("pick_shed_t", 0)),


        "shed1_current_month": fmt_int(shed1_cur),
        "shed2_current_month": fmt_int(shed2_cur),
        "tot_shed_current_month": fmt_int(tot_shed_cur),

        "shed1_projected_month": fmt_int(shed1_proj),
        "shed2_projected_month": fmt_int(shed2_proj),
        "tot_shed_projected_month": fmt_int(tot_shed_proj),

        "shed1_prog": shed1_prog,
        "shed2_prog": shed2_prog,
        "tot_shed_prog": tot_shed_prog,
    }

# SINIGING

def finishing_dashboard():
    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
                ROUND(SUM(OLD_SINGING)*88/100) AS OLD_SINGING,
                ROUND(SUM(NEW_SINGING)*88/100) AS NEW_SINGING,
                COALESCE(ROUND(SUM(OLD_SINGING)*88/100),0)
                    + COALESCE(ROUND(SUM(NEW_SINGING)*88/100),0) AS TOT_SINGING,
                ROUND(SUM(OLD_SINGING_RW)*88/100) AS OLD_SINGING_RW,
                ROUND(SUM(NEW_SINGING_RW)*88/100) AS NEW_SINGING_RW,
                COALESCE(ROUND(SUM(OLD_SINGING_RW)*88/100),0)
                    + COALESCE(ROUND(SUM(NEW_SINGING_RW)*88/100),0) AS TOT_SINGING_RW
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0)
              AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                    AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(OLD_SINGING,0) > 0)
              );
        """)

        old_prev, new_prev, tot_prev, old_prev_rw, new_prev_rw, tot_prev_rw = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
                ROUND(SUM(OLD_SINGING)*88/100),
                ROUND(SUM(NEW_SINGING)*88/100),
                COALESCE(ROUND(SUM(OLD_SINGING)*88/100),0)
                    + COALESCE(ROUND(SUM(NEW_SINGING)*88/100),0),
                ROUND(SUM(OLD_SINGING_RW)*88/100),
                ROUND(SUM(NEW_SINGING_RW)*88/100),
                COALESCE(ROUND(SUM(OLD_SINGING_RW)*88/100),0)
                    + COALESCE(ROUND(SUM(NEW_SINGING_RW)*88/100),0)
            FROM RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
              AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0)
              AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
              AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        old_cur, new_cur, tot_cur, old_rw_cur, new_rw_cur, tot_rw_cur = cur.fetchone()

        old_cur = int(old_cur or 0)
        new_cur = int(new_cur or 0)
        tot_cur = int(tot_cur or 0)
        old_rw_cur = int(old_rw_cur or 0)
        new_rw_cur = int(new_rw_cur or 0)
        tot_rw_cur = int(tot_rw_cur or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        singing_current_month = round(tot_cur + tot_rw_cur)
        sing_projected_mn = round((singing_current_month / prod_days) * month_days) if prod_days else 0
        tot_prog = round((singing_current_month / sing_projected_mn) * 100, 2) if sing_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "sing",
        "old_prev_day": fmt_int(old_prev or 0),
        "new_prev_day": fmt_int(new_prev or 0),
        "tot_prev_day": fmt_int(tot_prev or 0),
        "old_prev_day_rw": fmt_int(old_prev_rw or 0),
        "new_prev_day_rw": fmt_int(new_prev_rw or 0),
        "tot_prev_day_rw": fmt_int(tot_prev_rw or 0),

        "old_current_month": fmt_int(old_cur),
        "new_current_month": fmt_int(new_cur),
        "tot_current_month": fmt_int(tot_cur),
        "old_curr_day_rw": fmt_int(old_rw_cur or 0),
        "new_curr_day_rw": fmt_int(new_rw_cur or 0),
        "tot_curr_day_rw": fmt_int(tot_rw_cur or 0),

        "sing_projected_month": fmt_int(sing_projected_mn),

        "tot_progress": tot_prog,
    }


# WASHING

def washing_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
            ROUND(SUM(WASHING)*88/100) WASHING,
            ROUND(SUM(WASHING_RW)*88/100) WASHING_RW,
            COALESCE(ROUND(SUM(WASHING)*88/100),0) + COALESCE(ROUND(SUM(WASHING_RW)*88/100),0) TOT_WASHING
            FROM 
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(WASHING,0) > 0 OR COALESCE(WASHING_RW,0) > 0) 
            AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                    AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0) 
              );
        """)

        wash_prev , wash_rw_prev , total_wash = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
            ROUND(SUM(WASHING)*88/100) WASHING,
            ROUND(SUM(WASHING_RW)*88/100) WASHING_RW,
            COALESCE(ROUND(SUM(WASHING)*88/100),0) + COALESCE(ROUND(SUM(WASHING_RW)*88/100),0) TOT_WASHING
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(WASHING,0) > 0 OR COALESCE(WASHING_RW,0) > 0) 
              AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
              AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        wash_curr_mn , wash_rw_curr_mn , total_wash_curr_mn = cur.fetchone()

        wash_curr_mn = int(wash_curr_mn or 0)
        wash_rw_curr_mn = int(wash_rw_curr_mn or 0)
        total_wash_curr_mn = int(total_wash_curr_mn or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        wash_projected_mn = round((total_wash_curr_mn / prod_days) * month_days) if prod_days else 0
        tot_prog = round((total_wash_curr_mn / wash_projected_mn) * 100, 2) if wash_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "wash",
        "old_prev_day": fmt_int(wash_prev or 0),
        "wash_rw_prev": fmt_int(wash_rw_prev or 0),
        "tot_prev_day": fmt_int(total_wash or 0),

        "wash_curr_mn": fmt_int(wash_curr_mn),
        "wash_rw_curr_mn": fmt_int(wash_rw_curr_mn),
        "total_wash_curr_mn": fmt_int(total_wash_curr_mn),

        "wash_projected_mn": fmt_int(wash_projected_mn),

        "tot_progress": tot_prog,
    }

# MERCERIZE

def mercerize_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
            ROUND(SUM(MERCERIZE)*88/100) MERCERIZE,
            ROUND(SUM(MERCERIZE_RW)*88/100) MERCERIZE_RW,
            COALESCE(ROUND(SUM(MERCERIZE)*88/100),0) + COALESCE(ROUND(SUM(MERCERIZE_RW)*88/100),0) TOT_MERCERIZE
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(MERCERIZE,0) > 0 OR COALESCE(MERCERIZE_RW,0) > 0) 
            AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                   AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0) 
              );
        """)

        mercerz_prev , mercerz_rw_prev , total_mercerz = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
            ROUND(SUM(MERCERIZE)*88/100) MERCERIZE,
            ROUND(SUM(MERCERIZE_RW)*88/100) MERCERIZE_RW,
            COALESCE(ROUND(SUM(MERCERIZE)*88/100),0) + COALESCE(ROUND(SUM(MERCERIZE_RW)*88/100),0) TOT_MERCERIZE
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(MERCERIZE,0) > 0 OR COALESCE(MERCERIZE_RW,0) > 0) 
            AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        mercerz_curr_mn , mercerz_rw_curr_mn , total_mercerz_curr_mn  = cur.fetchone()

        mercerz_curr_mn = int(mercerz_curr_mn or 0)
        mercerz_rw_curr_mn = int(mercerz_rw_curr_mn or 0)
        total_mercerz_curr_mn = int(total_mercerz_curr_mn or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        mercz_projected_mn = round((total_mercerz_curr_mn / prod_days) * month_days) if prod_days else 0
        tot_prog = round((total_mercerz_curr_mn / mercz_projected_mn) * 100, 2) if mercz_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "mercerz",
        "prev": fmt_int(mercerz_prev or 0),
        "rw_prev": fmt_int(mercerz_rw_prev or 0),
        "total_mercerz": fmt_int(total_mercerz or 0),

        "curr_mn": fmt_int(mercerz_curr_mn),
        "rw_curr_mn": fmt_int(mercerz_rw_curr_mn),
        "total_mercerz_curr_mn": fmt_int(total_mercerz_curr_mn),

        "projected_mn": fmt_int(mercz_projected_mn),

        "tot_progress": tot_prog,
    }
    

#STENTER
def stenter_dashboard():

    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
            ROUND(SUM(STENTER)*88/100) STENTER,
            ROUND(SUM(STENTER_RW)*88/100) STENTER_RW,
            COALESCE(ROUND(SUM(STENTER)*88/100),0) + COALESCE(ROUND(SUM(STENTER_RW)*88/100),0) TOT_STENTER
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(STENTER,0) > 0 OR COALESCE(STENTER_RW,0) > 0) 
            AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                  AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0) 
              );
        """)

        stent_prev , stent_rw_prev , total_stent = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
            ROUND(SUM(STENTER)*88/100) STENTER,
            ROUND(SUM(STENTER_RW)*88/100) STENTER_RW,
            COALESCE(ROUND(SUM(STENTER)*88/100),0) + COALESCE(ROUND(SUM(STENTER_RW)*88/100),0) TOT_STENTER
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(STENTER,0) > 0 OR COALESCE(STENTER_RW,0) > 0) 
            AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        stent_curr_mn , stent_rw_curr_mn , total_stent_curr_mn  = cur.fetchone()

        stent_curr_mn = int(stent_curr_mn or 0)
        stent_rw_curr_mn = int(stent_rw_curr_mn or 0)
        total_stent_curr_mn = int(total_stent_curr_mn or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        stent_projected_mn = round((total_stent_curr_mn / prod_days) * month_days) if prod_days else 0
        tot_prog = round((total_stent_curr_mn / stent_projected_mn) * 100, 2) if stent_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "stent",
        "prev": fmt_int(stent_prev or 0),
        "rw_prev": fmt_int(stent_rw_prev or 0),
        "total_stent": fmt_int(total_stent or 0),

        "curr_mn": fmt_int(stent_curr_mn),
        "rw_curr_mn": fmt_int(stent_rw_curr_mn),
        "total_stent_curr_mn": fmt_int(total_stent_curr_mn),

        "projected_mn": fmt_int(stent_projected_mn),

        "tot_progress": tot_prog,
    }
    


#SANFORIZING


def sanfor_dashboard():
    with connection.cursor() as cur:

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
            ROUND(SUM(OLD_SANFORIZING)) OLD_SANFORIZING,
            ROUND(SUM(NEW_SANFORIZING)) NEW_SANFORIZING,
            COALESCE(ROUND(SUM(OLD_SANFORIZING)),0) + COALESCE(ROUND(SUM(NEW_SANFORIZING)),0) TOT_SANFORIZING,
            ROUND(SUM(OLD_SANFORIZING_RW)) OLD_SANFORIZING_RW,
            ROUND(SUM(NEW_SANFORIZING_RW)) NEW_SANFORIZING_RW,
            COALESCE(ROUND(SUM(OLD_SANFORIZING_RW)),0) + COALESCE(ROUND(SUM(NEW_SANFORIZING_RW)),0) TOT_SANFORIZING_RW
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(OLD_SANFORIZING,0) > 0 OR COALESCE(NEW_SANFORIZING,0) > 0) 
            AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                  AND (COALESCE(OLD_SINGING,0) > 0 OR COALESCE(NEW_SINGING,0) > 0) 
              );
        """)

        old_prev, new_prev, tot_prev, old_prev_rw, new_prev_rw, tot_prev_rw = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
            ROUND(SUM(OLD_SANFORIZING)) OLD_SANFORIZING,
            ROUND(SUM(NEW_SANFORIZING)) NEW_SANFORIZING,
            COALESCE(ROUND(SUM(OLD_SANFORIZING)),0) + COALESCE(ROUND(SUM(NEW_SANFORIZING)),0) TOT_SANFORIZING,
            ROUND(SUM(OLD_SANFORIZING_RW)) OLD_SANFORIZING_RW,
            ROUND(SUM(NEW_SANFORIZING_RW)) NEW_SANFORIZING_RW,
            COALESCE(ROUND(SUM(OLD_SANFORIZING_RW)),0) + COALESCE(ROUND(SUM(NEW_SANFORIZING_RW)),0) TOT_SANFORIZING_RW
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND (COALESCE(OLD_SANFORIZING,0) > 0 OR COALESCE(NEW_SANFORIZING,0) > 0) 
            AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        old_cur, new_cur, tot_cur, old_rw_cur, new_rw_cur, tot_rw_cur = cur.fetchone()

        old_cur = int(old_cur or 0)
        new_cur = int(new_cur or 0)
        tot_cur = int(tot_cur or 0)
        old_rw_cur = int(old_rw_cur or 0)
        new_rw_cur = int(new_rw_cur or 0)
        tot_rw_cur = int(tot_rw_cur or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        sanfor_current_month = round(tot_cur + tot_rw_cur)
        sanfor_projected_mn = round((sanfor_current_month / prod_days) * month_days) if prod_days else 0
        tot_prog = round((sanfor_current_month / sanfor_projected_mn) * 100, 2) if sanfor_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "sanfor",
        "old_prev_day": fmt_int(old_prev or 0),
        "new_prev_day": fmt_int(new_prev or 0),
        "tot_prev_day": fmt_int(tot_prev or 0),
        "old_prev_day_rw": fmt_int(old_prev_rw or 0),
        "new_prev_day_rw": fmt_int(new_prev_rw or 0),
        "tot_prev_day_rw": fmt_int(tot_prev_rw or 0),

        "old_current_month": fmt_int(old_cur),
        "new_current_month": fmt_int(new_cur),
        "tot_current_month": fmt_int(tot_cur),
        "old_curr_day_rw": fmt_int(old_rw_cur or 0),
        "new_curr_day_rw": fmt_int(new_rw_cur or 0),
        "tot_curr_day_rw": fmt_int(tot_rw_cur or 0),

        "sanfor_projected_mn": fmt_int(sanfor_projected_mn),

        "tot_progress": tot_prog,
    }


def inspection_dashboard():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(DISTINCT CASE
                    WHEN rep_date = (
                        SELECT MAX(vdate)
                        FROM rpt_mill_activity_v2_tab
                        WHERE vdate IS NOT NULL
                        AND COALESCE(total,0) > 0
                    )
                    THEN machine_no
                END) AS v_prev_mac,

                COUNT(DISTINCT machine_no) AS v_curr_mac
            FROM db_ins_data
            WHERE rep_date BETWEEN date_trunc('month', CURRENT_DATE)
                            AND (
                                SELECT MAX(vdate)
                                FROM rpt_mill_activity_v2_tab
                                WHERE vdate IS NOT NULL
                                    AND COALESCE(total,0) > 0
                            ); """)
        
        v_prev_mac , v_curr_mac = cur.fetchone()

        # ---------- PREVIOUS DAY ----------
        cur.execute("""
            SELECT
                ROUND(SUM(TOTAL)) INSPECTION,
                SUM(DIGITAL_MTR) DIGITAL_METER_INS,
                ROUND(PERCAL(SUM(DIGITAL_MTR),SUM(TOTAL),'e',NULL) * 100,2) AS DIGITAL_METER_INS_PER,
                ROUND(SUM(INS_REWASH))  INSPECTION_RW,
                SUM(A_GRADE) A_GRADE_PER,
                SUM(B_GRADE) B_GRADE_PER
                FROM
                RPT_MILL_ACTIVITY_V2_TAB
                WHERE LENGTH(MONTHNO) > 9
                AND COALESCE(TOTAL,0) > 0 
                AND TO_DATE(MONTHNO,'DD-MM-YYYY') = (
                  SELECT MAX(vdate)
                  FROM rpt_mill_activity_v2_tab
                  WHERE vdate IS NOT NULL
                    AND COALESCE(TOTAL,0) > 0 
              );
                
        """)

        insp_prev , dm_ins_prev , dm_per_prev , ins_rw_prev , a_grade_prev , b_grade_prev = cur.fetchone()

        # ---------- CURRENT MONTH ----------
        cur.execute("""
            SELECT
            ROUND(SUM(TOTAL)) INS,
            SUM(DIGITAL_MTR) DIGITAL_METER_INS,
            ROUND(PERCAL(SUM(DIGITAL_MTR),SUM(TOTAL),'e',NULL) * 100,2) AS DIGITAL_METER_INS_PER,
            ROUND(SUM(INS_REWASH)) INSPECTION_RW,
            ROUND(AVG(A_GRADE),2) A_GRADE_PER,
            ROUND(AVG(B_GRADE),2) B_GRADE_PER
            FROM
            RPT_MILL_ACTIVITY_V2_TAB
            WHERE LENGTH(MONTHNO) > 9
            AND COALESCE(TOTAL,0) > 0 
            AND EXTRACT(YEAR FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM to_date(monthno,'DD-MM-YYYY')) = EXTRACT(MONTH FROM CURRENT_DATE);
        """)

        insp_curr , dm_ins_curr , dm_per_curr , ins_rw_curr , a_grade_curr , b_grade_curr = cur.fetchone()

        insp_curr = int(insp_curr or 0)
        dm_ins_curr = int(dm_ins_curr or 0)
        dm_per_curr = int(dm_per_curr or 0)
        ins_rw_curr = int(ins_rw_curr or 0)
        a_grade_curr = int(a_grade_curr or 0)
        b_grade_curr = int(b_grade_curr or 0)

        # ---------- DAYS ----------
        cur.execute("""
            SELECT
                EXTRACT(day FROM (DATE_TRUNC('month', CURRENT_DATE)
                + INTERVAL '1 month - 1 day'))::INT,
                (EXTRACT(day FROM CURRENT_DATE)::INT - 1)
        """)
        month_days, prod_days = cur.fetchone()

        # ---------- ORACLE-COMPATIBLE LOGIC ----------
        inspec_current_month = round(insp_curr + ins_rw_curr)
        inspec_projected_mn = round((inspec_current_month / prod_days) * month_days) if prod_days else 0
        tot_prog = round((inspec_current_month / inspec_projected_mn) * 100, 2) if inspec_projected_mn else 0

    # ---------- OUTPUT ----------
    return {
        "title": "inspec",
        "prev_meter": fmt_int(insp_prev or 0),
        "prev_machines": fmt_int(v_prev_mac or 0),
        "prev_digi": fmt_int(dm_ins_prev or 0),
        "prev_digi_perc": fmt_int(dm_per_prev or 0),
        "prev_rw": fmt_int(ins_rw_prev or 0),
        "prev_a_grade": fmt_int(a_grade_prev or 0),
        "prev_b_grade": fmt_int(b_grade_prev or 0),

        "curr_meter": fmt_int(insp_curr),
        "curr_machines": fmt_int(v_curr_mac),
        "curr_digi": fmt_int(dm_ins_curr),
        "curr_digi_perc": fmt_int(dm_per_curr),
        "curr_rw": fmt_int(ins_rw_curr or 0),
        "curr_a_grade": fmt_int(a_grade_curr or 0),
        "curr_b_grade": fmt_int(b_grade_curr or 0),

        "inspec_projected_mn": fmt_int(inspec_projected_mn),

        "tot_progress": tot_prog,
    }
