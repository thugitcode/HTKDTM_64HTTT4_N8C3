import streamlit as st
import sys
import os
import time
import pandas as pd
import json
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- KHỞI TẠO KẾT NỐI DB ---
if "db_client" not in st.session_state:
    from src.services.db_connector import get_connection
    try:
        st.session_state.db_client = get_connection()
    except:
        st.session_state.db_client = None
    
# 1. CẤU HÌNH APP
st.set_page_config(page_title="Ebsis - Intelligent Learning", page_icon="🎓", layout="wide")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. IMPORT GIAO DIỆN & LOGIC
from services.email_service import generate_insight_pdf
from src.ui.login_ui import render_login_ui, render_register_face_ui
from src.ui.adaptive_ui import render_adaptive_ui
from src.ui.student_dashboard import render_student_dashboard_page, render_student_profile_page
from src.core.m2_adaptive import get_user_progress
from src.core.m1_proctoring import verify_login

# --- HÀM GHI LOG HOẠT ĐỘNG ---
def save_activity_log(user_id, name, action):
    try:
        client = st.session_state.db_client
        if client:
            sheet = client.open("Ebsis_DB").worksheet("LOGS")
            now = datetime.now()
            new_log = [
                str(user_id), name, action,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d"), now.hour
            ]
            sheet.append_row(new_log)
    except:
        pass

# 3. QUẢN LÝ TRẠNG THÁI SESSION
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

# --- LOGIC KHÔI PHỤC SESSION KHI F5 ---
if st.session_state['user_info'] is None:
    params = st.query_params
    if "uid" in params:
        user_id_saved = params["uid"]
        with st.spinner("Đang khôi phục phiên làm việc..."):
            from src.services.db_connector import get_connection
            client = get_connection()
            if client:
                sheet = client.open("Ebsis_DB").worksheet("USERS")
                records = sheet.get_all_records()
                for r in records:
                    if str(r.get('user_id')) == str(user_id_saved):
                        st.session_state['user_info'] = r
                        save_activity_log(r['user_id'], r['full_name'], "Auto-Login (F5)")
                        break

