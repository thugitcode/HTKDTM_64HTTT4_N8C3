import streamlit as st
import time
from src.core.m1_proctoring import verify_login, login_with_face, create_new_user, register_face
from src.ui.styles import load_custom_css

def render_login_ui():
    """Hiển thị màn hình đăng nhập (Sử dụng cơ chế Radio-Tabs để ép chuyển trang)"""
    load_custom_css() 
    
    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- BƯỚC 1: QUẢN LÝ TRẠNG THÁI ACTIVE ---
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "🔐 ĐĂNG NHẬP"

    col1, col2, col3 = st.columns([1, 1.2, 1]) 
    
    with col2:
        st.markdown("""
        <div class="st-card" style="text-align: center;">
            <h1 style="color: #2563EB; margin-bottom: 0;">🎓 EBSIS</h1>
            <p style="color: #64748B; margin-top: 5px;">Hệ thống Đào tạo & Giám sát Thông minh</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- BƯỚC 2: GIẢ LẬP TABS BẰNG RADIO (NGÀI ĐIỀU HƯỚNG) ---
        # Giao diện này nhìn vẫn chuyên nghiệp nhưng kiểm soát được index 100%
        mode = st.radio(
            "Chọn hình thức",
            ["🔐 ĐĂNG NHẬP", "📸 FACE ID", "📝 ĐĂNG KÝ"],
            index=["🔐 ĐĂNG NHẬP", "📸 FACE ID", "📝 ĐĂNG KÝ"].index(st.session_state["auth_mode"]),
            horizontal=True,
            label_visibility="collapsed"
        )
        # Cập nhật ngược lại session_state khi người dùng click tay
        st.session_state["auth_mode"] = mode

        st.divider()

        # --- TAB 1: LOGIN ---
        if mode == "🔐 ĐĂNG NHẬP":
            st.markdown('<div class="st-card">', unsafe_allow_html=True)
            u = st.text_input("Mã sinh viên", placeholder="Ví dụ: SV001", key="login_user")
            p = st.text_input("Mật khẩu", type="password", key="login_pass")
            
            if st.button("🚀 TRUY CẬP HỆ THỐNG", use_container_width=True, type="primary"):
                user = verify_login(u, p)
                if user: return user
                else: st.error("❌ Thông tin không chính xác")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: FACE ID ---
        elif mode == "📸 FACE ID":
            st.markdown('<div class="st-card" style="text-align: center;">', unsafe_allow_html=True)
            st.info("💡 Hướng mặt về phía camera")
            img = st.camera_input("FaceID Login", label_visibility="collapsed", key="face_cam_login")
            
            if img:
                with st.spinner("🔄 Đang quét sinh trắc học..."):
                    user, msg = login_with_face(img)
                    if user: return user
                    else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 3: SIGN UP (ÉP CHUYỂN HƯỚNG THÀNH CÔNG) ---
        elif mode == "📝 ĐĂNG KÝ":
            st.markdown('<div class="st-card">', unsafe_allow_html=True)
            st.markdown("**Tạo tài khoản mới**")
            new_id = st.text_input("Mã SV mới", key="reg_id")
            new_name = st.text_input("Họ và tên đầy đủ", key="reg_name")
            new_pass = st.text_input("Mật khẩu mới", type="password", key="reg_pass")
            
            if st.button("✨ TẠO TÀI KHOẢN", use_container_width=True):
                if not new_id or not new_name or not new_pass:
                    st.error("Vui lòng điền đủ thông tin!")
                else:
                    with st.spinner("Đang khởi tạo hồ sơ..."):
                        ok, msg = create_new_user(new_id, new_name, new_pass)
                        if ok: 
                            st.success(f"🎉 {msg}")
                            st.toast("Đang chuyển sang đăng nhập...", icon="🔐")
                            
                            # --- ĐOẠN THEN CHỐT ---
                            # 1. Ép biến auth_mode về Đăng nhập
                            st.session_state["auth_mode"] = "🔐 ĐĂNG NHẬP"
                            
                            # 2. Xóa các key nhập liệu để reset form
                            for k in ["reg_id", "reg_name", "reg_pass"]:
                                if k in st.session_state: del st.session_state[k]
                            
                            # 3. Chờ 1.5s và rerun. Lần này radio sẽ bị ép về index 0
                            time.sleep(1.5)
                            st.rerun()
                        else: 
                            st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    return None

def render_register_face_ui(user):
    """
    Giao diện đăng ký khuôn mặt (Style mới)
    Fix lỗi: Đăng ký thành công nhưng Badge vẫn hiện màu đỏ
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
        img = st.camera_input("Chụp ảnh mẫu", label_visibility="collapsed", key="face_reg_cam")
        
        if img:
            with st.spinner("Đang trích xuất vector khuôn mặt..."):
                ok, msg = register_face(user['user_id'], img)
                if ok: 
                    st.success(msg)
                    
                    # --- ĐOẠN FIX THEN CHỐT ---
                    # Cập nhật trực tiếp vào session_state để Badge ở cột bên phải đổi màu ngay
                    if 'user_info' in st.session_state:
                        st.session_state['user_info']['has_face_id'] = 'TRUE'
                    
                    st.balloons()
                    time.sleep(2) # Đợi 2 giây để thấy thông báo thành công
                    st.rerun()    # Ép trang load lại để nhận diện has_face_id mới
                else: 
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
                
    with c2:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.subheader("Thông tin")
        st.write(f"**Sinh viên:** {user['full_name']}")
        st.write(f"**Mã SV:** {user['user_id']}")
        st.divider()
        
        # --- LOGIC HIỂN THỊ BADGE (LUÔN ĐỌC TỪ SESSION MỚI NHẤT) ---
        # Ép kiểu string và viết hoa để so sánh chính xác với "TRUE" trong Google Sheets
        current_status = str(st.session_state.get('user_info', {}).get('has_face_id', 'FALSE')).upper()
        
        if current_status == 'TRUE':
            st.markdown("""
                <div style="background-color:#dcfce7; color:#166534; padding:15px; border-radius:10px; text-align:center; font-weight:bold; border: 2px solid #22c55e;">
                    ✅ ĐÃ ĐĂNG KÝ FACE ID
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color:#fee2e2; color:#991b1b; padding:15px; border-radius:10px; text-align:center; font-weight:bold; border: 2px solid #ef4444;">
                    ⚠️ CHƯA CÓ DỮ LIỆU HÌNH ẢNH
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔒 Dữ liệu được mã hóa và lưu trữ bảo mật.")
        st.markdown('</div>', unsafe_allow_html=True)