import sys
import os
import json
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.db_connector import get_connection

# ==========================================
# 1. BỘ ĐỀ THI ĐÁNH GIÁ NĂNG LỰC (20 CÂU)
# ==========================================
RAW_QUESTIONS = [
    # --- PHẦN 1: CODING (PYTHON) ---
    {"id": "CODE_01", "skill_tag": "Coding", "question_text": "Hàm len() trong Python dùng để làm gì?", "option_a": "Tính độ dài chuỗi/list", "option_b": "Tạo list mới", "option_c": "Xóa phần tử", "option_d": "Lặp", "correct_opt": "A"},
    {"id": "CODE_02", "skill_tag": "Coding", "question_text": "Kết quả của 10 // 3 là?", "option_a": "3.33", "option_b": "3", "option_c": "1", "option_d": "30", "correct_opt": "B"},
    {"id": "CODE_03", "skill_tag": "Coding", "question_text": "Index của phần tử cuối cùng trong list là?", "option_a": "0", "option_b": "1", "option_c": "-1", "option_d": "len()", "correct_opt": "C"},
    {"id": "CODE_04", "skill_tag": "Coding", "question_text": "Để bắt lỗi trong Python, ta dùng khối lệnh nào?", "option_a": "try...catch", "option_b": "try...except", "option_c": "if...else", "option_d": "do...while", "correct_opt": "B"},
    {"id": "CODE_05", "skill_tag": "Coding", "question_text": "Thư viện nào dùng để vẽ biểu đồ?", "option_a": "Pandas", "option_b": "Numpy", "option_c": "Matplotlib", "option_d": "Requests", "correct_opt": "C"},

    # --- PHẦN 2: DATABASE (SQL) ---
    {"id": "DB_01", "skill_tag": "Database", "question_text": "Lệnh SELECT dùng để làm gì?", "option_a": "Xóa dữ liệu", "option_b": "Lấy dữ liệu", "option_c": "Sửa dữ liệu", "option_d": "Thêm dữ liệu", "correct_opt": "B"},
    {"id": "DB_02", "skill_tag": "Database", "question_text": "Điều kiện WHERE đặt ở đâu?", "option_a": "Trước SELECT", "option_b": "Sau FROM", "option_c": "Sau ORDER BY", "option_d": "Cuối cùng", "correct_opt": "B"},
    {"id": "DB_03", "skill_tag": "Database", "question_text": "JOIN nào trả về bản ghi chung của 2 bảng?", "option_a": "LEFT JOIN", "option_b": "RIGHT JOIN", "option_c": "INNER JOIN", "option_d": "FULL JOIN", "correct_opt": "C"},
    {"id": "DB_04", "skill_tag": "Database", "question_text": "Khóa chính (PK) có được trùng không?", "option_a": "Có", "option_b": "Không", "option_c": "Tùy database", "option_d": "Chỉ khi null", "correct_opt": "B"},
    {"id": "DB_05", "skill_tag": "Database", "question_text": "Lệnh nào dùng để sắp xếp?", "option_a": "SORT BY", "option_b": "ORDER BY", "option_c": "GROUP BY", "option_d": "ARRANGE", "correct_opt": "B"},

    # --- PHẦN 3: NETWORK ---
    {"id": "NET_01", "skill_tag": "Network", "question_text": "IP là viết tắt của?", "option_a": "Internet Provider", "option_b": "Internet Protocol", "option_c": "Intel Processor", "option_d": "Info Pack", "correct_opt": "B"},
    {"id": "NET_02", "skill_tag": "Network", "question_text": "DNS dùng để làm gì?", "option_a": "Cấp IP động", "option_b": "Phân giải tên miền (Domain -> IP)", "option_c": "Định tuyến", "option_d": "Bảo mật", "correct_opt": "B"},
    {"id": "NET_03", "skill_tag": "Network", "question_text": "Lệnh Ping dùng giao thức nào?", "option_a": "TCP", "option_b": "UDP", "option_c": "ICMP", "option_d": "HTTP", "correct_opt": "C"},
    {"id": "NET_04", "skill_tag": "Network", "question_text": "Cổng (Port) 80 thường dùng cho dịch vụ nào?", "option_a": "FTP", "option_b": "SSH", "option_c": "HTTP (Web)", "option_d": "HTTPS", "correct_opt": "C"},
    {"id": "NET_05", "skill_tag": "Network", "question_text": "Địa chỉ MAC là địa chỉ gì?", "option_a": "Vật lý (Phần cứng)", "option_b": "Logic (Phần mềm)", "option_c": "Mạng ảo", "option_d": "Email", "correct_opt": "A"},

    # --- PHẦN 4: AGILE/SCRUM ---
    {"id": "SE_01", "skill_tag": "Agile", "question_text": "Agile là gì?", "option_a": "Ngôn ngữ lập trình", "option_b": "Tư duy phát triển phần mềm linh hoạt", "option_c": "Công cụ test", "option_d": "Server", "correct_opt": "B"},
    {"id": "SE_02", "skill_tag": "Agile", "question_text": "Ai là người sở hữu Product Backlog?", "option_a": "Scrum Master", "option_b": "Dev Team", "option_c": "Product Owner", "option_d": "Tester", "correct_opt": "C"},
    {"id": "SE_03", "skill_tag": "Agile", "question_text": "Sprint thường kéo dài bao lâu?", "option_a": "1-4 tuần", "option_b": "3 tháng", "option_c": "1 ngày", "option_d": "1 năm", "correct_opt": "A"},
    {"id": "SE_04", "skill_tag": "Agile", "question_text": "Daily Meeting nên kéo dài tối đa?", "option_a": "1 tiếng", "option_b": "15 phút", "option_c": "30 phút", "option_d": "Không giới hạn", "correct_opt": "B"},
    {"id": "SE_05", "skill_tag": "Agile", "question_text": "User Story mô tả cái gì?", "option_a": "Cấu trúc database", "option_b": "Nhu cầu người dùng", "option_c": "Lỗi phần mềm", "option_d": "Code", "correct_opt": "B"}
]

