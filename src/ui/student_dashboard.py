import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

def render_student_dashboard_page(user_id, progress):
    """Trang Dashboard tổng quan với các thẻ KPI và biểu đồ"""
    user = st.session_state.get('user_info', {})
    
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; margin-bottom: 25px;">
            <h1 style="margin:0; font-size: 26px;">📊 Tổng quan hệ thống</h1>
            <p style="margin:5px 0 0 0; opacity: 0.9;">Chào mừng trở lại Ebsis, <b>{user.get('full_name', 'Học viên')}</b>!</p>
        </div>
    """, unsafe_allow_html=True)

    if not progress:
        st.info("💡 Bạn chưa có dữ liệu học tập. Hãy bắt đầu bài kiểm tra năng lực để kích hoạt lộ trình!"); return

    # --- Hàng 1: Thẻ KPI (Metrics) ---
    col1, col2, col3, col4 = st.columns(4)
    cur_ch = int(progress.get('current_chapter', 0))
    completion = int((cur_ch / 8) * 100) 
    
    with col1: st.metric("Tiến độ", f"{completion}%")
    with col2: st.metric("Điểm thi", f"{progress.get('score', 0)}%")
    with col3: st.metric("Chương", f"{cur_ch}/8")
    with col4: st.metric("Vi phạm", f"{progress.get('cheat_count', 0)} lần", delta_color="inverse")

    st.divider()

    # --- Hàng 2: Biểu đồ & Huy hiệu ---
    c_chart, c_badge = st.columns([2, 1])
    with c_chart:
        st.subheader("📈 Phân tích năng lực")
        skill_data = pd.DataFrame({
            "Kỹ năng": ["Phân tích", "Kỹ thuật", "Thái độ", "Tương tác AI", "Tiến độ"],
            "Điểm": [progress.get('score', 0), 75, 100 - (int(progress.get('cheat_count', 0))*10), 85, completion]
        })
        st.bar_chart(skill_data.set_index("Kỹ năng"))

    with c_badge:
        st.subheader("🏅 Huy hiệu đạt được")
        if cur_ch >= 1: st.success("✅ Đã nhập môn")
        if cur_ch >= 4: st.warning("🔥 Vượt nửa chặng đường")
        if cur_ch >= 8: st.info("🎓 Tân cử nhân Ebsis")

def render_student_profile_page():
    """Trang thông tin cá nhân hỗ trợ Chỉnh sửa trực tiếp"""
    st.header("👤 Hồ sơ cá nhân")
    
    # Khởi tạo trạng thái chỉnh sửa nếu chưa có
    if 'editing_profile' not in st.session_state:
        st.session_state['editing_profile'] = False

    user = st.session_state.get('user_info', {})
    user_id = user.get('user_id', 'N/A')

    # --- CHẾ ĐỘ CHỈNH SỬA ---
    if st.session_state['editing_profile']:
        with st.form("edit_profile_form"):
            st.subheader("📝 Chỉnh sửa thông tin")
            new_name = st.text_input("Họ và tên", value=user.get('full_name', ''))
            new_email = st.text_input("Email", value=user.get('email', ''))
            new_major = st.selectbox("Chuyên ngành", 
                                    ["Hệ thống thông tin (BA)", "Công nghệ thông tin", "Quản trị kinh doanh"],
                                    index=0)
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True):
                    from src.core.m2_adaptive import update_user_profile_db
                    # Gọi hàm update với đầy đủ tham số
                    if update_user_profile_db(user_id, new_name, new_major, new_email):
                        # Cập nhật Session State cục bộ
                        st.session_state['user_info']['full_name'] = new_name
                        st.session_state['user_info']['email'] = new_email
                        st.session_state['user_info']['major'] = new_major
                        
                        st.success("✅ Đã cập nhật hồ sơ thành công!")
                        st.session_state['editing_profile'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Lỗi kết nối Database.")
            
            with col_cancel:
                if st.form_submit_button("❌ Hủy", use_container_width=True):
                    st.session_state['editing_profile'] = False
                    st.rerun()

    # --- CHẾ ĐỘ HIỂN THỊ ---
    else:
        with st.container(border=True):
            col_img, col_txt = st.columns([1, 3])
            with col_img:
                # Avatar mặc định chuyên nghiệp
                st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
            with col_txt:
                st.subheader(user.get('full_name', 'Học viên'))
                st.write(f"📧 **Email:** {user.get('email', 'Chưa cập nhật')}")
                st.write(f"🆔 **Mã sinh viên:** `{user_id}`")
                st.write(f"🏫 **Chuyên ngành:** {user.get('major', 'Hệ thống thông tin (BA)')}")
                
        if st.button("🔄 Cập nhật thông tin", type="primary"):
            st.session_state['editing_profile'] = True
            st.rerun()
            
    st.divider()
    
    # --- CÀI ĐẶT TÀI KHOẢN ---
    st.subheader("⚙️ Cài đặt học tập")
    
    # Lưu cài đặt vào session để duy trì trạng thái
    email_notif = st.toggle("Nhận thông báo bài học qua Email", 
                             value=st.session_state.get('email_notif', True))
    camera_sec = st.toggle("Chế độ bảo mật Camera nâng cao (AI Proctoring)", 
                            value=st.session_state.get('camera_sec', True))
    
    # Cập nhật session khi người dùng thay đổi
    st.session_state['email_notif'] = email_notif
    st.session_state['camera_sec'] = camera_sec

    if st.button("💾 Lưu cài đặt hệ thống"):
        st.toast("Đã ghi nhận cấu hình hệ thống!")