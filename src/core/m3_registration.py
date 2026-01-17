import pandas as pd
from datetime import datetime
from src.services.db_connector import get_connection

def handle_next_course_registration(user_id, current_course_id):
    """
    Thêm dòng tiến độ mới cho môn học tiếp theo mà không xóa môn cũ.
    """
    client = get_connection()
    if not client: 
        return False, "Không thể kết nối cơ sở dữ liệu."
    
    try:
        db = client.open("Ebsis_DB")
        
        # 1. Xác định môn học tiếp theo từ bảng COURSES
        ws_courses = db.worksheet("COURSES")
        all_courses = ws_courses.get_all_records()
        
        # Tìm skill_tag của môn hiện tại
        current_course = next((c for c in all_courses if str(c['course_id']) == str(current_course_id)), None)
        if not current_course:
            return False, "Không tìm thấy thông tin môn học hiện tại."
            
        current_skill = current_course.get('skill_tag', 'Coding')
        
        # Logic luân chuyển (Thư có thể điều chỉnh mapping này)
        skill_map = {"Coding": "Database", "Database": "Network", "Network": "Agile", "Agile": "Coding"}
        next_skill = skill_map.get(current_skill, "Coding")
        
        # Lấy thông tin môn mới
        next_course_info = next((c for c in all_courses if c['skill_tag'] == next_skill), None)
        if not next_course_info:
            return False, f"Chưa cấu hình môn học cho kỹ năng {next_skill}."

        # 2. Kiểm tra xem môn này đã được đăng ký chưa để tránh trùng lặp
        ws_progress = db.worksheet("PROGRESS")
        existing_records = ws_progress.get_all_records()
        is_already_reg = any(str(r['user_id']) == str(user_id) and str(r['course_id']) == str(next_course_info['course_id']) for r in existing_records)
        
        if is_already_reg:
            return True, f"Bạn đã đăng ký môn {next_skill} trước đó rồi. Đang chuyển hướng..."

        # 3. THÊM DÒNG MỚI (Key point: append_row để giữ lại Progress cũ)
        new_row = [
            str(user_id), 
            str(next_course_info['course_id']), 
            0,      # score
            0,      # cheat_count
            0,      # current_chapter (Bắt đầu từ đầu)
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "[]"    # violation_logs
        ]
        ws_progress.append_row(new_row)
        
        return True, f"Đã mở khóa lộ trình {next_skill} thành công!"
        
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"