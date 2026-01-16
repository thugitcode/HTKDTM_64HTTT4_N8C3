import streamlit as st
import sys
import os
import time

# --- CẤU HÌNH ---
st.set_page_config(page_title="Ebsis - Intelligent Learning", page_icon="🎓", layout="wide")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Logic
from src.core.m1_proctoring import verify_login, register_face, login_with_face
from src.core.m2_adaptive import load_data, analyze_and_generate_path

# --- CSS ---
def local_css():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #f8f9fa; }
        .metric-card { background-color: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center; }
        div.stButton > button { background-color: #2E86C1; color: white; border-radius: 5px; width: 100%; }
        /* Style cho trạng thái lộ trình */
        .status-red { color: #E74C3C; font-weight: bold; }
        .status-orange { color: #F39C12; font-weight: bold; }
        .status-green { color: #27AE60; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION ---
if 'is_logged_in' not in st.session_state: st.session_state['is_logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

# --- LOGIN SCREEN ---
def login_screen():
    local_css()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🎓 EBSIS SYSTEM</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 Mật khẩu", "📸 Face ID"])
        
        with tab1:
            u = st.text_input("Mã SV", "SV001")
            p = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập"):
                user = verify_login(u, p)
                if user:
                    st.session_state['is_logged_in'] = True
                    st.session_state['user_info'] = user
                    st.rerun()
                else: st.error("Sai thông tin!")
        
        with tab2:
            img = st.camera_input("Quét khuôn mặt", label_visibility="collapsed")
            if img:
                user, msg = login_with_face(img)
                if user:
                    st.success(f"Chào {user['full_name']}!")
                    st.session_state['is_logged_in'] = True
                    st.session_state['user_info'] = user
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)

# --- MAIN DASHBOARD ---
def main_dashboard():
    local_css()
    user = st.session_state['user_info']
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
        st.markdown(f"### {user['full_name']}")
        st.caption(f"ID: {user['user_id']} | Role: {user['role']}")
        st.divider()
        menu = st.radio("Menu", ["🏠 Dashboard", "🔐 Smart Entry", "🧠 Adaptive Path", "📊 Analytics"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Đăng xuất"):
            st.session_state['is_logged_in'] = False
            st.rerun()

    # 1. DASHBOARD
    if menu == "🏠 Dashboard":
        st.title("Tổng quan học tập")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown("<div class='metric-card'><h3>📚 4</h3><p>Modules</p></div>", unsafe_allow_html=True)
        c2.markdown("<div class='metric-card'><h3>⏳ 12h</h3><p>Giờ học</p></div>", unsafe_allow_html=True)
        c3.markdown("<div class='metric-card'><h3>🔥 85%</h3><p>Chuyên cần</p></div>", unsafe_allow_html=True)
        c4.markdown("<div class='metric-card'><h3>⭐ A</h3><p>Xếp loại</p></div>", unsafe_allow_html=True)
        
        st.markdown("### 📢 Thông báo từ AI")
        st.info("💡 Bạn có bài kiểm tra năng lực chưa hoàn thành. Hãy vào menu **Adaptive Path** để nhận lộ trình học.")

    # 2. SMART ENTRY
    elif menu == "🔐 Smart Entry":
        st.title("🔐 Đăng ký FaceID")
        c1, c2 = st.columns(2)
        with c1:
            img = st.camera_input("Chụp ảnh mẫu")
            if img:
                ok, msg = register_face(user['user_id'], img)
                if ok: st.success(msg)
                else: st.error(msg)
        with c2:
            st.info("Dữ liệu khuôn mặt dùng để đăng nhập và giám sát thi cử.")
            if user.get('has_face_id'): st.success("✅ Đã có dữ liệu khuôn mặt.")

    # 3. ADAPTIVE PATH (LỘ TRÌNH CÁ NHÂN HÓA)
    elif menu == "🧠 Adaptive Path":
        st.title("🧠 Lộ trình học tập Cá nhân hóa")
        st.markdown("---")
        
        df_q, df_c = load_data()
        
        if df_q.empty or df_c.empty:
            st.warning("⚠️ Đang tải dữ liệu... Nếu chờ lâu hãy chạy lại file `init_db.py`")
        else:
            if 'quiz_done' not in st.session_state: st.session_state['quiz_done'] = False
            
            # --- PHẦN 1: BÀI THI KHẢO SÁT (4 KỸ NĂNG) ---
            if not st.session_state['quiz_done']:
                st.info("🕒 **Khảo sát năng lực (Assessment):** Hệ thống sẽ kiểm tra kiến thức 4 tuần của bạn để thiết kế lộ trình phù hợp.")
                
                with st.form("assessment_form"):
                    # Chia tab cho dễ nhìn
                    tab1, tab2, tab3, tab4 = st.tabs(["🐍 Python (Tuần 1)", "🗄️ SQL (Tuần 2)", "🌐 Network (Tuần 3)", "⚙️ Agile (Tuần 4)"])
                    
                    user_answers = {}
                    skills_map = {0: "Coding", 1: "Database", 2: "Network", 3: "SE"}
                    tabs = [tab1, tab2, tab3, tab4]
                    
                    for i, tab in enumerate(tabs):
                        with tab:
                            skill = skills_map[i]
                            qs = df_q[df_q['skill_tag'] == skill]
                            for _, row in qs.iterrows():
                                st.write(f"**{row['question_text']}**")
                                c = st.radio(f"q_{row['id']}", 
                                             [f"A. {row['option_a']}", f"B. {row['option_b']}", f"C. {row['option_c']}", f"D. {row['option_d']}"],
                                             key=row['id'], label_visibility="collapsed")
                                if c: user_answers[row['id']] = c[0]
                                st.divider()
                    
                    if st.form_submit_button("Nộp bài & Phân tích lộ trình"):
                        if len(user_answers) < 4: # Demo check sơ bộ
                             st.warning("Vui lòng trả lời ít nhất 1 câu hỏi mỗi phần!")
                        else:
                            st.session_state['answers'] = user_answers
                            st.session_state['quiz_done'] = True
                            st.rerun()

            # --- PHẦN 2: HIỂN THỊ LỘ TRÌNH (ROADMAP) ---
            else:
                perf, roadmap = analyze_and_generate_path(st.session_state['answers'], df_q, df_c)
                
                st.success("🎉 AI đã xây dựng xong lộ trình 1 tháng cho bạn!")
                
                # Biểu đồ năng lực
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown("### 📊 Năng lực hiện tại")
                    st.bar_chart(perf)
                
                with c2:
                    st.markdown("### 🗓️ Lộ trình học tập (1 Tháng)")
                    for item in roadmap:
                        # Icon trạng thái
                        icon = "🔴" if item['color'] == 'red' else "🟡" if item['color'] == 'orange' else "🟢"
                        
                        # Expander: Tự động mở nếu bị Yếu (Critical)
                        with st.expander(f"{icon} {item['title']} (Điểm: {item['score']}/100)", expanded=item['is_open']):
                            
                            # Hiển thị trạng thái & Lời khuyên
                            st.markdown(f"**Trạng thái:** <span class='status-{item['color']}'>{item['status']}</span>", unsafe_allow_html=True)
                            st.info(f"💡 **AI Recommendation:** {item['action']}")
                            
                            # Danh sách bài học (Video/PDF)
                            st.markdown("#### 📚 Tài liệu bắt buộc:")
                            for mat in item['materials']:
                                col_icon, col_content = st.columns([0.1, 0.9])
                                with col_icon: st.write("📺" if mat['type'] == 'Video' else "📄")
                                with col_content:
                                    st.write(f"**{mat['name']}**")
                                    if mat['type'] == 'Video':
                                        st.video(mat['url'])
                                    else:
                                        st.markdown(f"[Tải tài liệu]({mat['url']})")
                
                if st.button("Làm lại bài test"):
                    st.session_state['quiz_done'] = False
                    st.rerun()

    # 4. ANALYTICS
    elif menu == "📊 Analytics":
        st.title("📊 Báo cáo thống kê")
        st.info("Tính năng đang phát triển...")

if __name__ == "__main__":
    if st.session_state['is_logged_in']:
        main_dashboard()
    else:
        login_screen()