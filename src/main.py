import streamlit as st
import sys
import os
import time
import pandas as pd
import json
from datetime import datetime

# Thêm vào ngay sau phần import
if "db_client" not in st.session_state:
    from src.services.db_connector import get_connection
    st.session_state.db_client = get_connection()
    
# 1. CẤU HÌNH APP
st.set_page_config(page_title="Ebsis - Intelligent Learning", page_icon="🎓", layout="wide")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. IMPORT GIAO DIỆN & LOGIC
from src.ui.login_ui import render_login_ui, render_register_face_ui
from src.ui.adaptive_ui import render_adaptive_ui
from src.ui.student_dashboard import render_student_dashboard_page, render_student_profile_page
from src.core.m2_adaptive import get_user_progress
from src.core.m1_proctoring import verify_login # Import thêm để khôi phục session

# 3. QUẢN LÝ TRẠNG THÁI
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

# --- [BỔ SUNG] LOGIC KHÔI PHỤC SESSION KHI F5 ---
if st.session_state['user_info'] is None:
    # Kiểm tra xem trên thanh địa chỉ có ID người dùng không
    params = st.query_params
    if "uid" in params:
        user_id_saved = params["uid"]
        # Gọi Database lấy lại thông tin user mà không bắt nhập pass lại
        with st.spinner("Đang khôi phục phiên làm việc..."):
            from src.services.db_connector import get_connection
            client = get_connection()
            if client:
                sheet = client.open("Ebsis_DB").worksheet("USERS")
                records = sheet.get_all_records()
                for r in records:
                    if str(r.get('user_id')) == str(user_id_saved):
                        st.session_state['user_info'] = r
                        break

