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
# 4. LƯU TIẾN ĐỘ (SUPER ROBUST VERSION)
# ==========================================
def save_learning_progress(user_id, course_id, score=None, cheat_count=None, current_chapter=None, violation_log=None):
    client = get_connection()
    if not client: return False
    
    try:
        sheet = client.open("Ebsis_DB").worksheet("PROGRESS")
        all_data = sheet.get_all_records()
        df = pd.DataFrame(all_data)
        
        # Tìm dòng của User
        match = df[(df['user_id'] == str(user_id)) & (df['course_id'] == str(course_id))]
        
        if not match.empty:
            row_idx = match.index[0] + 2 # +2 vì index bắt đầu từ 0 và có header
            
            # --- BƯỚC 1: LẤY LOG CŨ ---
            try:
                old_log_raw = match.iloc[0]['violation_details']
                old_logs = json.loads(old_log_raw) if old_log_raw else []
            except:
                old_logs = []

            # --- BƯỚC 2: GỘP LOG MỚI VÀO ---
            if violation_log:
                # Chỉ thêm nếu log mới là một danh sách
                if isinstance(violation_log, list):
                    updated_logs = old_logs + violation_log
                else:
                    updated_logs = old_logs + [violation_log]
                
                # Chuyển thành JSON string để lưu, dùng ensure_ascii=False để không lỗi tiếng Việt
                log_json = json.dumps(updated_logs, ensure_ascii=False)
                sheet.update_cell(row_idx, 7, log_json) # Cột 7 là violation_details

            # --- BƯỚC 3: CẬP NHẬT CÁC THÔNG TIN KHÁC ---
            if score is not None: sheet.update_cell(row_idx, 3, score)
            
            # Cheat count cũng nên cộng dồn thay vì ghi đè
            if cheat_count is not None and cheat_count > 0:
                old_cheat = int(match.iloc[0]['cheat_count'] or 0)
                sheet.update_cell(row_idx, 4, old_cheat + cheat_count)
            
            if current_chapter is not None: sheet.update_cell(row_idx, 5, current_chapter)
            
            sheet.update_cell(row_idx, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
        else:
            # Nếu chưa có bản ghi thì tạo mới hoàn toàn
            log_json = json.dumps(violation_log if violation_log else [], ensure_ascii=False)
            new_row = [str(user_id), str(course_id), score or 0, cheat_count or 0, current_chapter or 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), log_json]
            sheet.append_row(new_row)
            
        return True
    except Exception as e:
        print(f"Lỗi lưu tiến độ: {e}")
        return False
    
# ==========================================
# 5. TẢI TIẾN ĐỘ
# ==========================================
def get_user_progress(user_id):
    client = get_connection()
    if not client: return None
    try:
        sheet = client.open("Ebsis_DB").worksheet("PROGRESS")
        records = sheet.get_all_records()
        for r in records:
            if str(r['user_id']) == str(user_id):
                return {
                    'course_id': r.get('course_id'),
                    'current_chapter': r.get('current_chapter', 0),
                    'score': r.get('score', 0),
                    'cheat_count': r.get('cheat_count', 0),
                    'violation_details': r.get('violation_details', '[]')
                }
        return None
    except: return None

# ==========================================
# 6. LẤY NỘI DUNG KHÓA HỌC
# ==========================================
def get_course_content(course_id):
    _, df_c = load_data()
    row = df_c[df_c['course_id'] == course_id]
    if not row.empty:
        try: return json.loads(row.iloc[0]['data_json'])
        except: return None
    return None

# ========================================================
# 7. [HOÀN THIỆN] CẬP NHẬT THÔNG TIN HỒ SƠ
# ========================================================
def update_user_profile_db(user_id, new_name, new_major, new_email=None):
    """
    Cập nhật thông tin sinh viên vào Google Sheets (Sheet USERS)
    Cấu trúc mong muốn: 
    Cột 2: full_name, Cột 6: email, Cột 7: major
    """
    client = get_connection()
    if not client: 
        return False
        
    try:
        sheet = client.open("Ebsis_DB").worksheet("USERS")
        cell = sheet.find(str(user_id))
        
        if cell:
            # 1. Cập nhật Họ tên (Cột 2)
            sheet.update_cell(cell.row, 2, make_serializable(new_name))
            
            # 2. Cập nhật Email (Cột 6 - Bạn cần thêm tiêu đề 'email' vào cột F trên Sheets)
            if new_email:
                sheet.update_cell(cell.row, 6, make_serializable(new_email))
            
            # 3. Cập nhật Chuyên ngành (Cột 7 - Bạn cần thêm tiêu đề 'major' vào cột G trên Sheets)
            sheet.update_cell(cell.row, 7, make_serializable(new_major))
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Lỗi cập nhật hồ sơ: {e}")
        return False