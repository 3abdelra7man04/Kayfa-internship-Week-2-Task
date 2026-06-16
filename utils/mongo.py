import streamlit as st
from pymongo.mongo_client import MongoClient
import pandas as pd
import certifi
from datetime import datetime

@st.cache_resource
def get_mongo_client():
    uri = st.secrets.get("MONGO_URI")
    if not uri:
        st.error("MONGO_URI not found in secrets.toml")
        st.stop()
    try:
        client = MongoClient(uri, tlsCAFile=certifi.where())
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB Atlas: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def load_collection(collection_name):
    client = get_mongo_client()
    db_name = st.secrets.get("MONGO_DB", "kayfa_elearning")
    db = client[db_name]
    
    collection = db[collection_name]
    data = list(collection.find({}, {"_id": 0}))
    
    if not data:
        return pd.DataFrame()
        
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_all_data():
    """Load all 8 collections."""
    return {
        "students": load_collection("students_data"),
        "courses": load_collection("courses"),
        "groups": load_collection("groups_data"),
        "grades": load_collection("grades_data"),
        "attendance": load_collection("attendance_data"),
        "engagement": load_collection("engagement_events_data"),
        "submissions": load_collection("assignment_submissions_data"),
        "concepts": load_collection("concepts_performances_data")
    }

def apply_filters(data_dict, selected_course, selected_group, selected_gender):
    """Apply sidebar filters across all relevant dataframes based on student IDs."""
    
    students = data_dict["students"].copy()
    groups = data_dict["groups"].copy()
    
    # 1. Filter students based on Group and Gender
    if selected_group != "All":
        students = students[students["group_id"] == selected_group]
    if selected_gender != "All":
        students = students[students["gender"] == selected_gender]
        
    # 2. To filter by course, we must check which groups belong to the course
    if selected_course != "All":
        course_groups = groups[groups["course_id"] == selected_course]["group_id"].unique()
        students = students[students["group_id"].isin(course_groups)]
        
    valid_student_ids = set(students["student_id"].unique())
    
    # Now filter the other tables based on valid students or course
    filtered_data = {
        "students": students,
        "courses": data_dict["courses"].copy(),
        "groups": data_dict["groups"].copy()
    }
    
    if selected_course != "All":
        filtered_data["courses"] = filtered_data["courses"][filtered_data["courses"]["course_id"] == selected_course]
        filtered_data["groups"] = filtered_data["groups"][filtered_data["groups"]["course_id"] == selected_course]

    # For grades, attendance, engagement, submissions, concepts: filter by valid students
    # And also filter by course_id where applicable
    for key in ["grades", "attendance", "engagement", "submissions", "concepts"]:
        df = data_dict[key].copy()
        
        if "student_id" in df.columns:
            df = df[df["student_id"].isin(valid_student_ids)]
            
        if "course_id" in df.columns and selected_course != "All":
            df = df[df["course_id"] == selected_course]
            
        filtered_data[key] = df
        
    return filtered_data

def get_latest_state():
    """Retrieve the most recent snapshot (filters + KPIs + aggregations) from MongoDB."""
    client = get_mongo_client()
    db_name = st.secrets.get("MONGO_DB", "kayfa_elearning")
    db = client[db_name]

    latest = db["kpi_snapshots"].find_one(sort=[("ts", -1)], projection={"_id": 0})

    if latest:
        return latest.get("filters"), latest
    return None, None

