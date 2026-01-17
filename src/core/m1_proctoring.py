import sys
import os
import numpy as np
import cv2

# --- CẤU HÌNH ĐƯỜNG DẪN ĐỂ IMPORT MODULE KHÁC ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.db_connector import get_connection

# --- IMPORT FACE ENGINE (MEDIAPIPE) ---
try:
    from src.core.face_processor import FaceEngine
    face_engine = FaceEngine() # Khởi tạo engine ngay khi app chạy
    FACE_LIB_AVAILABLE = True
except ImportError as e:
    FACE_LIB_AVAILABLE = False
    print(f"⚠️ Lỗi import FaceEngine: {e}. Tính năng FaceID sẽ bị tắt.")

# =========================================================
# 1. LOGIC ĐĂNG NHẬP (MẬT KHẨU)
# =========================================================
def verify_login(student_id, password):
    """Kiểm tra ID/Pass với Google Sheet"""
    client = get_connection()
    if not client: return None
    
    try:
        sheet = client.open("Ebsis_DB").worksheet("USERS")
        users = sheet.get_all_records()
        
        for user in users:
            # So sánh chuỗi (xóa khoảng trắng thừa) để chính xác
            u_id = str(user.get('user_id', '')).strip()
            u_pass = str(user.get('password', '')).strip()
            
            if u_id == str(student_id).strip() and u_pass == str(password).strip():
                return user 
        return None
    except Exception as e:
        print(f"Lỗi verify_login: {e}")
        return None

# =========================================================
# 2. LOGIC TẠO TÀI KHOẢN MỚI (SIGN UP)
# =========================================================
def create_new_user(student_id, full_name, password):
    """Tạo user mới và lưu vào Sheet USERS"""
    client = get_connection()
    if not client: return False, "Lỗi kết nối Server"
    
    try:
        # Mở Sheet hoặc tạo nếu chưa có
        try: sheet = client.open("Ebsis_DB").worksheet("USERS")
        except: 
            sheet = client.open("Ebsis_DB").add_worksheet("USERS", 100, 5)
            sheet.append_row(["user_id", "full_name", "password", "role", "has_face_id"])
            
        # Kiểm tra trùng ID
        existing_ids = sheet.col_values(1)
        if str(student_id) in [str(x) for x in existing_ids]:
            return False, f"Mã sinh viên {student_id} đã tồn tại!"
            
        # --- QUAN TRỌNG: SẮP XẾP ĐÚNG CỘT ---
        # Sheet Header: user_id | full_name | password | role | has_face_id
        new_row = [
            str(student_id), 
            full_name,          # Tên nằm ở cột 2
            str(password),      # Pass nằm ở cột 3
            "Student", 
            "FALSE"
        ]
        sheet.append_row(new_row)
        
        return True, "Đăng ký thành công! Hãy đăng nhập ngay."
        
    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"

# =========================================================
# 3. ĐĂNG KÝ FACE ID (SỬ DỤNG FACE ENGINE MỚI)
# =========================================================
def register_face(user_id, image_file):
    if not FACE_LIB_AVAILABLE: return False, "Lỗi FaceEngine (Thiếu thư viện)."

    try:
        # 1. Xử lý ảnh bằng Engine mới (MediaPipe)
        img_rgb = face_engine.process_image(image_file)
        
        # 2. Lấy vector đặc trưng
        embedding = face_engine.get_face_embedding(img_rgb)
        
        if embedding is None:
            return False, "⚠️ Không tìm thấy khuôn mặt. Vui lòng nhìn thẳng camera, bỏ khẩu trang."
            
        # 3. Lưu file .npy vào thư mục data
        save_dir = 'data/face_encodings'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        np.save(f"{save_dir}/{user_id}.npy", embedding)
        
        # 4. Cập nhật trạng thái lên Google Sheet
        client = get_connection()
        if client:
            sheet = client.open("Ebsis_DB").worksheet("USERS")
            cell = sheet.find(str(user_id))
            if cell: 
                # Cập nhật cột 5 (has_face_id)
                sheet.update_cell(cell.row, 5, "TRUE")
            
        return True, "✅ Đăng ký khuôn mặt thành công!"
        
    except Exception as e:
        return False, f"Lỗi xử lý: {e}"

# =========================================================
# 4. ĐĂNG NHẬP FACE ID (CÓ KIỂM TRA GIAN LẬN)
# =========================================================
def login_with_face(image_file):
    if not FACE_LIB_AVAILABLE: return None, "Lỗi FaceEngine."

    try:
        # 1. Xử lý ảnh đầu vào
        img_rgb = face_engine.process_image(image_file)
        
        # 2. CHỐNG GIAN LẬN: Kiểm tra hướng nhìn (Head Pose)
        pose_status = face_engine.detect_head_pose(img_rgb)
        if "⚠️" in pose_status:
            return None, f"Phát hiện hành vi lạ: {pose_status}. Vui lòng nhìn thẳng!"

        # 3. Lấy vector input
        input_vector = face_engine.get_face_embedding(img_rgb)
        if input_vector is None: return None, "Không tìm thấy khuôn mặt."

        # 4. So sánh với kho dữ liệu đã lưu
        faces_dir = 'data/face_encodings'
        if not os.path.exists(faces_dir): return None, "Hệ thống chưa có dữ liệu khuôn mặt nào."

        found_id = None
        min_dist = 100.0 # Khởi tạo khoảng cách lớn nhất
        
        print("\n--- SO KHỚP KHUÔN MẶT ---")
        for f in os.listdir(faces_dir):
            if f.endswith('.npy'):
                try:
                    # Load vector của user đã đăng ký
                    saved_vector = np.load(os.path.join(faces_dir, f))
                    
                    # Tính khoảng cách Euclidean
                    dist = np.linalg.norm(saved_vector - input_vector)
                    print(f"User {f}: Dist={dist:.4f}")
                    
                    if dist < min_dist:
                        min_dist = dist
                        found_id = os.path.splitext(f)[0] # Lấy ID từ tên file
                except: continue
        
        # 5. Đánh giá kết quả
        # MediaPipe Vector thường có khoảng cách nhỏ hơn dlib.
        # Ngưỡng 0.5 là an toàn. Nếu muốn chặt hơn thì giảm xuống 0.3
        THRESHOLD = 0.5 
        
        print(f"--> Kết quả tốt nhất: {min_dist:.4f} (Ngưỡng {THRESHOLD})")

        if min_dist < THRESHOLD and found_id:
            # Tìm thông tin chi tiết trong Database
            client = get_connection()
            if client:
                sheet = client.open("Ebsis_DB").worksheet("USERS")
                users = sheet.get_all_records()
                for u in users:
                    if str(u.get('user_id', '')).strip() == found_id:
                        return u, "Thành công"
                        
        return None, "Khuôn mặt không khớp với dữ liệu đã đăng ký."

    except Exception as e: return None, f"Lỗi hệ thống: {e}"