# --- HÀM TẠO BÀI TẬP NHANH ---
def get_practice_lesson(title, desc):
    return {"type": "Practice", "title": title, "desc": desc}

# ==========================================
# 2. CHI TIẾT 4 LỘ TRÌNH (FULL 8 NGÀY/MÔN)
# ==========================================

# --- PYTHON ---
PYTHON_COURSE = {
    "course_id": "CRS_PY_PRO", "skill_tag": "Coding", "title": "🐍 Python Foundation",
    "chapters": [
        {"day": 1, "title": "Cài đặt & Biến số", "lessons": [{"type": "Video", "title": "Nhập môn Python", "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8"}, get_practice_lesson("Lab 1", "Cài đặt môi trường và viết lệnh print đầu tiên.")]},
        {"day": 2, "title": "Kiểu dữ liệu cơ bản", "lessons": [{"type": "Video", "title": "Làm việc với String & Number", "url": "https://www.youtube.com/watch?v=HGOBQPFzWKo"}, get_practice_lesson("Lab 2", "Khai báo biến lưu tên và tuổi của bạn.")]},
        {"day": 3, "title": "List & Tuple", "lessons": [{"type": "Video", "title": "Cấu trúc dữ liệu danh sách", "url": "https://www.youtube.com/watch?v=8M20vS58V-U"}, get_practice_lesson("Lab 3", "Tạo một list 5 món ăn và in ra phần tử thứ 2.")]},
        {"day": 4, "title": "Cấu trúc If-Else", "lessons": [{"type": "Video", "title": "Điều hướng Logic", "url": "https://www.youtube.com/watch?v=f4vVq_H8Yog"}, get_practice_lesson("Lab 4", "Viết code kiểm tra số nhập vào là dương hay âm.")]},
        {"day": 5, "title": "Vòng lặp For/While", "lessons": [{"type": "Video", "title": "Tự động hóa tác vụ", "url": "https://www.youtube.com/watch?v=0ZvaDa8e8Y4"}, get_practice_lesson("Lab 5", "Dùng vòng lặp in các số từ 1 đến 10.")]},
        {"day": 6, "title": "Hàm (Functions)", "lessons": [{"type": "Video", "title": "Viết mã nguồn tái sử dụng", "url": "https://www.youtube.com/watch?v=u-OmAt_2FpY"}, get_practice_lesson("Lab 6", "Viết hàm tính diện tích hình chữ nhật.")]},
        {"day": 7, "title": "Xử lý lỗi Exceptions", "lessons": [{"type": "Video", "title": "Hạn chế Crash ứng dụng", "url": "https://www.youtube.com/watch?v=NIWwJbo-9_8"}, get_practice_lesson("Lab 7", "Dùng try-except để xử lý lỗi chia cho 0.")]},
        {"day": 8, "title": "🚩 Checkpoint Python", "lessons": [{"type": "Quiz", "title": "Bài thi cuối khóa", "test_id": "CH_PY"}]}
    ]
}