def save_dashboard_state(filters_dict, filtered_data):
    """
    Compute all KPIs and chart aggregations from the already-filtered DataFrames
    and persist them as a single snapshot document in MongoDB.
    Returns the snapshot dict (without _id) so callers can store it in session_state.
    """
    client = get_mongo_client()
    db_name = st.secrets.get("MONGO_DB", "kayfa_elearning")
    db = client[db_name]

    now = datetime.utcnow()

    students    = filtered_data.get("students",    pd.DataFrame())
    courses     = filtered_data.get("courses",     pd.DataFrame())
    grades      = filtered_data.get("grades",      pd.DataFrame())
    groups      = filtered_data.get("groups",      pd.DataFrame())
    attendance  = filtered_data.get("attendance",  pd.DataFrame())
    submissions = filtered_data.get("submissions", pd.DataFrame())
    concepts    = filtered_data.get("concepts",    pd.DataFrame())
    engagement  = filtered_data.get("engagement",  pd.DataFrame())

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_students  = len(students)
    total_courses   = len(courses)
    avg_score       = round(float(grades["score"].mean()), 2)        if not grades.empty     else 0.0
    attendance_rate = round(float((attendance["status"] == "P").mean() * 100), 2) if not attendance.empty else 0.0

    kpis = {
        "total_students":  total_students,
        "total_courses":   total_courses,
        "avg_score":       avg_score,
        "attendance_rate": attendance_rate,
    }

    # ── Aggregations ──────────────────────────────────────────────────────────
    agg = {}

    # 1. Attendance rate per group
    if not attendance.empty and "group_id" in attendance.columns:
        att_rate = (
            attendance.groupby("group_id")
            .apply(lambda g: round(float((g["status"] == "P").mean() * 100), 2))
            .reset_index(name="attendance_rate")
        )
        agg["attendance_rate_by_group"] = att_rate.to_dict("records")
    else:
        agg["attendance_rate_by_group"] = []

    # 2. Score volatility (std dev) by assessment type — sorted descending
    if not grades.empty and "type" in grades.columns:
        vol = (
            grades.groupby("type")["score"]
            .std()
            .reset_index(name="std_dev")
            .sort_values("std_dev", ascending=False)
        )
        vol["std_dev"] = vol["std_dev"].round(4)
        agg["score_volatility"] = vol.to_dict("records")
    else:
        agg["score_volatility"] = []

    # 3. Average grade per course (sorted ascending for chart ordering)
    if not grades.empty and "course_id" in grades.columns:
        avg_g = (
            grades.groupby("course_id")["score"]
            .mean()
            .reset_index(name="avg_score")
        )
        avg_g["avg_score"] = avg_g["avg_score"].round(2)
        if not courses.empty and "course_name" in courses.columns:
            avg_g = avg_g.merge(courses[["course_id", "course_name"]], on="course_id", how="left")
        agg["course_avg_grade"] = avg_g.sort_values("avg_score").to_dict("records")
    else:
        agg["course_avg_grade"] = []

    # 4. Average grades and attendance rate (% present) by student
    if (not grades.empty and "student_id" in grades.columns) and (not attendance.empty and "student_id" in attendance.columns):
        avg_grades_by_student = (
            grades.groupby("student_id")["score"]
            .mean()
            .reset_index(name="score")
        )
        avg_grades_by_student["score"] = avg_grades_by_student["score"].round(2)

        # One row per student: % of records where status == "P"
        avg_att_by_student = (
            attendance.groupby("student_id")
            .apply(lambda g: round(float((g["status"] == "P").mean() * 100), 2))
            .reset_index(name="attendance_rate")
        )

        avg_grades_att_by_student = avg_grades_by_student.merge(avg_att_by_student, on="student_id", how="inner")
        agg["avg_grades_att_by_student"] = avg_grades_att_by_student.sort_values("score", ascending=False).to_dict("records")
    else:
        agg["avg_grades_att_by_student"] = []

    # 5. Average grades and login counts by student
    avg_grades_by_student = (
        grades.groupby("student_id")["score"]
        .mean()
        .reset_index(name="score")
    )
    avg_grades_by_student["score"] = avg_grades_by_student["score"].round(2)

    print("avg_grades_by_student", avg_grades_by_student.empty)

    # login count per student
    login_count_by_student = (
        engagement[engagement["event_type"] == "login"].groupby("student_id")
        .size()
        .reset_index(name="login_count")
    )

    print("login_count_by_student", login_count_by_student.empty)

    avg_grades_login_by_student = avg_grades_by_student.merge(login_count_by_student, on="student_id", how="left")
    agg["avg_grades_login_by_student"] = avg_grades_login_by_student.sort_values("score", ascending=False).to_dict("records")

    # 6 Average grades vs total_video_watch_seconds by student
    avg_grades_by_student = (
        grades.groupby("student_id")["score"]
        .mean()
        .reset_index(name="score")
    )
    avg_grades_by_student["score"] = avg_grades_by_student["score"].round(2)

    # total_video_watch_seconds per student
    total_video_watch_seconds_by_student = (
        engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"]
        .sum()
        .reset_index(name="total_video_watch_seconds")
    )

    avg_grades_video_watch_by_student = avg_grades_by_student.merge(total_video_watch_seconds_by_student, on="student_id", how="left")
    agg["avg_grades_video_watch_by_student"] = avg_grades_video_watch_by_student.sort_values("score", ascending=False).to_dict("records")

    # 7 concepts of highest failure rate
    if not concepts.empty:
        concepts_with_courses = concepts.merge(courses, on="course_id", how="left")

        # combine concept and course name to be course-concept-name
        concepts_with_courses["course_concept_name"] = concepts_with_courses["course_name"] + " - " + concepts_with_courses["concept_name"]

        concepts_failure_rate = (
            concepts_with_courses.groupby("course_concept_name")["mastery_status"]
            .value_counts(normalize=True)
            .mul(100)
            .round(2)
            .reset_index(name="failure_rate")
        )

        concepts_top_10_failure_rate = concepts_failure_rate[concepts_failure_rate["mastery_status"] == "failed"].sort_values("failure_rate", ascending=False).head(10)
        agg["concepts_top_10_failure_rate"] = concepts_top_10_failure_rate.to_dict("records")
    else:
        agg["concepts_top_10_failure_rate"] = []
    
    # 8 Worst Concept (Recursion Overtime)
    if not concepts.empty and "concept_name" in concepts.columns and "timestamp" in concepts.columns and "score_pct" in concepts.columns:
        recursion_concepts = concepts[concepts["concept_name"] == "Recursion"]
        if not recursion_concepts.empty:
            recursion_overtime = (
                recursion_concepts.groupby(recursion_concepts["timestamp"].str.split('T').str[0].rename("date"))["score_pct"]
                .mean()
                .reset_index(name="score_pct")
            )
            recursion_overtime['score_pct'] = recursion_overtime['score_pct'].round(2)
            agg["recursion_overtime"] = recursion_overtime.to_dict("records")
        else:
            agg["recursion_overtime"] = []
    else:
        agg["recursion_overtime"] = []

    # 9. Submission buffer vs score
    if not submissions.empty and not grades.empty and "assessment_id" in submissions.columns and "assessment_id" in grades.columns:
        subs_tmp = submissions.copy()
        grades_tmp = grades.copy()
        
        grades_tmp["assessment_id_base"] = grades_tmp["assessment_id"].str.replace(r'\d+$', '', regex=True)
        
        if "deadline" in subs_tmp.columns and "date" in grades_tmp.columns:
            subs_tmp["date_base"] = subs_tmp["deadline"].str.split('T').str[0]
            grades_tmp["date_base"] = grades_tmp["date"]
            
            sub_grades = subs_tmp.merge(
                grades_tmp, 
                left_on=["student_id", "course_id", "assessment_id", "date_base"], 
                right_on=["student_id", "course_id", "assessment_id_base", "date_base"], 
                how="inner"
            )
            
            if "deadline" in sub_grades.columns and "submitted_at" in sub_grades.columns:
                sub_grades['deadline_dt'] = pd.to_datetime(sub_grades['deadline'], errors='coerce')
                sub_grades['submitted_dt'] = pd.to_datetime(sub_grades['submitted_at'], errors='coerce')
                sub_grades['buffer_hours'] = (sub_grades['deadline_dt'] - sub_grades['submitted_dt']).dt.total_seconds() / 3600
                
                sub_score_student = sub_grades.groupby("student_id").agg({"buffer_hours": "mean", "score": "mean"}).reset_index()
                sub_score_student['buffer_hours'] = sub_score_student['buffer_hours'].round(2)
                sub_score_student['score'] = sub_score_student['score'].round(2)
                
                agg["submission_vs_score"] = sub_score_student.to_dict("records")
            else:
                agg["submission_vs_score"] = []
        else:
            agg["submission_vs_score"] = []
    else:
        agg["submission_vs_score"] = []

    # 10. Daily Attendance Trend
    if not attendance.empty and "session_datetime" in attendance.columns and "status" in attendance.columns:
        att_tmp = attendance.copy()
        att_tmp['date'] = pd.to_datetime(att_tmp['session_datetime'], errors='coerce').dt.strftime('%Y-%m-%d')
        daily_att = att_tmp.dropna(subset=['date']).groupby('date')['status'].apply(lambda x: round((x == 'P').mean() * 100, 2)).reset_index(name='attendance_pct')
        agg["daily_attendance"] = daily_att.to_dict("records")
    else:
        agg["daily_attendance"] = []

    # 11. Daily Engagement Trend
    if not engagement.empty and "event_datetime" in engagement.columns:
        eng_tmp = engagement.copy()
        eng_tmp['date'] = pd.to_datetime(eng_tmp['event_datetime'], errors='coerce').dt.strftime('%Y-%m-%d')
        daily_eng = eng_tmp.dropna(subset=['date']).groupby('date').size().reset_index(name='event_count')
        agg["daily_engagement"] = daily_eng.to_dict("records")
    else:
        agg["daily_engagement"] = []

    # 12. Age Band Analysis
    if not students.empty and "age" in students.columns:
        s_tmp = students.copy()
        s_tmp['age_band'] = pd.cut(s_tmp['age'], bins=[0, 19, 24, 29, 100], labels=['<20', '20-24', '25-29', '30+'])
        
        g_agg = grades.groupby('student_id')['score'].mean().reset_index(name='avg_score') if not grades.empty else pd.DataFrame(columns=['student_id', 'avg_score'])
        a_agg = attendance.groupby('student_id')['status'].apply(lambda x: (x == 'P').mean() * 100).reset_index(name='attendance_rate') if not attendance.empty else pd.DataFrame(columns=['student_id', 'attendance_rate'])
        e_agg = engagement.groupby('student_id').size().reset_index(name='engagement_count') if not engagement.empty else pd.DataFrame(columns=['student_id', 'engagement_count'])
        
        m = s_tmp[['student_id', 'age_band']].merge(g_agg, on='student_id', how='left') \
                                             .merge(a_agg, on='student_id', how='left') \
                                             .merge(e_agg, on='student_id', how='left')
        
        age_analysis = m.groupby('age_band', observed=False)[['avg_score', 'attendance_rate', 'engagement_count']].mean().reset_index()
        age_analysis = age_analysis.round(2)
        age_analysis = age_analysis.dropna(subset=['avg_score', 'attendance_rate', 'engagement_count'], how='all')
        
        agg["age_analysis"] = age_analysis.to_dict("records")
    else:
        agg["age_analysis"] = []

    # 13. Student Segmentation
    if not grades.empty and not attendance.empty and not engagement.empty and not concepts.empty:
        g_agg = grades.groupby('student_id')['score'].mean().reset_index(name='avg_grade')
        a_agg = attendance.groupby('student_id')['status'].apply(lambda x: (x=='P').mean()*100).reset_index(name='attendance_rate')
        e_agg = engagement.groupby('student_id').size().reset_index(name='engagement_count')
        failed_c = concepts[concepts['score_pct'] < 50].groupby('student_id').size().reset_index(name='failed_concepts')
        
        m = g_agg.merge(a_agg, on='student_id', how='left') \
                 .merge(e_agg, on='student_id', how='left') \
                 .merge(failed_c, on='student_id', how='left').fillna({'failed_concepts': 0})
                 
        def get_segment(row):
            if row['avg_grade'] >= 75 and row['attendance_rate'] >= 75:
                return 'High Achievers'
            elif row['attendance_rate'] < 70 and row['avg_grade'] < 65:
                return 'Disengaged At-Risk'
            elif row['attendance_rate'] >= 70 and row['failed_concepts'] >= 3:
                return 'Struggling Attenders'
            else:
                return 'Steady Performers'
                
        m['segment'] = m.apply(get_segment, axis=1)
        m['avg_grade'] = m['avg_grade'].round(1)
        m['attendance_rate'] = m['attendance_rate'].round(1)
        
        agg["student_segmentation"] = m.to_dict("records")
    else:
        agg["student_segmentation"] = []

    # 14. Group Discrepancies
    if not groups.empty and "stated_num_students" in groups.columns and "student_count" in groups.columns:
        g_tmp = groups.copy()
        g_tmp['discrepancy'] = g_tmp['student_count'] - g_tmp['stated_num_students']
        agg["group_discrepancies"] = g_tmp[['group_id', 'group_name', 'stated_num_students', 'student_count', 'discrepancy']].to_dict("records")
    else:
        agg["group_discrepancies"] = []

    # 15. At-Risk Ranking
    if not attendance.empty and not engagement.empty and not concepts.empty:
        # Engagement Decline
        e_tmp = engagement.copy()
        e_tmp['event_datetime'] = pd.to_datetime(e_tmp['event_datetime'])
        mid_date = e_tmp['event_datetime'].min() + (e_tmp['event_datetime'].max() - e_tmp['event_datetime'].min()) / 2
        fh = e_tmp[e_tmp['event_datetime'] < mid_date].groupby('student_id').size().reset_index(name='first_half')
        sh = e_tmp[e_tmp['event_datetime'] >= mid_date].groupby('student_id').size().reset_index(name='second_half')
        e_decline = fh.merge(sh, on='student_id', how='outer').fillna(0)
        e_decline['engagement_decline'] = e_decline['first_half'] - e_decline['second_half']
        e_decline['engagement_decline'] = e_decline['engagement_decline'].clip(lower=0)
        
        # Attendance & Failed Concepts
        a_agg = attendance.groupby('student_id')['status'].apply(lambda x: (x=='P').mean()*100).reset_index(name='attendance_rate')
        failed_c = concepts[concepts['score_pct'] < 50].groupby('student_id').size().reset_index(name='failed_concepts')
        
        m = a_agg.merge(e_decline[['student_id', 'engagement_decline']], on='student_id', how='left') \
                 .merge(failed_c, on='student_id', how='left').fillna(0)
                 
        m['attendance_risk'] = 100 - m['attendance_rate']
        
        max_att_risk = m['attendance_risk'].max() if m['attendance_risk'].max() > 0 else 1
        max_dec_risk = m['engagement_decline'].max() if m['engagement_decline'].max() > 0 else 1
        max_fai_risk = m['failed_concepts'].max() if m['failed_concepts'].max() > 0 else 1
        
        m['attendance_norm'] = m['attendance_risk'] / max_att_risk
        m['decline_norm'] = m['engagement_decline'] / max_dec_risk
        m['failed_norm'] = m['failed_concepts'] / max_fai_risk
        
        m['risk_score'] = ((m['attendance_norm'] + m['decline_norm'] + m['failed_norm']) / 3) * 100
        
        # Merge student names
        if not students.empty and "name" in students.columns:
            m = m.merge(students[['student_id', 'name']], on='student_id', how='left')
            m['student_name'] = m['name']
        else:
            m['student_name'] = m['student_id']
            
        m = m.sort_values('risk_score', ascending=False).head(10)
        
        # Round columns for presentation
        m['attendance_rate'] = m['attendance_rate'].round(1)
        m['risk_score'] = m['risk_score'].round(1)
        
        agg["at_risk_ranking"] = m[['student_id', 'student_name', 'attendance_rate', 'engagement_decline', 'failed_concepts', 'risk_score']].to_dict("records")
    else:
        agg["at_risk_ranking"] = []

    # 16. Group Grade Trends
    if not grades.empty and "date" in grades.columns and "group_id" in grades.columns:
        g_tmp = grades.copy()
        g_tmp['date'] = pd.to_datetime(g_tmp['date'])
        
        # Get the timeseries data for plotting
        trends = g_tmp.groupby(['group_id', 'date'])['score'].mean().reset_index()
        trends['date'] = trends['date'].dt.strftime('%Y-%m-%d')
        trends['score'] = trends['score'].round(1)
        agg["group_trends"] = trends.to_dict("records")
        
        # Calculate trend deltas (last assessment - first assessment)
        deltas = []
        for grp in trends['group_id'].unique():
            sub = trends[trends['group_id'] == grp].sort_values('date')
            if len(sub) > 1:
                first_score = sub.iloc[0]['score']
                last_score = sub.iloc[-1]['score']
                delta = round(last_score - first_score, 1)
                trend = "Trending Up 📈" if delta > 0 else ("Sliding Down 📉" if delta < 0 else "Flat ➖")
                deltas.append({
                    "group_id": grp,
                    "first_score": first_score,
                    "last_score": last_score,
                    "delta": delta,
                    "trend_status": trend
                })
            else:
                deltas.append({
                    "group_id": grp,
                    "first_score": sub.iloc[0]['score'],
                    "last_score": sub.iloc[0]['score'],
                    "delta": 0.0,
                    "trend_status": "Not Enough Data"
                })
        # Sort by delta descending (highest positive trend first)
        deltas = sorted(deltas, key=lambda x: x['delta'], reverse=True)
        agg["group_trend_deltas"] = deltas
    else:
        agg["group_trends"] = []
        agg["group_trend_deltas"] = []


    
    # ── Persist snapshot ──────────────────────────────────────────────────────
    snapshot = {
        "filters": filters_dict,
        "ts":      now,
        "kpis":    kpis,
        "agg":     agg,
    }
    db["kpi_snapshots"].insert_one(snapshot)
    snapshot.pop("_id", None)   # remove ObjectId before returning
    return snapshot