def main():
    user = st.session_state['user_info']

    # --- TRẠNG THÁI 1: CHƯA ĐĂNG NHẬP ---
    if not user:
        logged_in_user = render_login_ui()
        if logged_in_user:
            st.session_state['user_info'] = logged_in_user
            # [BỔ SUNG] Ghim ID lên URL để F5 không bị mất
            st.query_params["uid"] = logged_in_user['user_id']
            st.rerun()
            
    # --- TRẠNG THÁI 2: ĐÃ ĐĂNG NHẬP ---
    else:
        # Sidebar chung duy nhất của toàn hệ thống
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
            st.write(f"Xin chào, **{user['full_name']}**")
            st.caption(f"Vai trò: {user.get('role', 'Sinh viên')}")
            st.divider()
            
            # CẤU TRÚC MENU PHẲNG
            menu = st.radio(
                "Menu chính", 
                ["🏠 Dashboard", "🧠 Học tập (LMS)", "👤 Hồ sơ cá nhân", "🔐 Quản lý FaceID", "📊 Báo cáo"],
                index=0,
                key="main_app_navigation"
            )
            
            st.divider()
            if st.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.clear()
                # [BỔ SUNG] Xóa ID trên URL khi đăng xuất
                st.query_params.clear()
                st.rerun()

        # --- ĐIỀU HƯỚNG NỘI DUNG CHÍNH ---
        user_id = user.get('user_id')
        
        if menu == "🏠 Dashboard":
            # [BỔ SUNG QUAN TRỌNG] - Luôn lấy dữ liệu mới nhất từ DB khi vào Dashboard
            with st.spinner("Đang cập nhật tiến độ mới nhất..."):
                current_progress = get_user_progress(user_id)
            
            render_student_dashboard_page(user_id, current_progress)
            
        elif menu == "🧠 Học tập (LMS)":
            render_adaptive_ui()
            
        elif menu == "👤 Hồ sơ cá nhân":
            render_student_profile_page()
            
        elif menu == "🔐 Quản lý FaceID":
            render_register_face_ui(user)
            
        elif menu == "📊 Báo cáo":
            # --- [HOÀN THIỆN NÂNG CAO] TRUNG TÂM PHÂN TÍCH ---
            st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; color: white; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                    <h1 style="margin:0; font-size: 2.5rem;">📊 INSIGHTS DASHBOARD</h1>
                    <p style="margin:5px 0 0 0; opacity:0.9; font-size: 1.1rem;">Phân tích sâu lộ trình học tập và chỉ số tư duy của sinh viên</p>
                </div>
            """, unsafe_allow_html=True)

            with st.spinner("Đang tổng hợp dữ liệu..."):
                current_progress = get_user_progress(user_id)
                
            if current_progress:
                # 1. THÔNG SỐ TỔNG QUAN (KPIs nâng cao)
                c1, c2, c3, c4 = st.columns(4)
                score = current_progress.get('score', 0)
                chap = int(float(current_progress.get('current_chapter', 0)))
                cheats = current_progress.get('cheat_count', 0)

                with c1:
                    st.metric("Hệ số năng lực", f"{score}%", delta=f"{score-50}%" if score > 50 else f"{score-50}%")
                with c2:
                    st.metric("Độ phủ lộ trình", f"{(chap/8)*100:.1f}%", f"{chap}/8 Bài")
                with c3:
                    st.metric("Chỉ số trung thực", f"{max(0, 100 - (cheats*10))}%", delta=f"-{cheats} lỗi", delta_color="inverse")
                with c4:
                    status = "🎓 ĐỦ ĐIỀU KIỆN" if score >= 80 and chap >= 8 else "⏳ ĐANG TÍCH LŨY"
                    st.metric("Trạng thái", status)

                st.divider()

                # 2. PHÂN TÍCH TRỰC QUAN ĐA CHIỀU
                col_left, col_right = st.columns([1.5, 1])
                
                with col_left:
                    st.subheader("🎯 Bản đồ Kỹ năng Mục tiêu")
                    # Tích hợp biểu đồ Radar mô phỏng (Dùng line_chart để thể hiện xu hướng năng lực)
                    if 'exam_result' in st.session_state and st.session_state['exam_result']:
                        res = st.session_state['exam_result']
                        df_radar = pd.DataFrame({
                            'Kỹ năng': list(res['skill_breakdown'].keys()),
                            'Hiện tại': [s['score'] for s in res['skill_breakdown'].values()]
                        })
                        st.line_chart(df_radar.set_index('Kỹ năng'))
                    else:
                        st.info("💡 Chưa có dữ liệu bài test. Hiển thị phân tích kỹ năng BA tiêu chuẩn:")
                        df_target = pd.DataFrame({
                            "Kỹ năng": ["SQL Query", "BPMN Process", "SRS Documentation", "Logic Flow", "UI/UX"],
                            "Mức độ (%)": [score, score-10, 50, score+5, 40]
                        }).set_index("Kỹ năng")
                        st.bar_chart(df_target)

                with col_right:
                    st.subheader("🛡️ Nhật ký Giám sát & Rủi ro")
                    try:
                        raw_logs = current_progress.get('violation_details', '[]')
                        logs = json.loads(raw_logs) if isinstance(raw_logs, str) else raw_logs
                        
                        if logs and len(logs) > 0:
                            df_logs = pd.DataFrame(logs)
                            st.dataframe(df_logs, use_container_width=True, hide_index=True)
                        else:
                            st.success("🌟 Hồ sơ sạch: AI không phát hiện hành vi gian lận.")
                            st.progress(100)
                            st.caption("Điểm tin cậy: Tuyệt đối")
                    except Exception as e:
                        st.write("Dữ liệu log đang đồng bộ...")

                # 3. ACTIONABLE INSIGHTS (Gợi ý hành động thực tế)
                st.divider()
                st.subheader("🤖 Chiến lược phát triển từ Trợ lý EBSIS")
                
                tab_advice, tab_roadmap = st.tabs(["💬 Nhận xét chuyên sâu", "🛣️ Lộ trình đề xuất"])
                
                with tab_advice:
                    with st.container(border=True):
                        if score >= 80:
                            st.balloons()
                            st.markdown("### ✅ Đánh giá: **XUẤT SẮC (Top 5%)**")
                            st.write(f"Dựa trên dữ liệu học tập, bạn có khả năng tư duy hệ thống (Systems Thinking) vượt trội. Bạn nên bắt đầu tìm hiểu về **System Design** và **Cloud Architecture**.")
                        elif score >= 50:
                            st.markdown("### 📈 Đánh giá: **TIỀM NĂNG**")
                            st.write(f"Tiến độ {chap}/8 chương cho thấy bạn rất kiên trì. Tuy nhiên, để tối ưu điểm số, hãy sử dụng tính năng 'Sandbox' để thực hành nhiều hơn các câu lệnh SQL nâng cao.")
                        else:
                            st.markdown("### ⚠️ Đánh giá: **CẦN HỖ TRỢ**")
                            st.error("Hệ thống nhận thấy bạn đang gặp nút thắt ở phần Business Logic. Đề xuất: Liên hệ Tutor AI để được giải thích lại Ngày 3 & 4.")

                with tab_roadmap:
                    st.write("Dựa trên Profile của bạn, đây là 3 kỹ năng cần 'Unlock' tiếp theo:")
                    st.markdown("- 🔓 **Level 1:** Hoàn thiện sơ đồ BPMN cho dự án HRM.")
                    st.markdown("- 🔒 **Level 2:** Viết tài liệu SRS cho Module thanh toán.")
                    st.markdown("- 🔒 **Level 3:** Triển khai GenAI tích hợp Google Maps API.")

            else:
                st.warning("⚠️ Hệ thống chưa tìm thấy dữ liệu. Hãy hoàn thành bài đánh giá năng lực để khởi tạo báo cáo chi tiết!")

if __name__ == "__main__":
    main()