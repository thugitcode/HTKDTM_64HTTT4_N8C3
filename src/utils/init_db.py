import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.db_connector import get_connection

# ==========================================
# 1. BỘ ĐỀ THI ĐÁNH GIÁ NĂNG LỰC (20 CÂU)
# ==========================================
# Chia làm 4 phần: Python (Tuần 1), SQL (Tuần 2), Network (Tuần 3), Agile (Tuần 4)
RAW_QUESTIONS = [
    # --- TUẦN 1: CODING (PYTHON) ---
    {"id": "CODE_01", "skill_tag": "Coding", "question_text": "Hàm len() trong Python dùng để làm gì?", "option_a": "Tính độ dài chuỗi/list", "option_b": "Tạo list mới", "option_c": "Xóa phần tử", "option_d": "Lặp", "correct_opt": "A"},
    {"id": "CODE_02", "skill_tag": "Coding", "question_text": "Kết quả của 10 // 3 là?", "option_a": "3.33", "option_b": "3", "option_c": "1", "option_d": "30", "correct_opt": "B"},
    {"id": "CODE_03", "skill_tag": "Coding", "question_text": "Index của phần tử cuối cùng trong list là?", "option_a": "0", "option_b": "1", "option_c": "-1", "option_d": "len()", "correct_opt": "C"},
    {"id": "CODE_04", "skill_tag": "Coding", "question_text": "Để bắt lỗi trong Python, ta dùng khối lệnh nào?", "option_a": "try...catch", "option_b": "try...except", "option_c": "if...else", "option_d": "do...while", "correct_opt": "B"},
    {"id": "CODE_05", "skill_tag": "Coding", "question_text": "Thư viện nào dùng để vẽ biểu đồ?", "option_a": "Pandas", "option_b": "Numpy", "option_c": "Matplotlib", "option_d": "Requests", "correct_opt": "C"},

    # --- TUẦN 2: DATABASE (SQL) ---
    {"id": "DB_01", "skill_tag": "Database", "question_text": "Lệnh SELECT dùng để làm gì?", "option_a": "Xóa dữ liệu", "option_b": "Lấy dữ liệu", "option_c": "Sửa dữ liệu", "option_d": "Thêm dữ liệu", "correct_opt": "B"},
    {"id": "DB_02", "skill_tag": "Database", "question_text": "Điều kiện WHERE đặt ở đâu?", "option_a": "Trước SELECT", "option_b": "Sau FROM", "option_c": "Sau ORDER BY", "option_d": "Cuối cùng", "correct_opt": "B"},
    {"id": "DB_03", "skill_tag": "Database", "question_text": "JOIN nào trả về bản ghi chung của 2 bảng?", "option_a": "LEFT JOIN", "option_b": "RIGHT JOIN", "option_c": "INNER JOIN", "option_d": "FULL JOIN", "correct_opt": "C"},
    {"id": "DB_04", "skill_tag": "Database", "question_text": "Khóa chính (PK) có được trùng không?", "option_a": "Có", "option_b": "Không", "option_c": "Tùy database", "option_d": "Chỉ khi null", "correct_opt": "B"},
    {"id": "DB_05", "skill_tag": "Database", "question_text": "Lệnh nào dùng để sắp xếp?", "option_a": "SORT BY", "option_b": "ORDER BY", "option_c": "GROUP BY", "option_d": "ARRANGE", "correct_opt": "B"},

    # --- TUẦN 3: NETWORK ---
    {"id": "NET_01", "skill_tag": "Network", "question_text": "IP là viết tắt của?", "option_a": "Internet Provider", "option_b": "Internet Protocol", "option_c": "Intel Processor", "option_d": "Info Pack", "correct_opt": "B"},
    {"id": "NET_02", "skill_tag": "Network", "question_text": "DNS dùng để làm gì?", "option_a": "Cấp IP động", "option_b": "Phân giải tên miền", "option_c": "Định tuyến", "option_d": "Bảo mật", "correct_opt": "B"},
    {"id": "NET_03", "skill_tag": "Network", "question_text": "Ping dùng giao thức nào?", "option_a": "TCP", "option_b": "UDP", "option_c": "ICMP", "option_d": "HTTP", "correct_opt": "C"},
    {"id": "NET_04", "skill_tag": "Network", "question_text": "Cổng 80 là của dịch vụ nào?", "option_a": "FTP", "option_b": "SSH", "option_c": "HTTP", "option_d": "HTTPS", "correct_opt": "C"},
    {"id": "NET_05", "skill_tag": "Network", "question_text": "Địa chỉ MAC là địa chỉ gì?", "option_a": "Vật lý", "option_b": "Logic", "option_c": "Mạng", "option_d": "Email", "correct_opt": "A"},

    # --- TUẦN 4: SE & AGILE ---
    {"id": "SE_01", "skill_tag": "SE", "question_text": "Agile là gì?", "option_a": "Ngôn ngữ lập trình", "option_b": "Phương pháp quản lý dự án", "option_c": "Công cụ test", "option_d": "Server", "correct_opt": "B"},
    {"id": "SE_02", "skill_tag": "SE", "question_text": "Ai chịu trách nhiệm về Product Backlog?", "option_a": "Scrum Master", "option_b": "Dev Team", "option_c": "Product Owner", "option_d": "Tester", "correct_opt": "C"},
    {"id": "SE_03", "skill_tag": "SE", "question_text": "Sprint thường kéo dài bao lâu?", "option_a": "1-4 tuần", "option_b": "3 tháng", "option_c": "1 ngày", "option_d": "1 năm", "correct_opt": "A"},
    {"id": "SE_04", "skill_tag": "SE", "question_text": "Daily Meeting nên kéo dài tối đa?", "option_a": "1 tiếng", "option_b": "15 phút", "option_c": "30 phút", "option_d": "Không giới hạn", "correct_opt": "B"},
    {"id": "SE_05", "skill_tag": "SE", "question_text": "User Story mô tả cái gì?", "option_a": "Cấu trúc database", "option_b": "Nhu cầu người dùng", "option_c": "Lỗi phần mềm", "option_d": "Code", "correct_opt": "B"}
]

