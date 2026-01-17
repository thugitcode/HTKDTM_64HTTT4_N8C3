import streamlit as st
import time
import cv2
import numpy as np
import av
import pandas as pd
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from src.ui.student_dashboard import render_student_dashboard_page, render_student_profile_page

# Import Core Logic
from src.core.m2_adaptive import (
    load_data, assign_personalized_course, 
    save_learning_progress, get_user_progress, get_course_content
)
from src.ui.styles import load_custom_css
from src.ui.chatbot_ui import render_ai_tutor

# --- CẤU HÌNH AI ---
try:
    from src.core.face_processor import FaceEngine
    if 'face_engine' not in st.session_state:
        st.session_state['face_engine'] = FaceEngine()
    face_engine = st.session_state['face_engine']
    AI_AVAILABLE = True
except: 
    AI_AVAILABLE = False

# --- VIDEO PROCESSOR ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.violation_count = 0
        self.frame_counter = 0
        self.violation_log = [] 
        self.last_status = "NORMAL"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_counter += 1
        should_process = (self.frame_counter % 5 == 0)

        if AI_AVAILABLE:
            if should_process:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.pose = face_engine.detect_head_pose(img_rgb)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                if "⚠️" in self.pose or self.pose == "Không tìm thấy mặt":
                    self.color = (0, 0, 255)
                    self.status_text = f"VI PHAM: {self.pose}"
                    if self.last_status == "NORMAL":
                        self.violation_count += 1
                        self.violation_log.append({"Thời gian": current_time, "Lỗi": self.pose})
                        self.last_status = "VIOLATION"
                else:
                    self.color = (0, 255, 0)
                    self.status_text = "HOP LE"
                    self.last_status = "NORMAL"
            
            if hasattr(self, 'color'):
                h, w, _ = img.shape
                cv2.rectangle(img, (20, 20), (w-20, h-20), self.color, 3)
                cv2.putText(img, getattr(self, 'status_text', ''), (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.color, 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- [BỔ SUNG] HÀM TỔNG HỢP THỜI GIAN HỌC TẬP ---
def _calculate_total_learning_time(logs):
    """Phân tích log để tính tổng thời gian tương tác (giả định)"""
    if not logs: return "0 phút"
    try:
        df_logs = pd.DataFrame(logs)
        if "Thời gian" not in df_logs.columns: return "Chưa xác định"
        
        # Chuyển cột thời gian về định dạng datetime
        df_logs['t'] = pd.to_datetime(df_logs['Thời gian'], format='%H:%M:%S')
        duration = df_logs['t'].max() - df_logs['t'].min()
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} phút"
    except:
        return "Đang tính toán..."

# --- GIAO DIỆN LỄ TỐT NGHIỆP ---
def _render_graduation_ceremony(user_info, course, final_score):
    st.balloons()
    # Giao diện chứng chỉ vàng kim
    st.markdown(f"""
    <div style="border: 15px double #D4AF37; padding: 40px; text-align: center; background-color: #fdfdfd; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <div style="color: #D4AF37; font-size: 50px; margin-bottom: 10px;">🏆</div>
        <h1 style="color: #1E3A8A; font-family: 'serif'; font-size: 36px;">CHỨNG CHỈ TỐT NGHIỆP</h1>
        <p style="font-style: italic;">Hệ thống EBSIS xác nhận</p>
        <h2 style="text-transform: uppercase; color: #333; border-bottom: 2px solid #D4AF37; display: inline-block; padding: 0 20px;">{user_info.get('full_name', 'Học viên')}</h2>
        <p>Đã hoàn thành xuất sắc khóa học: <strong>{course['title']}</strong></p>
        <p style="color: #10B981; font-weight: bold;">Điểm tích lũy: {final_score}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Logic gợi ý lộ trình tiếp theo
    skill_map = {
        "Coding": "Database", "Database": "Coding", 
        "Network": "Agile", "Agile": "Coding"
    }
    next_skill = skill_map.get(course.get('skill_tag'), "Coding")
    st.info(f"🚀 **Bước tiếp theo:** Dựa trên kỹ năng vừa đạt được, bạn nên học tiếp môn **{next_skill}**")
    
    if st.button(f"🎯 Đăng ký học môn {next_skill}", type="primary", use_container_width=True):
        st.session_state['my_course'] = None
        st.session_state['force_retake'] = True
        st.rerun()

def render_adaptive_ui():
    """
    Hàm điều hướng nội dung LMS. 
    Lưu ý: Sidebar đã được quản lý tại main.py nên ở đây chỉ tập trung vào nội dung chính.
    """
    load_custom_css()
    
    # 1. Khởi tạo & Đồng bộ Session State (Giữ nguyên logic gốc của bạn)
    if 'my_course' not in st.session_state: st.session_state['my_course'] = None
    if 'cur_chapter_idx' not in st.session_state: st.session_state['cur_chapter_idx'] = 0
    if 'exam_result' not in st.session_state: st.session_state['exam_result'] = None
    if 'current_cheat_log' not in st.session_state: st.session_state['current_cheat_log'] = []
    if 'current_cheat_count' not in st.session_state: st.session_state['current_cheat_count'] = 0
    if 'force_retake' not in st.session_state: st.session_state['force_retake'] = False 
    
    user = st.session_state.get('user_info', {})
    user_id = str(user.get('user_id', 'Guest'))
    
    # 2. AUTO LOAD DỮ LIỆU TỪ DB (Đảm bảo dữ liệu luôn mới nhất)
    if st.session_state['my_course'] is None and not st.session_state['force_retake']:
        progress = get_user_progress(user_id)
        if progress:
            course_data = get_course_content(progress['course_id'])
            if course_data:
                st.session_state['my_course'] = course_data
                st.session_state['cur_chapter_idx'] = int(progress.get('current_chapter', 0))
                st.session_state['history_score'] = progress.get('score', 0)
                st.session_state['history_cheat'] = progress.get('cheat_count', 0)
                st.session_state['viewing_idx'] = min(int(progress.get('current_chapter', 0)), 7)

    # 3. GIAO DIỆN NỘI DUNG (Dùng Tabs thay cho Radio để không bị trùng Menu Cha)
    # Phân cấp: Sidebar bên trái là Module lớn, Tabs bên phải là thao tác nhỏ
    tab_study, tab_exam = st.tabs(["📖 Vào lớp học", "🩺 Kiểm tra năng lực"])

    with tab_study:
        if st.session_state['my_course']:
            # Nếu đã có khóa học thì vào học trực tiếp
            _render_classroom(user_id)
        else:
            st.info("👋 Chào mừng bạn! Vui lòng qua Tab 'Kiểm tra năng lực' để bắt đầu lộ trình học tập.")

    with tab_exam:
        # Logic hiển thị linh hoạt: Đã thi rồi thì hiện lịch sử, chưa thi thì hiện phòng thi
        if st.session_state['exam_result']:
            _render_analysis_report(user_id)
        elif st.session_state['my_course']:
            _render_exam_history(user_id)
        else:
            _render_smart_exam_realtime(user_id)

# --- [BỔ SUNG] MÀN HÌNH DASHBOARD THEO DÕI ---
def _render_student_dashboard(user_id):
    st.header("📊 BẢNG THEO DÕI TIẾN ĐỘ")
    progress = get_user_progress(user_id)
    if not progress:
        st.warning("Chưa có dữ liệu học tập."); return

    col1, col2, col3 = st.columns(3)
    col1.metric("Môn học", st.session_state['my_course']['title'] if st.session_state['my_course'] else "N/A")
    
    # Tính tổng thời gian dựa trên log
    import json
    logs = json.loads(progress.get('violation_details', '[]'))
    total_time = _calculate_total_learning_time(logs)
    
    col2.metric("Thời gian học tập", total_time)
    col3.metric("Số vi phạm", f"{progress.get('cheat_count', 0)} lần")

    st.divider()
    st.subheader("🕒 Lịch sử hoạt động")
    if logs:
        df_show = pd.DataFrame(logs).rename(columns={"Lỗi": "Chi tiết/Cảnh báo"})
        st.dataframe(df_show, use_container_width=True)

# --- MÀN HÌNH LỊCH SỬ ---
def _render_exam_history(user_id):
    course = st.session_state.get('my_course')
    score = st.session_state.get('history_score', 0)
    cheat = st.session_state.get('history_cheat', 0)
    
    st.markdown("""
    <div class="exam-header-container" style="background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);">
        <h2>📜 LỊCH SỬ KIỂM TRA</h2>
        <p>Bạn đã hoàn thành bài đánh giá năng lực.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Điểm số cũ", f"{score}/100")
    c2.metric("Số vi phạm cũ", f"{cheat} lần", delta_color="inverse")
    count = st.info(f"Khóa học: **{course['title']}**")
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 LÀM LẠI BÀI TEST", use_container_width=True):
            st.session_state['my_course'] = None
            st.session_state['exam_result'] = None
            st.session_state['current_cheat_log'] = []
            st.session_state['current_cheat_count'] = 0
            st.session_state['force_retake'] = True 
            st.rerun()
            
    with col_btn2:
        if st.button("🎓 VÀO LỚP HỌC TIẾP", type="primary", use_container_width=True):
            st.rerun()

# --- PHÒNG THI ĐẦU VÀO ---
def _render_smart_exam_realtime(user_id):
    st.markdown("""
    <div class="exam-header-container">
        <h2>🩺 PHÒNG THI GIÁM SÁT REAL-TIME</h2>
        <p>Bắt buộc bật Camera để hiển thị đề thi.</p>
    </div>
    """, unsafe_allow_html=True)
    
    df_q, df_c = load_data()
    col_exam, col_cam = st.columns([2, 1.2]) 
    
    webrtc_ctx = None
    with col_cam:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("**🔴 CAMERA GIÁM SÁT**")
        if AI_AVAILABLE:
            webrtc_ctx = webrtc_streamer(key="proctoring", mode=WebRtcMode.SENDRECV, video_processor_factory=VideoProcessor, media_stream_constraints={"video": True, "audio": False}, async_processing=True)
        else:
            st.error("⚠️ Lỗi AI.")
        st.markdown('</div>', unsafe_allow_html=True)

    is_camera_on = webrtc_ctx and webrtc_ctx.state.playing

    with col_exam:
        if not is_camera_on:
            st.warning("⚠️ Đề thi đang bị ẩn. Vui lòng bật Camera (Nút START).")
        else:
            with st.form("exam_form"):
                st.markdown("### 📝 Bài làm")
                answers = {}
                if not df_q.empty:
                    diag_q = df_q[~df_q['id'].str.startswith('CHECK_')]
                    skills = diag_q['skill_tag'].unique()
                    for skill in skills:
                        st.markdown(f"#### 🔹 {skill}")
                        for idx, row in diag_q[diag_q['skill_tag'] == skill].iterrows():
                            st.markdown(f"**Câu {row['id']}:** {row['question_text']}")
                            c = st.radio("Chọn:", [row['option_a'], row['option_b'], row['option_c'], row['option_d']], key=row['id'], horizontal=True, index=None)
                            if c:
                                map_ans = {row['option_a']:'A', row['option_b']:'B', row['option_c']:'C', row['option_d']:'D'}
                                answers[row['id']] = map_ans.get(c, 'A')
                            st.divider()
                
                if st.form_submit_button("📤 NỘP BÀI & LƯU KẾT QUẢ", type="primary", use_container_width=True):
                    cheat_count = webrtc_ctx.video_transformer.violation_count if webrtc_ctx.video_transformer else 0
                    cheat_log = webrtc_ctx.video_transformer.violation_log if webrtc_ctx.video_transformer else []
                    
                    analysis_result = assign_personalized_course(answers, diag_q, df_c)
                    course = analysis_result['recommended_course']
                    
                    with st.spinner("Đang lưu kết quả..."):
                        save_learning_progress(user_id, course['course_id'], analysis_result['total_score'], cheat_count, 0, violation_log=cheat_log)
                        st.session_state['exam_result'] = analysis_result
                        st.session_state['my_course'] = course 
                        st.rerun()

# --- BÀI THI CHECKPOINT (CUỐI KHÓA) ---
def _render_checkpoint_quiz(user_id, course, skill_tag):
    st.markdown(f"### 🚩 BÀI THI CHECKPOINT: {skill_tag.upper()}")
    st.info("💡 Bạn cần trả lời đúng tối thiểu 80% để hoàn thành lộ trình học này.")
    df_q, _ = load_data()
    pool = df_q[df_q['skill_tag'] == skill_tag].to_dict('records')
    
    if not pool:
        st.error("Chưa nạp bộ câu hỏi cho môn học này."); return

    with st.form("checkpoint_form"):
        user_ans = {}
        for i, q in enumerate(pool):
            st.write(f"**Câu {i+1}: {q['question_text']}**")
            user_ans[q['id']] = st.radio("Chọn đáp án:", [q['option_a'], q['option_b'], q['option_c'], q['option_d']], key=f"ch_{q['id']}")
        
        if st.form_submit_button("NỘP BÀI VÀ KẾT THÚC"):
            correct = 0
            for q in pool:
                mapping = {"A": q['option_a'], "B": q['option_b'], "C": q['option_c'], "D": q['option_d']}
                if user_ans[q['id']] == mapping[q['correct_opt']]:
                    correct += 1
            final_percent = int((correct / len(pool)) * 100)
            
            # CỘNG DỒN LOG KẾT QUẢ THI
            checkpoint_log = [{"Thời gian": datetime.now().strftime("%H:%M:%S"), "Sự kiện": f"Hoàn thành Checkpoint: {final_percent}%"}]
            
            with st.spinner("Đang ghi nhận kết quả tốt nghiệp..."):
                save_learning_progress(user_id, course['course_id'], final_percent, 0, 8, violation_log=checkpoint_log)
            
            st.session_state['history_score'] = final_percent
            st.session_state['cur_chapter_idx'] = 8
            # FIX LỖI INDEX TẠI ĐÂY
            st.session_state['viewing_idx'] = len(course.get('chapters', [])) - 1
            
            if final_percent >= 80:
                st.success(f"🎉 Tuyệt vời! Bạn đạt {final_percent}%. Bạn đã tốt nghiệp khóa học!"); st.balloons()
                time.sleep(1)
            else:
                st.error(f"⚠️ Kết quả: {final_percent}%. Bạn cần 80% để qua môn. Hãy ôn tập lại!")
            st.rerun()

# --- REPORT CHI TIẾT ---
def _render_analysis_report(user_id):
    result = st.session_state['exam_result']
    course = result['recommended_course']
    cheat_count = st.session_state.get('current_cheat_count', 0)
    cheat_log = st.session_state.get('current_cheat_log', [])
    
    st.markdown(f"""
    <div class="exam-header-container" style="background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);">
        <h2>📊 KẾT QUẢ VỪA THI: {result['total_score']}/100</h2>
        <p>Dữ liệu đã được lưu vào hồ sơ.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if cheat_count > 0:
        with st.expander("⚠️ Xem nhật ký vi phạm", expanded=False):
            st.dataframe(pd.DataFrame(cheat_log), use_container_width=True)
    else:
        st.success("✅ Không vi phạm quy chế.")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Biểu đồ kỹ năng")
        for skill, stats in result['skill_breakdown'].items():
            st.progress(stats['score']/100)
            st.caption(f"{skill}: {stats['score']}%")
    with c2:
        st.info(f"💡 Đề xuất: **{course['title']}**")
        st.write("Dựa trên kết quả, AI đã gán khóa học này cho bạn.")

    with st.expander("🔎 Xem chi tiết đúng/sai", expanded=False):
        for i, item in enumerate(result['details']):
            col_icon, col_text = st.columns([0.1, 0.9])
            with col_icon:
                if item['is_correct']: st.success("Đ")
                else: st.error("S")
            with col_text:
                st.markdown(f"**Câu {i+1}: {item['question']}**")
                if not item['is_correct']:
                    st.markdown(f"❌ Bạn chọn: ~~{item['user_opt']}~~ | 👉 **Đúng: {item['correct_opt']}**")
            st.markdown("---")
            
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 LÀM LẠI BÀI TEST", use_container_width=True):
            st.session_state['exam_result'] = None
            st.session_state['my_course'] = None 
            st.session_state['force_retake'] = True 
            st.rerun()
    with col_btn2:
        if st.button("🎓 VÀO HỌC NGAY", type="primary", use_container_width=True):
            st.session_state['exam_result'] = None
            st.rerun()

# --- LỚP HỌC ---
def _render_classroom(user_id):
    course = st.session_state.get('my_course')
    if not course:
        st.warning("⚠️ Chưa có lộ trình học."); return

    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 20px; border-radius: 15px; color: white; margin-bottom: 25px;">
        <h1 style="margin:0; font-size: 24px;">{course['title']}</h1>
        <p style="margin:5px 0 0 0; opacity: 0.8;">Lộ trình cá nhân hóa cho BA</p>
    </div>
    """, unsafe_allow_html=True)

    max_unlocked_idx = st.session_state.get('cur_chapter_idx', 0)
    chapters = course.get('chapters', [])

    if 'viewing_idx' not in st.session_state:
        st.session_state['viewing_idx'] = max_unlocked_idx

    # --- FIX LỖI INDEX OUT OF RANGE TẠI ĐÂY ---
    if st.session_state['viewing_idx'] >= len(chapters):
        st.session_state['viewing_idx'] = len(chapters) - 1
    
    cur_view_idx = st.session_state['viewing_idx']
    # ------------------------------------------

    col_nav, col_content = st.columns([1, 2.8])

    with col_nav:
        st.subheader("📅 Lộ trình")
        for idx, ch in enumerate(chapters):
            is_locked = idx > max_unlocked_idx
            is_done = idx < max_unlocked_idx
            
            icon = "🔒" if is_locked else "✅" if is_done else "▶️"
            label = f"Ngày {ch['day']}: {ch['title'][:12]}..."
            if st.button(f"{icon} {label}", key=f"nav_{idx}", use_container_width=True, disabled=is_locked):
                st.session_state['viewing_idx'] = idx; st.rerun()

    with col_content:
        active_day = chapters[cur_view_idx]
        c_main, c_ai = st.columns([2, 1])
        
        with c_main:
            st.markdown(f"### 📌 {active_day['title']}")
            st.divider()

            is_quiz_day = False
            for lesson in active_day.get('lessons', []):
                if lesson['type'] == 'Video':
                    st.video(lesson['url'])
                elif lesson['type'] == 'Reading':
                    st.info(f"📖 [Tài liệu: {lesson['title']}]({lesson['url']})")
                elif lesson['type'] == 'Practice':
                    st.markdown("---")
                    st.markdown(f"#### 🛠️ Thực hành: {lesson['title']}")
                    st.warning(f"📝 **Yêu cầu:** {lesson['desc']}")
                    
                    if course['skill_tag'] in ['Coding', 'Database']:
                        user_code = st.text_area("Môi trường thực hành (Sandbox)", placeholder="Nhập code Python hoặc SQL...", height=150, key=f"code_day_{cur_view_idx}")
                        if st.button("🚀 Chạy & Nộp bài", key=f"btn_day_{cur_view_idx}"):
                            st.success("✅ Đã ghi nhận bài làm!"); 
                            practice_log = [{"Thời gian": datetime.now().strftime("%H:%M:%S"), "Sự kiện": f"Nộp bài thực hành Ngày {active_day['day']}"}]
                            save_learning_progress(user_id, course['course_id'], score=None, cheat_count=0, violation_log=practice_log)
                    else:
                        st.file_uploader("Nộp sơ đồ/tài liệu nộp bài (.pdf, .png, .docx)", key=f"file_day_{cur_view_idx}")
                    st.markdown("---")
                elif lesson['type'] == 'Quiz':
                    is_quiz_day = True
            
            if is_quiz_day:
                current_score = st.session_state.get('history_score', 0)
                if max_unlocked_idx >= 8 and current_score >= 80:
                    _render_graduation_ceremony(st.session_state.user_info, course, current_score)
                else:
                    _render_checkpoint_quiz(user_id, course, course['skill_tag'])
            else:
                if cur_view_idx == max_unlocked_idx:
                    st.divider()
                    if st.button("✅ HOÀN THÀNH & MỞ KHÓA TIẾP THEO", type="primary", use_container_width=True):
                        next_idx = cur_view_idx + 1
                        finish_log = [{"Thời gian": datetime.now().strftime("%H:%M:%S"), "Sự kiện": f"Hoàn thành bài học Ngày {active_day['day']}"}]
                        if next_idx < len(chapters):
                            with st.spinner("Đang đồng bộ tiến độ..."):
                                save_learning_progress(user_id, course['course_id'], None, 0, next_idx, violation_log=finish_log)
                            st.session_state['cur_chapter_idx'] = next_idx
                            st.session_state['viewing_idx'] = next_idx
                            st.balloons(); st.rerun()
                        else:
                            st.success("🎉 Bạn đã hoàn thành bài học cuối. Hãy thực hiện bài thi tốt nghiệp!")

        with c_ai:
            st.markdown("### 🤖 Trợ lý AI")
            render_ai_tutor(active_day['title'])