# --- SQL ---
SQL_COURSE = {
    "course_id": "CRS_SQL_MASTER", "skill_tag": "Database", "title": "🗄️ SQL Masterclass",
    "chapters": [
        {"day": 1, "title": "Hệ quản trị CSDL", "lessons": [{"type": "Video", "title": "Giới thiệu SQL", "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY"}, get_practice_lesson("Lab 1", "Cài đặt SQL Server hoặc MySQL.")]},
        {"day": 2, "title": "Truy vấn SELECT", "lessons": [{"type": "Video", "title": "Lấy dữ liệu cơ bản", "url": "https://www.youtube.com/watch?v=27axs9dO7AE"}, get_practice_lesson("Lab 2", "SELECT tất cả nhân viên trong bảng Employees.")]},
        {"day": 3, "title": "Lọc với WHERE", "lessons": [{"type": "Video", "title": "Điều kiện truy vấn", "url": "https://www.youtube.com/watch?v=p3qvj9hO_Bo"}, get_practice_lesson("Lab 3", "Lọc các đơn hàng có giá trị > 1000.")]},
        {"day": 4, "title": "Hàm Aggregate", "lessons": [{"type": "Video", "title": "Thống kê dữ liệu", "url": "https://www.youtube.com/watch?v=mI2vFv_0v8k"}, get_practice_lesson("Lab 4", "Tính trung bình lương của phòng kế toán.")]},
        {"day": 5, "title": "GROUP BY", "lessons": [{"type": "Video", "title": "Nhóm dữ liệu", "url": "https://www.youtube.com/watch?v=B_9H7_K_P0A"}, get_practice_lesson("Lab 5", "Đếm số nhân viên của mỗi phòng ban.")]},
        {"day": 6, "title": "Kết nối INNER JOIN", "lessons": [{"type": "Video", "title": "Liên kết bảng", "url": "https://www.youtube.com/watch?v=9yeOJ0ZMUYw"}, get_practice_lesson("Lab 6", "Hiển thị tên khách hàng kèm mã đơn hàng.")]},
        {"day": 7, "title": "Thiết kế ERD", "lessons": [{"type": "Video", "title": "Cấu trúc Database", "url": "https://www.youtube.com/watch?v=Q5f7L5q9MvI"}, get_practice_lesson("Lab 7", "Phác thảo sơ đồ bảng cho app bán hàng.")]},
        {"day": 8, "title": "🚩 Checkpoint SQL", "lessons": [{"type": "Quiz", "title": "Bài thi cuối khóa", "test_id": "CH_DB"}]}
    ]
}

# --- NETWORK ---
NET_COURSE = {
    "course_id": "CRS_NET_BASIC", "skill_tag": "Network", "title": "🌐 Networking Essentials",
    "chapters": [
        {"day": 1, "title": "Mô hình OSI", "lessons": [{"type": "Video", "title": "Kiến thức 7 lớp OSI", "url": "https://www.youtube.com/watch?v=vv4y_uOneC0"}, get_practice_lesson("Lab 1", "Vẽ lại mô hình OSI.")]},
        {"day": 2, "title": "Địa chỉ IP", "lessons": [{"type": "Video", "title": "IPv4 & IPv6", "url": "https://www.youtube.com/watch?v=s_Ntt6eTn94"}, get_practice_lesson("Lab 2", "Xem địa chỉ IP máy tính đang dùng.")]},
        {"day": 3, "title": "DNS Server", "lessons": [{"type": "Video", "title": "Cơ chế phân giải tên miền", "url": "https://www.youtube.com/watch?v=27f_G_vS5W8"}, get_practice_lesson("Lab 3", "Dùng nslookup kiểm tra IP của google.com.")]},
        {"day": 4, "title": "TCP/IP Protocol", "lessons": [{"type": "Video", "title": "Giao thức truyền tin", "url": "https://www.youtube.com/watch?v=PpsEaqJV_A0"}, get_practice_lesson("Lab 4", "Phân biệt sự khác nhau giữa TCP và UDP.")]},
        {"day": 5, "title": "Router & Switch", "lessons": [{"type": "Video", "title": "Thiết bị mạng", "url": "https://www.youtube.com/watch?v=1z0ULvg_pW8"}, get_practice_lesson("Lab 5", "Vẽ sơ đồ kết nối mạng LAN đơn giản.")]},
        {"day": 6, "title": "Bảo mật & Firewall", "lessons": [{"type": "Video", "title": "Tường lửa mạng", "url": "https://www.youtube.com/watch?v=kDEX1HXybrU"}, get_practice_lesson("Lab 6", "Cách thức Firewall chặn dữ liệu độc hại.")]},
        {"day": 7, "title": "Mạng đám mây", "lessons": [{"type": "Video", "title": "Giới thiệu Cloud Network", "url": "https://www.youtube.com/watch?v=p9VfBvC_SRE"}, get_practice_lesson("Lab 7", "Tìm hiểu về VPC (Virtual Private Cloud).")]},
        {"day": 8, "title": "🚩 Checkpoint Network", "lessons": [{"type": "Quiz", "title": "Bài thi cuối khóa", "test_id": "CH_NET"}]}
    ]
}

