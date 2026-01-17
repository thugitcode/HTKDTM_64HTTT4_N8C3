import streamlit as st
import sys
import os

# 1. CẤU HÌNH APP
st.set_page_config(page_title="Ebsis - Intelligent Learning", page_icon="🎓", layout="wide")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. IMPORT GIAO DIỆN & LOGIC
from src.ui.login_ui import render_login_ui, render_register_face_ui
from src.ui.adaptive_ui import render_adaptive_ui
from src.ui.student_dashboard import render_student_dashboard_page, render_student_profile_page
from src.core.m2_adaptive import get_user_progress

# 3. QUẢN LÝ TRẠNG THÁI
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

def main():
    user = st.session_state['user_info']

    # --- TRẠNG THÁI 1: CHƯA ĐĂNG NHẬP ---
    if not user:
        logged_in_user = render_login_ui()
        if logged_in_user:
            st.session_state['user_info'] = logged_in_user
            st.rerun()
            
    # --- TRẠNG THÁI 2: ĐÃ ĐĂNG NHẬP ---
    else:
        # Sidebar chung duy nhất của toàn hệ thống
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
            st.write(f"Xin chào, **{user['full_name']}**")
            st.caption(f"Vai trò: {user.get('role', 'Sinh viên')}")
            st.divider()
            
            # CẤU TRÚC MENU PHẲNG: Không lồng menu con vào menu cha
            menu = st.radio(
                "Menu chính", 
                ["🏠 Dashboard", "🧠 Học tập (LMS)", "👤 Hồ sơ cá nhân", "🔐 Quản lý FaceID", "📊 Báo cáo"],
                index=0,
                key="main_app_navigation"
            )
            
            st.divider()
            if st.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        # --- ĐIỀU HƯỚNG NỘI DUNG CHÍNH ---
        user_id = user.get('user_id')
        
        if menu == "🏠 Dashboard":
            # Gọi trực tiếp Dashboard xịn (Thẻ KPI màu + Biểu đồ)
            current_progress = get_user_progress(user_id)
            render_student_dashboard_page(user_id, current_progress)
            
        elif menu == "🧠 Học tập (LMS)":
            # Gọi logic học tập (File này đã được xóa Sidebar thừa bên dưới)
            render_adaptive_ui()
            
        elif menu == "👤 Hồ sơ cá nhân":
            render_student_profile_page()
            
        elif menu == "🔐 Quản lý FaceID":
            render_register_face_ui(user)
            
        elif menu == "📊 Báo cáo":
            st.title("📊 Analytics Dashboard")
            st.info("Tính năng phân tích tiến độ đang được phát triển...")

if __name__ == "__main__":
    main()