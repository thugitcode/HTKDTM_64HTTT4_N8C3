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
# 1. HÀM XỬ LÝ DỮ LIỆU (QUAN TRỌNG: BIẾN MỌI THỨ THÀNH GHI ĐƯỢC)
# ========================================================
def make_serializable(obj):
    """
    Hàm đệ quy giúp chuyển đổi mọi kiểu dữ liệu lạ (numpy, datetime...)
    thành kiểu dữ liệu chuẩn của Python (int, float, str, list, dict)
    để tránh lỗi khi lưu vào Google Sheets hoặc JSON.
    """
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
# 2. HÀM TẢI DỮ LIỆU
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    client = get_connection()
    if not client: return pd.DataFrame(), pd.DataFrame()
    try:
        ws_q = client.open("Ebsis_DB").worksheet("QUESTIONS")
        ws_c = client.open("Ebsis_DB").worksheet("COURSES")
        return pd.DataFrame(ws_q.get_all_records()), pd.DataFrame(ws_c.get_all_records())
    except Exception as e:
        print(f"Lỗi load_data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. AI PHÂN TÍCH
# ==========================================
def assign_personalized_course(user_answers, df_questions, df_courses):
    skill_stats = {}
    detailed_report = []
    total_correct = 0
    total_questions = len(df_questions)
    
    all_skills = df_questions['skill_tag'].unique()
    for s in all_skills:
        skill_stats[s] = {'total': 0, 'correct': 0, 'score': 0}

    for idx, row in df_questions.iterrows():
        q_id = str(row['id'])
        skill = row['skill_tag']
        correct_opt = row['correct_opt']
        user_choice = user_answers.get(q_id, None)
        is_correct = (str(user_choice) == str(correct_opt))
        
        skill_stats[skill]['total'] += 1
        if is_correct:
            skill_stats[skill]['correct'] += 1
            total_correct += 1
            
        detailed_report.append({
            "question": row['question_text'],
            "skill": skill,
            "user_opt": user_choice if user_choice else "Không chọn",
            "correct_opt": correct_opt,
            "is_correct": is_correct,
            "explanation": f"Đáp án đúng là {correct_opt}."
        })

    weakest_skill = "Coding"
    min_percent = 101
    for skill, stats in skill_stats.items():
        if stats['total'] > 0:
            percent = (stats['correct'] / stats['total']) * 100
        else:
            percent = 0
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
        "recommended_course": recommended_course
    }

# ==========================================
# 4. LƯU TIẾN ĐỘ (CẢI TIẾN: GHÉP CODE ĐỒNG BỘ)
# ==========================================
def save_learning_progress(user_id, course_id, score=None, cheat_count=None, current_chapter=None, violation_log=None):
    client = get_connection()
    if not client: return False
    
    try:
        sheet = client.open("Ebsis_DB").worksheet("PROGRESS")
        all_data = sheet.get_all_records()
        df = pd.DataFrame(all_data)
        
        # [BỔ SUNG] Ép kiểu string để tìm kiếm chính xác ID
        user_id_str = str(user_id)
        
        # Tìm dòng của User
        match = df[df['user_id'].astype(str) == user_id_str]
        
        if not match.empty:
            row_idx = match.index[0] + 2 
            
            # --- BƯỚC 1: LẤY LOG CŨ ---
            try:
                old_log_raw = match.iloc[0]['violation_details']
                old_logs = json.loads(old_log_raw) if old_log_raw else []
            except:
                old_logs = []

            # --- BƯỚC 2: GỘP LOG MỚI VÀO ---
            if violation_log:
                updated_logs = old_logs + (violation_log if isinstance(violation_log, list) else [violation_log])
                log_json = json.dumps(updated_logs, ensure_ascii=False)
                sheet.update_cell(row_idx, 7, log_json) 

            # --- BƯỚC 3: CẬP NHẬT CÁC THÔNG TIN KHÁC ---
            if score is not None: 
                sheet.update_cell(row_idx, 3, make_serializable(score))
            
            if cheat_count is not None:
                old_cheat = int(match.iloc[0]['cheat_count'] or 0)
                sheet.update_cell(row_idx, 4, old_cheat + cheat_count)
            
            # [CỐT LÕI] Ghi số chương hiện tại vào Cột 5
            if current_chapter is not None: 
                sheet.update_cell(row_idx, 5, int(current_chapter))
            
            # Cập nhật thời gian và course_id nếu có thay đổi
            sheet.update_cell(row_idx, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if course_id: sheet.update_cell(row_idx, 2, str(course_id))
            
        else:
            # Tạo mới nếu chưa có
            log_json = json.dumps(violation_log if violation_log else [], ensure_ascii=False)
            new_row = [str(user_id), str(course_id), score or 0, cheat_count or 0, current_chapter or 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), log_json]
            sheet.append_row(new_row)
            
        return True
    except Exception as e:
        print(f"Lỗi lưu tiến độ: {e}")
        return False
    
# ==========================================
# 5. TẢI TIẾN ĐỘ (CẢI TIẾN: FIX LỖI 0%)
# ==========================================
def get_user_progress(user_id):
    client = get_connection()
    if not client: return None
    try:
        sheet = client.open("Ebsis_DB").worksheet("PROGRESS")
        records = sheet.get_all_records()
        user_id_str = str(user_id)
        
        for r in records:
            # [FIX QUAN TRỌNG] Ép kiểu string khi so sánh để tránh lỗi ID số/chuỗi
            if str(r.get('user_id')) == user_id_str:
                return {
                    'course_id': str(r.get('course_id', '')),
                    # Ép kiểu float rồi mới sang int để tránh lỗi chuỗi "3.0"
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
    # So sánh ID dạng chuỗi
    row = df_c[df_c['course_id'].astype(str) == str(course_id)]
    if not row.empty:
        try: return json.loads(row.iloc[0]['data_json'])
        except: return None
    return None

# ========================================================
# 7. CẬP NHẬT THÔNG TIN HỒ SƠ (GIỮ NGUYÊN LUỒNG CŨ)
# ========================================================
def update_user_profile_db(user_id, new_name, new_major, new_email=None):
    client = get_connection()
    if not client: return False
    try:
        sheet = client.open("Ebsis_DB").worksheet("USERS")
        cell = sheet.find(str(user_id))
        if cell:
            sheet.update_cell(cell.row, 2, make_serializable(new_name))
            if new_email:
                sheet.update_cell(cell.row, 6, make_serializable(new_email))
            sheet.update_cell(cell.row, 7, make_serializable(new_major))
            return True
        return False
    except Exception as e:
        print(f"Lỗi cập nhật hồ sơ: {e}")
        return False