# --- AGILE ---
AGILE_COURSE = {
    "course_id": "CRS_AGILE_PM", "skill_tag": "Agile", "title": "🚀 Agile & Scrum Professional",
    "chapters": [
        {"day": 1, "title": "Tư duy Agile", "lessons": [{"type": "Video", "title": "Triết lý Agile", "url": "https://www.youtube.com/watch?v=Z9QbYZh1YXY"}, get_practice_lesson("Lab 1", "Nêu 4 giá trị của tuyên ngôn Agile.")]},
        {"day": 2, "title": "Khung Scrum", "lessons": [{"type": "Video", "title": "Vận hành dự án Scrum", "url": "https://www.youtube.com/watch?v=9TycLR0TqFA"}, get_practice_lesson("Lab 2", "Vẽ vòng đời của 1 Sprint.")]},
        {"day": 3, "title": "Sự kiện Scrum", "lessons": [{"type": "Video", "title": "Họp kế hoạch & Retro", "url": "https://www.youtube.com/watch?v=S0TIDpT7GIs"}, get_practice_lesson("Lab 3", "Mô phỏng 1 buổi họp Daily Standup.")]},
        {"day": 4, "title": "User Story", "lessons": [{"type": "Video", "title": "Cách viết yêu cầu", "url": "https://www.youtube.com/watch?v=nm6pE6PzG-0"}, get_practice_lesson("Lab 4", "Viết User Story cho tính năng 'Thanh toán'.")]},
        {"day": 5, "title": "Ước lượng công việc", "lessons": [{"type": "Video", "title": "Story Points & Poker", "url": "https://www.youtube.com/watch?v=mD0iX2M5u_0"}, get_practice_lesson("Lab 5", "Dùng Fibonacci ước lượng 3 công việc.")]},
        {"day": 6, "title": "Kanban Board", "lessons": [{"type": "Video", "title": "Quản lý dòng chảy công việc", "url": "https://www.youtube.com/watch?v=iVaNWp_n7T4"}, get_practice_lesson("Lab 6", "Thiết lập bảng Todo - In Progress - Done.")]},
        {"day": 7, "title": "Hiệu suất dự án", "lessons": [{"type": "Video", "title": "Đo lường Velocity", "url": "https://www.youtube.com/watch?v=OThFmIdG8jE"}, get_practice_lesson("Lab 7", "Phân tích biểu đồ Burn-down Chart.")]},
        {"day": 8, "title": "🚩 Checkpoint Agile", "lessons": [{"type": "Quiz", "title": "Bài thi cuối khóa", "test_id": "CH_SE"}]}
    ]
}

def sync_data():
    client = get_connection()
    if not client: return
    print("⏳ Đang đồng bộ hóa Database với link Video chất lượng cao...")

    # Sync Questions
    try:
        ws_q = client.open("Ebsis_DB").worksheet("QUESTIONS")
        ws_q.clear()
        ws_q.append_row(["id", "skill_tag", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_opt"])
        ws_q.append_rows([[q['id'], q['skill_tag'], q['question_text'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_opt']] for q in RAW_QUESTIONS])
        print("✅ QUESTIONS: Cập nhật thành công.")
    except Exception as e: print(f"Lỗi QUESTIONS: {e}")

    # Sync Courses
    try:
        ws_c = client.open("Ebsis_DB").worksheet("COURSES")
        ws_c.clear()
        ws_c.append_row(["course_id", "skill_tag", "title", "data_json"])
        c_list = [PYTHON_COURSE, SQL_COURSE, NET_COURSE, AGILE_COURSE]
        ws_c.append_rows([[c['course_id'], c['skill_tag'], c['title'], json.dumps(c, ensure_ascii=False)] for c in c_list])
        print("✅ COURSES: Đầy đủ 4 môn x 8 ngày học.")
    except Exception as e: print(f"Lỗi COURSES: {e}")

if __name__ == "__main__":
    sync_data()