def main():
    user = st.session_state['user_info']

    # --- TRẠNG THÁI 1: CHƯA ĐĂNG NHẬP ---
    if not user:
        logged_in_user = render_login_ui()
        if logged_in_user:
            st.session_state['user_info'] = logged_in_user
            st.query_params["uid"] = logged_in_user['user_id']
            save_activity_log(logged_in_user['user_id'], logged_in_user['full_name'], "Login Success")
            st.rerun()
            
    # --- TRẠNG THÁI 2: ĐÃ ĐĂNG NHẬP ---
    else:
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
            st.write(f"Xin chào, **{user['full_name']}**")
            st.caption(f"Vai trò: {user.get('role', 'Sinh viên')}")
            st.divider()
            
            menu = st.radio(
                "Menu chính", 
                ["🏠 Dashboard", "🧠 Học tập (LMS)", "👤 Hồ sơ cá nhân", "🔐 Quản lý FaceID", "📊 Báo cáo"],
                index=0, key="main_app_navigation"
            )
            
            st.divider()
            if st.button("🚪 Đăng xuất", use_container_width=True):
                save_activity_log(user['user_id'], user['full_name'], "Logout")
                st.session_state.clear()
                st.query_params.clear()
                st.rerun()

        user_id = user.get('user_id')
        
        if menu == "🏠 Dashboard":
            with st.spinner("Đang cập nhật tiến độ mới nhất..."):
                current_progress = get_user_progress(user_id)
            render_student_dashboard_page(user_id, current_progress)
            
        elif menu == "🧠 Học tập (LMS)":
            save_activity_log(user_id, user['full_name'], "Enter LMS")
            render_adaptive_ui()
            
        elif menu == "👤 Hồ sơ cá nhân":
            render_student_profile_page()
            
        elif menu == "🔐 Quản lý FaceID":
            render_register_face_ui(user)
            
        elif menu == "📊 Báo cáo":
            # --- STYLE CSS SIÊU CẤP ---
            st.markdown("""
                <style>
                [data-testid="stMetricValue"] { font-size: 28px; color: #1e3a8a; }
                .report-card {
                    background-color: #ffffff; padding: 20px; border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #3b82f6;
                    margin-bottom: 20px;
                }
                .ai-box {
                    background: #f0f9ff; border-radius: 15px; padding: 20px;
                    border: 1px solid #bae6fd; color: #0369a1; margin-top: 20px;
                }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; color: white; margin-bottom: 30px;">
                    <h1 style="margin:0; font-size: 2.2rem;">🚀 ULTRA ANALYTICS CENTER</h1>
                    <p style="margin:5px 0 0 0; opacity:0.8;">Trung tâm phân tích năng lực đa tầng - Dự án Ebsis Redeemer</p>
                </div>
            """, unsafe_allow_html=True)

            with st.spinner("Đang tổng hợp dữ liệu từ Big Data..."):
                current_progress = get_user_progress(user_id)
                is_admin = user.get('role') == 'Admin'

            if current_progress:
                score = current_progress.get('score', 0)
                cheats = current_progress.get('cheat_count', 0)
                chap = int(float(current_progress.get('current_chapter', 0)))
                raw_violations = current_progress.get('violation_details', '[]')

                # --- ROW 1: KPI TIÊU CHUẨN ---
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.metric("Hệ số Mastery", f"{score}%", "▲ 3.1%")
                    st.markdown('</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.metric("Chỉ số Tin cậy", f"{max(0, 100-(cheats*2))}%", f"-{cheats} lỗi", delta_color="inverse")
                    st.markdown('</div>', unsafe_allow_html=True)
                with c3:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.metric("Xếp hạng Lớp", "Top 5", "▲ 1")
                    st.markdown('</div>', unsafe_allow_html=True)
                with c4:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.metric("Hoàn thành", f"{(chap/8)*100:.0f}%", f"{chap}/8 Bài")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.divider()

                # --- ROW 2: RADAR & GAUGE ---
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🕸️ Bản đồ Gen Năng lực")
                    categories = ['SQL Coding', 'BPMN Design', 'SRS Detail', 'UI/UX Logic', 'Problem Solving']
                    values = [score, max(0, score-10), 85, 70, score+5]
                    fig_radar = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#1e3a8a'))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350)
                    st.plotly_chart(fig_radar, use_container_width=True)

                with col2:
                    st.subheader("🛡️ Độ Minh bạch AI (Gauge)")
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number", value=max(0, 100-(cheats*2)),
                        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1e3a8a"},
                               'steps': [{'range': [0, 50], 'color': "#fee2e2"}, {'range': [50, 100], 'color': "#dcfce7"}]}
                    ))
                    fig_gauge.update_layout(height=350)
                    st.plotly_chart(fig_gauge, use_container_width=True)

                # --- ROW 3: TREE MAP & FUNNEL ---
                st.divider()
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader("🌳 Phân bổ Kiến thức (Tree Map)")
                    fig_tree = px.treemap(
                        names=["SQL", "Subquery", "Join", "BPMN", "Events", "Gateways", "SRS", "Usecase"],
                        parents=["", "SQL", "SQL", "", "BPMN", "BPMN", "", "SRS"],
                        values=[10, 20, 30, 15, 25, 35, 20, 40]
                    )
                    st.plotly_chart(fig_tree, use_container_width=True)

                with col4:
                    st.subheader("🌪️ Phễu Chuyển đổi (Funnel)")
                    fig_funnel = go.Figure(go.Funnel(
                        y=["Đăng ký", "Hoàn thành Ch1", "Vượt qua Checkpoint", "Tốt nghiệp"],
                        x=[100, 85, 60, score if chap == 8 else 10],
                        textinfo="value+percent initial"
                    ))
                    st.plotly_chart(fig_funnel, use_container_width=True)

                # --- ROW 4: AREA & BULLET ---
                st.divider()
                st.subheader("📈 Lịch sử Biến thiên & Phân tích Sai lệch")
                col5, col6 = st.columns([2, 1])
                with col5:
                    time_x = [f"Tuần {i}" for i in range(1, 6)]
                    score_y = [40, 55, score-10, score-5, score]
                    fig_area = px.area(x=time_x, y=score_y, title="Lộ trình tăng trưởng Mastery Score")
                    st.plotly_chart(fig_area, use_container_width=True)
                
                with col6:
                    fig_bullet = go.Figure(go.Indicator(
                        mode="number+gauge+delta", value=score,
                        delta={'reference': 80},
                        gauge={'shape': "bullet", 'axis': {'range': [0, 100]},
                               'threshold': {'line': {'color': "red", 'width': 2}, 'thickness': 0.75, 'value': 80}}
                    ))
                    fig_bullet.update_layout(height=250, title="So với Mục tiêu (80%)")
                    st.plotly_chart(fig_bullet, use_container_width=True)

                # --- ROW 5: HEATMAP ---
                st.divider()
                st.subheader("🔥 Nhật ký Tương tác (Heatmap)")
                heatmap_data = np.random.randint(0, 10, size=(7, 12))
                fig_heat = px.imshow(heatmap_data, x=['8h','10h','12h','14h','16h','18h','20h','22h','0h','2h','4h','6h'],
                                   y=['T2','T3','T4','T5','T6','T7','CN'], color_continuous_scale="Blues")
                st.plotly_chart(fig_heat, use_container_width=True)

                # --- CHI TIẾT VI PHẠM ---
                with st.expander("🚨 Xem chi tiết Nhật ký Giám sát AI"):
                    try:
                        logs_list = json.loads(raw_violations) if isinstance(raw_violations, str) else raw_violations
                        if logs_list: st.table(pd.DataFrame(logs_list))
                        else: st.success("Không có vi phạm nào.")
                    except: st.write("Đang tải dữ liệu...")

                # --- AI ADVISOR ---
                st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                st.markdown(f"### 🤖 AI Insight: Chiến lược cho {user['full_name']}")
                st.write(f"Dựa trên **Phễu chuyển đổi**, bạn đang ở giai đoạn cuối của khóa học. Biểu đồ **Tree Map** cho thấy kiến thức **SQL** của bạn rất vững, nhưng **UI/UX** trong biểu đồ Radar đang bị khuyết. Đề xuất: Tập trung Chapter 4 ngay!")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- ADMIN VIEW ---
                if is_admin:
                    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
                    st.subheader("🏢 Quản trị Hệ thống (Admin Only)")
                    fig_sun = px.sunburst(path=['course_id', 'user_id'], values=[score]*5)
                    st.plotly_chart(fig_sun, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.divider()
                pdf_data = generate_insight_pdf(user['full_name'], score, chap, cheats)
                st.download_button("📥 TẢI BÁO CÁO FULL ANALYTICS (PDF)", data=pdf_data, 
                                 file_name=f"Ebsis_Ultra_{user['user_id']}.pdf", mime="application/pdf", type="primary", use_container_width=True)
            else:
                st.warning("⚠️ Chưa có dữ liệu học tập.")

if __name__ == "__main__":
    main()