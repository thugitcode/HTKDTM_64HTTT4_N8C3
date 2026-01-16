import pandas as pd
import streamlit as st
from src.services.db_connector import get_all_users
import numpy as np
import os
from src.core.face_processor import FaceEngine

# Khởi tạo bộ não xử lý ảnh
face_engine = FaceEngine()

def verify_login(username, password):
    """Hàm kiểm tra đăng nhập bằng mật khẩu"""
    df_users = get_all_users()
    if df_users.empty: return None

    user = df_users[df_users['user_id'].astype(str) == str(username)]
    if not user.empty:
        stored_password = str(user.iloc[0]['password'])
        if stored_password == str(password):
            return user.iloc[0].to_dict()
    return None

def register_face(user_id, image_file):
    """Hàm đăng ký khuôn mặt"""
    try:
        img_rgb = face_engine.process_image(image_file)
        vector = face_engine.get_face_embedding(img_rgb)
        
        if vector is None:
            return False, "⚠️ Không tìm thấy khuôn mặt! Hãy bỏ khẩu trang/kính và nhìn thẳng."
        
        save_path = f"data/face_encodings/{user_id}.npy"
        os.makedirs("data/face_encodings", exist_ok=True)
        np.save(save_path, vector)
        return True, "✅ Đăng ký khuôn mặt thành công!"
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"

def login_with_face(image_file):
    """
    Hàm đăng nhập bằng khuôn mặt (Đã nâng cấp logic kiểm tra)
    """
    # 1. Kiểm tra xem hệ thống đã có dữ liệu ai đăng ký chưa
    faces_dir = "data/face_encodings"
    if not os.path.exists(faces_dir) or not os.listdir(faces_dir):
        return None, "📂 Hệ thống chưa có dữ liệu khuôn mặt nào. Vui lòng đăng nhập bằng Mật khẩu và đăng ký trước."

    # 2. Xử lý ảnh đầu vào
    try:
        img_rgb = face_engine.process_image(image_file)
        current_embedding = face_engine.get_face_embedding(img_rgb)
    except Exception as e:
        return None, f"Lỗi xử lý ảnh: {e}"
        
    if current_embedding is None:
        return None, "⚠️ Không tìm thấy khuôn mặt trong camera."

    # 3. Lấy danh sách user từ DB
    df_users = get_all_users()
    
    # Biến lưu khoảng cách nhỏ nhất tìm được
    min_dist = 100.0
    found_user_id = None

    # 4. Quét tất cả các file khuôn mặt
    print("\n--- BẮT ĐẦU SO SÁNH KHUÔN MẶT ---")
    for filename in os.listdir(faces_dir):
        if filename.endswith(".npy"):
            saved_user_id = filename.split(".")[0]
            
            # Load vector đã lưu
            try:
                saved_embedding = np.load(os.path.join(faces_dir, filename))
                
                # Tính khoảng cách
                dist = np.linalg.norm(saved_embedding - current_embedding)
                print(f"So sánh với {saved_user_id}: Sai số = {dist:.4f}")
                
                # Cập nhật người giống nhất
                if dist < min_dist:
                    min_dist = dist
                    found_user_id = saved_user_id
            except:
                continue
    
    # 5. Đánh giá kết quả
    # Tăng ngưỡng chấp nhận lên 0.6 (trước là 0.1 quá thấp)
    THRESHOLD = 0.6 
    
    print(f"--> Kết quả: Min Dist = {min_dist:.4f} (Ngưỡng {THRESHOLD})")
    
    if min_dist < THRESHOLD and found_user_id:
        # Tìm thông tin user trong Database
        user = df_users[df_users['user_id'].astype(str) == str(found_user_id)]
        if not user.empty:
            return user.iloc[0].to_dict(), "Thành công"
        else:
            return None, f"Nhận diện được {found_user_id} nhưng không tìm thấy thông tin trong Database."
    
    # Trường hợp không khớp ai
    return None, "🚫 Khuôn mặt không khớp với dữ liệu đã đăng ký. Vui lòng thử lại hoặc dùng Mật khẩu."