# ==========================================
# 2. KHUNG CHƯƠNG TRÌNH HỌC (MASTER CURRICULUM)
# ==========================================
# Đây là "Lộ trình tổng quan" cho 1 tháng
MASTER_CURRICULUM = [
    {
        "week": 1,
        "topic": "Coding",
        "title": "Tuần 1: Nhập môn Python & Tư duy lập trình",
        "description": "Làm chủ cú pháp cơ bản, biến, hàm và xử lý lỗi.",
        "materials": [
            {"type": "Video", "name": "Python Basic (F8)", "url": "https://youtu.be/07wW43c0dVM"},
            {"type": "Article", "name": "W3Schools Python Tutorial", "url": "https://www.w3schools.com/python/"}
        ]
    },
    {
        "week": 2,
        "topic": "Database",
        "title": "Tuần 2: Làm chủ SQL & Cơ sở dữ liệu",
        "description": "Hiểu về quan hệ bảng, truy vấn SELECT, JOIN và tối ưu hóa.",
        "materials": [
            {"type": "Video", "name": "SQL in 60 mins (TEDU)", "url": "https://youtu.be/kYOA94b4sMg"},
            {"type": "PDF", "name": "SQL Cheatsheet", "url": "#"}
        ]
    },
    {
        "week": 3,
        "topic": "Network",
        "title": "Tuần 3: Mạng máy tính căn bản",
        "description": "Mô hình OSI, TCP/IP và cách Internet vận hành.",
        "materials": [
            {"type": "Video", "name": "OSI Model Explained", "url": "https://youtu.be/3b_T44m9gvw"},
            {"type": "Lab", "name": "Cisco Packet Tracer Lab 1", "url": "#"}
        ]
    },
    {
        "week": 4,
        "topic": "SE",
        "title": "Tuần 4: Quy trình phần mềm & Agile",
        "description": "Làm việc nhóm hiệu quả với Scrum framework.",
        "materials": [
            {"type": "Video", "name": "Agile & Scrum Overview", "url": "https://youtu.be/XU0llRltyFM"},
            {"type": "Slide", "name": "Quy trình phát triển phần mềm", "url": "#"}
        ]
    }
]

def sync_data():
    print("⏳ Đang thiết lập lộ trình học chuẩn...")
    client = get_connection()
    if not client: return

    # 1. NẠP CÂU HỎI
    try:
        try: sheet_q = client.open("Ebsis_DB").worksheet("QUESTIONS")
        except: sheet_q = client.open("Ebsis_DB").add_worksheet("QUESTIONS", 200, 10)
        sheet_q.clear()
        sheet_q.append_row(["id", "skill_tag", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_opt"])
        rows = [[q['id'], q['skill_tag'], q['question_text'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_opt']] for q in RAW_QUESTIONS]
        sheet_q.append_rows(rows)
        print("✅ Đã nạp 20 câu hỏi.")
    except Exception as e: print(f"Lỗi Questions: {e}")

    # 2. NẠP CURRICULUM (Dùng Sheet MATERIALS để lưu curriculum)
    try:
        try: sheet_c = client.open("Ebsis_DB").worksheet("CURRICULUM")
        except: sheet_c = client.open("Ebsis_DB").add_worksheet("CURRICULUM", 50, 10)
        sheet_c.clear()
        sheet_c.append_row(["week", "topic", "title", "description", "materials_json"]) # materials_json sẽ lưu string json
        
        import json
        c_rows = []
        for c in MASTER_CURRICULUM:
            c_rows.append([c['week'], c['topic'], c['title'], c['description'], json.dumps(c['materials'])])
            
        sheet_c.append_rows(c_rows)
        print("✅ Đã nạp Khung chương trình chuẩn (4 tuần).")
    except Exception as e: print(f"Lỗi Curriculum: {e}")

if __name__ == "__main__":
    sync_data()