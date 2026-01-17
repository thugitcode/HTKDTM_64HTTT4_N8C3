import streamlit as st
import time
from src.core.m1_proctoring import verify_login, login_with_face, create_new_user, register_face
from src.ui.styles import load_custom_css

def render_login_ui():
    """Hiển thị màn hình đăng nhập (Style mới)"""
    load_custom_css() # Kích hoạt giao diện đẹp
    
    # Tạo khoảng trống để đẩy nội dung xuống
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1]) # Căn giữa
    
    with col2:
        # Header dạng Card
        st.markdown("""
        <div class="st-card" style="text-align: center;">
            <h1 style="color: #2563EB; margin-bottom: 0;">🎓 EBSIS</h1>
            <p style="color: #64748B; margin-top: 5px;">Hệ thống Đào tạo & Giám sát Thông minh</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_face, tab_signup = st.tabs(["🔑 Đăng nhập", "📸 FaceID", "📝 Đăng ký"])
        
        # --- TAB 1: LOGIN ---
        with tab_login:
            st.markdown('<div class="st-card">', unsafe_allow_html=True)
            u = st.text_input("Mã sinh viên", placeholder="Ví dụ: SV001")
            p = st.text_input("Mật khẩu", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 TRUY CẬP HỆ THỐNG", use_container_width=True, type="primary"):
                user = verify_login(u, p)
                if user: return user
                else: st.error("❌ Thông tin không chính xác")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: FACE ID ---
        with tab_face:
            st.markdown('<div class="st-card" style="text-align: center;">', unsafe_allow_html=True)
            st.info("💡 Hướng mặt về phía camera")
            img = st.camera_input("FaceID Login", label_visibility="collapsed")
            
            if img:
                with st.spinner("🔄 Đang quét sinh trắc học..."):
                    user, msg = login_with_face(img)
                    if user: return user
                    else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 3: SIGN UP ---
        with tab_signup:
            st.markdown('<div class="st-card">', unsafe_allow_html=True)
            st.markdown("**Tạo tài khoản mới**")
            new_id = st.text_input("Mã SV mới")
            new_name = st.text_input("Họ và tên đầy đủ")
            new_pass = st.text_input("Mật khẩu mới", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("✨ TẠO TÀI KHOẢN", use_container_width=True):
                if not new_id or not new_name or not new_pass:
                    st.error("Vui lòng điền đủ thông tin!")
                else:
                    ok, msg = create_new_user(new_id, new_name, new_pass)
                    if ok: st.success(msg)
                    else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    return None

def render_register_face_ui(user):
    """
    Giao diện đăng ký khuôn mặt (Style mới)
    Đây là hàm bị thiếu trước đó
    """
    load_custom_css()
    
    st.markdown("""
    <div class="exam-header-container">
        <h2>🔐 QUẢN LÝ SINH TRẮC HỌC</h2>
        <p>Dữ liệu khuôn mặt dùng để đăng nhập và giám sát thi cử</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.info("📸 **Lưu ý:** Tháo khẩu trang, kính râm. Đảm bảo ánh sáng tốt.")
        
        # Camera chụp ảnh mẫu
        img = st.camera_input("Chụp ảnh mẫu", label_visibility="collapsed")
        
        if img:
            with st.spinner("Đang trích xuất vector khuôn mặt..."):
                ok, msg = register_face(user['user_id'], img)
                if ok: 
                    st.success(msg)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
                
    with c2:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.subheader("Thông tin")
        st.write(f"**Sinh viên:** {user['full_name']}")
        st.write(f"**Mã SV:** {user['user_id']}")
        st.divider()
        
        # Kiểm tra trạng thái FaceID (từ string 'TRUE'/'FALSE' trong sheet)
        has_face = str(user.get('has_face_id', 'FALSE')).upper() == 'TRUE'
        
        if has_face:
            st.markdown('<div class="badge badge-success" style="text-align:center">✅ ĐÃ ĐĂNG KÝ FACE ID</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge badge-danger" style="text-align:center">⚠️ CHƯA CÓ DỮ LIỆU</div>', unsafe_allow_html=True)
            
        st.caption("Dữ liệu được mã hóa chuẩn AES-256.")
        st.markdown('</div>', unsafe_allow_html=True)