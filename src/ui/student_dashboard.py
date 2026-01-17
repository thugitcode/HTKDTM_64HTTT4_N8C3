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
    
    # ÉP KIỂU DỮ LIỆU AN TOÀN (Bổ sung xử lý lỗi dữ liệu trống hoặc sai định dạng)
    try:
        # Lấy giá trị, ép về float trước rồi mới về int để tránh lỗi chuỗi "3.0"
        cur_ch = int(float(progress.get('current_chapter', 0)))
        score = int(float(progress.get('score', 0)))
        cheat = int(float(progress.get('cheat_count', 0)))
    except (ValueError, TypeError):
        # Nếu dữ liệu lỗi, mặc định về 0
        cur_ch, score, cheat = 0, 0, 0

    # TÍNH TOÁN TIẾN ĐỘ CHUẨN BA
    # Nếu cur_ch = 3 (xong 3 bài), thì chương đang học là 4. 
    # Nhưng KPI "Chương" thường nên hiển thị số chương đã HOÀN THÀNH.
    completion = int((cur_ch / 8) * 100) if cur_ch > 0 else 0
    
    with col1: st.metric("Tiến độ", f"{completion}%")
    with col2: st.metric("Điểm thi", f"{score}%")
    with col3: st.metric("Chương", f"{cur_ch}/8")
    with col4: st.metric("Vi phạm", f"{cheat} lần", delta_color="inverse")

    # Thanh tiến độ trực quan
    st.progress(min(completion / 100, 1.0))
    st.markdown(f"<p style='text-align: right; color: gray; font-size: 0.8rem;'>Đã hoàn thành {cur_ch} trên tổng số 8 chương học</p>", unsafe_allow_html=True)

    st.divider()

    # --- Hàng 2: Biểu đồ & Huy hiệu ---
    c_chart, c_badge = st.columns([2, 1])
    with c_chart:
        st.subheader("📈 Phân tích năng lực chuyên sâu")
        
        # Tạo dữ liệu cho phân tích năng lực đa chiều
        skill_data = pd.DataFrame({
            "Kỹ năng": ["Phân tích", "Kỹ thuật", "Thái độ", "Tương tác AI", "Tiến độ"],
            "Điểm": [score, 75, max(0, 100 - (cheat * 10)), 85, completion]
        })
        
        # Hiển thị biểu đồ cột cho năng lực
        st.bar_chart(skill_data.set_index("Kỹ năng"), color="#1E3A8A")
        
        # [BỔ SUNG] Chú thích cho BA
        st.caption("ℹ️ Chỉ số 'Thái độ' được tính dựa trên số lần vi phạm trong quá trình kiểm tra.")

    with c_badge:
        st.subheader("🏅 Huy hiệu đạt được")
        if cur_ch >= 1: st.success("✅ Đã nhập môn")
        else: st.write("⚪ *Chưa đạt: Đã nhập môn*")
            
        if cur_ch >= 4: st.warning("🔥 Vượt nửa chặng đường")
        else: st.write("⚪ *Chưa đạt: Vượt nửa chặng đường*")
            
        if cur_ch >= 8: st.info("🎓 Tân cử nhân Ebsis")
        else: st.write("⚪ *Chưa đạt: Tân cử nhân Ebsis*")

    # --- [THÊM MỚI] Hàng 3: Nhật ký học tập chi tiết (Fix lỗi không lưu bài) ---
    st.divider()
    st.subheader("🕒 Nhật ký hoạt động chi tiết")
    
    log_data = progress.get('violation_details', '[]')
    try:
        # Nếu log_data là chuỗi JSON, parse nó ra. Nếu là list thì dùng luôn.
        if isinstance(log_data, str):
            logs = json.loads(log_data) if log_data != "" else []
        else:
            logs = log_data
            
        if logs:
            # Sắp xếp log mới nhất lên đầu
            df_logs = pd.DataFrame(logs)
            if "Thời gian" in df_logs.columns:
                # Hiển thị dạng bảng chuyên nghiệp
                st.table(df_logs.sort_index(ascending=False).head(10))
            else:
                st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("Chưa có lịch sử thao tác được ghi nhận. Hệ thống sẽ tự động cập nhật khi bạn hoàn thành bài học.")
    except Exception as e:
        st.error(f"⚠️ Lỗi hiển thị nhật ký: {e}")

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
                    if update_user_profile_db(user_id, new_name, new_major, new_email):
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



def render_transcript_tab(user_id):
    st.subheader("📜 Bảng điểm & Thành tựu")
    
    # Lấy dữ liệu từ Sheets (Sử dụng cache để tăng tốc)
    from src.core.m2_adaptive import get_connection
    client = get_connection()
    db = client.open("Ebsis_DB")
    ws_history = db.worksheet("HISTORY")
    
    # Filter dữ liệu của user
    history_records = ws_history.get_all_records()
    my_history = [r for r in history_records if str(r['user_id']) == str(user_id)]
    
    if not my_history:
        st.info("Bạn chưa hoàn thành khóa học nào.")
    else:
        for item in my_history:
            with st.expander(f"📘 {item['course_id']} - Hoàn thành ngày {item['completion_date'][:10]}"):
                c1, c2 = st.columns(2)
                c1.metric("Kết quả", f"{item['score']}%")
                c2.write(f"**Trạng thái:** {item['status']}")
                if st.button("👁️ Xem lại tài liệu", key=f"rev_{item['course_id']}"):
                    st.session_state['view_mode'] = 'read_only'
                    st.session_state['target_course'] = item['course_id']
                    st.rerun()