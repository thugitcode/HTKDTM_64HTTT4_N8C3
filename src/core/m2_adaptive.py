import pandas as pd
import json
import streamlit as st
from datetime import datetime, date
import sys
import os
import traceback
import numpy as np 

# Cấu hình đường dẫn import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.db_connector import get_connection

# ========================================================
# 1. HÀM XỬ LÝ DỮ LIỆU (SERALIZABLE)
# ========================================================
def make_serializable(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj

# ==========================================
# 2. HÀM TẢI DỮ LIỆU (TỐI ƯU CACHING)
# ==========================================
@st.cache_data(ttl=300)
def load_data():
    client = get_connection()
    if not client: return pd.DataFrame(), pd.DataFrame()
    try:
        db = client.open("Ebsis_DB")
        ws_q = db.worksheet("QUESTIONS")
        ws_c = db.worksheet("COURSES")
        return pd.DataFrame(ws_q.get_all_records()), pd.DataFrame(ws_c.get_all_records())
    except Exception as e:
        print(f"Lỗi load_data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. AI PHÂN TÍCH NĂNG LỰC
# ==========================================
def assign_personalized_course(user_answers, df_questions, df_courses):
    skill_stats = {}
    detailed_report = []
    total_correct = 0
    
    # Chỉ lấy các câu hỏi chẩn đoán (không lấy Checkpoint)
    diag_questions = df_questions[~df_questions['id'].astype(str).str.startswith('CHECK_')]
    total_questions = len(diag_questions)
    
    all_skills = diag_questions['skill_tag'].unique()
    for s in all_skills:
        skill_stats[s] = {'total': 0, 'correct': 0, 'score': 0}

    for idx, row in diag_questions.iterrows():
        q_id = str(row['id'])
        skill = row['skill_tag']
        correct_opt_key = str(row['correct_opt']).strip().upper()
        user_choice = str(user_answers.get(q_id, "")).strip().upper()
        
        is_correct = (user_choice == correct_opt_key)
        
        skill_stats[skill]['total'] += 1
        if is_correct:
            skill_stats[skill]['correct'] += 1
            total_correct += 1
            
        detailed_report.append({
            "question": row['question_text'],
            "skill": skill,
            "user_opt": user_answers.get(q_id, "Chưa chọn"),
            "correct_opt": row.get(f"option_{correct_opt_key.lower()}", correct_opt_key),
            "is_correct": is_correct
        })

    weakest_skill = "Coding"
    min_percent = 101
    for skill, stats in skill_stats.items():
        percent = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        stats['score'] = round(percent, 1)
        if percent < min_percent:
            min_percent = percent
            weakest_skill = skill

    course_row = df_courses[df_courses['skill_tag'] == weakest_skill]
    if course_row.empty:
        recommended_course = json.loads(df_courses.iloc[0]['data_json'])
    else:
        recommended_course = json.loads(course_row.iloc[0]['data_json'])
        
    return {
        "total_score": round((total_correct / total_questions) * 100, 1),
        "skill_breakdown": skill_stats,
        "details": detailed_report,
        "weakest_skill": weakest_skill,
        "recommended_course": recommended_course,
        "correct_count": total_correct,
        "total_questions": total_questions
    }

# ==========================================
# 4. LƯU TIẾN ĐỘ (FIX LỖI RESET KHI CHECKPOINT)
# ==========================================
def save_learning_progress(user_id, course_id, score=None, cheat_count=None, current_chapter=None, violation_log=None):
    client = get_connection()
    if not client: return False
    
    try:
        db = client.open("Ebsis_DB")
        sheet = db.worksheet("PROGRESS")
        df = pd.DataFrame(sheet.get_all_records())
        user_id_str = str(user_id).strip()
        
        df['user_id'] = df['user_id'].astype(str).str.strip()
        match = df[df['user_id'] == user_id_str]
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not match.empty:
            row_idx = match.index[0] + 2 
            
            # Gộp Log vi phạm
            try:
                old_log_raw = str(match.iloc[0].get('violation_details', '[]'))
                old_logs = json.loads(old_log_raw) if old_log_raw else []
            except: old_logs = []
            
            if violation_log:
                new_logs = violation_log if isinstance(violation_log, list) else [violation_log]
                updated_logs = old_logs + new_logs
            else: updated_logs = old_logs
            
            # --- LOGIC FIX Ở ĐÂY ---
            old_chapter = int(float(match.iloc[0].get('current_chapter', 0)))
            
            # Nếu là thi chẩn đoán (lần đầu): score có và current_chapter=0 -> Reset chapter về 0
            # Nếu là thi Checkpoint (cuối khóa): score có và current_chapter=8 -> Giữ nguyên 8
            if score is not None:
                final_chapter = current_chapter if current_chapter is not None else 0
            else:
                final_chapter = max(old_chapter, int(current_chapter)) if current_chapter is not None else old_chapter

            # Đảm bảo điểm số không bị ghi đè về 0 nếu score truyền vào là None
            new_score = score if score is not None else match.iloc[0].get('score', 0)
            new_cheat = int(match.iloc[0].get('cheat_count', 0)) + (cheat_count or 0)

            update_values = [
                str(course_id), 
                make_serializable(new_score),
                new_cheat,
                final_chapter,
                now_str,
                json.dumps(make_serializable(updated_logs), ensure_ascii=False)
            ]
            
            sheet.update(range_name=f"B{row_idx}:G{row_idx}", values=[update_values])
        else:
            new_row = [
                user_id_str, str(course_id), score or 0, 
                cheat_count or 0, current_chapter or 0, now_str, 
                json.dumps(violation_log if violation_log else [], ensure_ascii=False)
            ]
            sheet.append_row(new_row)
            
        return True
    except Exception as e:
        st.error(f"Lỗi ghi Cloud: {e}")
        return False
    
# ==========================================
# 5. TẢI TIẾN ĐỘ (FIX ÉP KIỂU)
# ==========================================
def get_user_progress(user_id):
    client = get_connection()
    if not client: return None
    try:
        sheet = client.open("Ebsis_DB").worksheet("PROGRESS")
        records = sheet.get_all_records()
        u_id = str(user_id).strip()
        
        for r in records:
            if str(r.get('user_id')).strip() == u_id:
                return {
                    'course_id': str(r.get('course_id', '')),
                    'current_chapter': int(float(r.get('current_chapter', 0))),
                    'score': int(float(r.get('score', 0))),
                    'cheat_count': int(float(r.get('cheat_count', 0))),
                    'violation_details': r.get('violation_details', '[]')
                }
        return None
    except Exception as e:
        print(f"Lỗi get_user_progress: {e}")
        return None

# ==========================================
# 6. LẤY NỘI DUNG KHÓA HỌC
# ==========================================
def get_course_content(course_id):
    _, df_c = load_data()
    if df_c.empty: return None
    row = df_c[df_c['course_id'].astype(str) == str(course_id)]
    if not row.empty:
        try:
            return json.loads(row.iloc[0]['data_json'])
        except: return None
    return None

# ==========================================
# 7. CẬP NHẬT HỒ SƠ
# ==========================================
def update_user_profile_db(user_id, new_name, new_major, new_email=None):
    client = get_connection()
    if not client: return False
    try:
        sheet = client.open("Ebsis_DB").worksheet("USERS")
        cell = sheet.find(str(user_id))
        if cell:
            sheet.update_cell(cell.row, 2, str(new_name))
            if new_email: sheet.update_cell(cell.row, 6, str(new_email))
            sheet.update_cell(cell.row, 7, str(new_major))
            return True
        return False
    except Exception as e:
        print(f"Lỗi cập nhật hồ sơ: {e}")
        return False
    
def handle_next_course_registration(user_id, next_course_id):
    client = get_connection()
    if not client: return False, "Lỗi kết nối"
    try:
        db = client.open("Ebsis_DB")
        sheet = db.worksheet("PROGRESS")
        df = pd.DataFrame(sheet.get_all_records())
        
        # Tìm đúng dòng của User
        user_id_str = str(user_id).strip()
        df['user_id'] = df['user_id'].astype(str).str.strip()
        match = df[df['user_id'] == user_id_str]
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not match.empty:
            row_idx = match.index[0] + 2
            # CẬP NHẬT: Phải ghi ID mới (next_course_id) vào cột B (index 1)
            update_values = [
                str(next_course_id), # Cột B: Course ID mới
                0,                  # Cột C: Score về 0
                0,                  # Cột D: Cheat về 0
                0,                  # Cột E: Chapter về 0
                now_str,            # Cột F: Time
                "[]"                # Cột G: Log trống
            ]
            sheet.update(range_name=f"B{row_idx}:G{row_idx}", values=[update_values])
            return True, "Thành công"
        return False, "Không tìm thấy user"
    except Exception as e:
        return False, str(e)