import streamlit as st
import time
import cv2
import numpy as np
import av
import pandas as pd
import json
import threading
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from src.ui.student_dashboard import render_student_dashboard_page, render_student_profile_page
from src.core.m3_registration import handle_next_course_registration
from src.services.email_service import send_graduation_email

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
        # Tối ưu: Chỉ quét AI mỗi 15 frame để máy không bị nóng và lag
        should_process = (self.frame_counter % 15 == 0)

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

# --- HÀM TỔNG HỢP THỜI GIAN HỌC TẬP ---
def _calculate_total_learning_time(logs):
    if not logs: return "0 phút"
    try:
        df_logs = pd.DataFrame(logs)
        if "Thời gian" not in df_logs.columns: return "Chưa xác định"
        df_logs['t'] = pd.to_datetime(df_logs['Thời gian'], format='%H:%M:%S')
        duration = df_logs['t'].max() - df_logs['t'].min()
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} phút"
    except:
        return "Đang tính toán..."

# --- GIAO DIỆN LỄ TỐT NGHIỆP (BẢN FIX TRIỆT ĐỂ LỖI TÊN & CHUYỂN MÔN MỚI) ---
def _render_graduation_ceremony(user_info, course, final_score):
    st.balloons()
    
    full_name_str = str(user_info.get('full_name', 'Học viên'))
    
    # 1. Hiển thị chứng chỉ (Giữ nguyên code UI của Thư)
    st.markdown(f"""
    <div style="border: 15px double #D4AF37; padding: 40px; text-align: center; background-color: #fdfdfd; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <div style="color: #D4AF37; font-size: 50px; margin-bottom: 10px;">🏆</div>
        <h1 style="color: #1E3A8A; font-family: 'serif'; font-size: 36px;">CHỨNG CHỈ TỐT NGHIỆP</h1>
        <p style="font-style: italic;">Hệ thống EBSIS xác nhận</p>
        <h2 style="text-transform: uppercase; color: #333; border-bottom: 2px solid #D4AF37; display: inline-block; padding: 0 20px;">{full_name_str}</h2>
        <p>Đã hoàn thành xuất sắc khóa học: <strong>{course['title']}</strong></p>
        <p style="color: #10B981; font-weight: bold;">Điểm tích lũy: {final_score}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Gửi Email (Giữ nguyên)
    col_mail, _ = st.columns([1, 1])
    with col_mail:
        user_email = user_info.get('email', '')
        if st.button("📧 Nhận Chứng Chỉ Qua Email", use_container_width=True, key="btn_send_grad_mail"):
            if user_email and "@" in user_email:
                with st.spinner("Đang gửi..."):
                    success, msg = send_graduation_email(user_email, full_name_str, course['title'], final_score)
                    if success: st.success("📩 Đã gửi!")
                    else: st.error(msg)
            else: st.error("Lỗi: Chưa có Email!")
    
    st.divider()
    
    # 3. Logic gợi ý và Đăng ký môn mới (PHẦN QUAN TRỌNG)
    skill_map = {"Coding": "Database", "Database": "Coding", "Network": "Agile", "Agile": "Coding"}
    next_skill = skill_map.get(course.get('skill_tag'), "Coding")
    st.info(f"🚀 **Bước tiếp theo:** Bạn nên học tiếp môn **{next_skill}**")
    
    if st.button(f"🎯 Đăng ký học môn {next_skill}", type="primary", use_container_width=True, key="btn_reg_next_course_final"):
        with st.spinner(f"Đang thiết lập lộ trình môn {next_skill}..."):
            # CHIÊU CỨU CÁNH: Xóa sạch bộ nhớ đệm của hàm load_data để ép App đọc lại Sheets
            st.cache_data.clear()
            
            # A. Gọi Database để đổi môn học của User sang môn mới
            success, msg = handle_next_course_registration(user_info['user_id'], course['course_id'])
            
            if success:
                # B. CHIÊU QUAN TRỌNG: "THANH TẨY" TOÀN BỘ BỘ NHỚ TẠM (RAM)
                # Xóa môn cũ để hàm render_adaptive_ui ở trên buộc phải gọi get_user_progress để lấy môn mới
                st.session_state['my_course'] = None 
                st.session_state['exam_result'] = None # Thoát khỏi màn hình chứng chỉ
                
                # C. Reset toàn bộ tiến độ về Ngày 1
                st.session_state['cur_chapter_idx'] = 0
                st.session_state['viewing_idx'] = 0
                st.session_state['history_score'] = 0 # Điểm môn mới bắt đầu từ 0
                st.session_state['force_retake'] = False

                st.toast(f"🎉 Đã kích hoạt môn {next_skill}!", icon="📚")
                
                # D. Chờ một chút để Google Sheets ghi xong rồi Rerun
                time.sleep(2) 
                st.rerun() 
            else:
                st.error(f"Lỗi: {msg}")

# --- HÀM ĐIỀU HƯỚNG CHÍNH (ROUTER) ---
def render_adaptive_ui(progress=None):
    load_custom_css()
    
    # 1. Khởi tạo & Đồng bộ Session State
    if 'my_course' not in st.session_state: st.session_state['my_course'] = None
    if 'cur_chapter_idx' not in st.session_state: st.session_state['cur_chapter_idx'] = 0
    if 'viewing_idx' not in st.session_state: st.session_state['viewing_idx'] = 0
    if 'exam_result' not in st.session_state: st.session_state['exam_result'] = None
    if 'current_cheat_log' not in st.session_state: st.session_state['current_cheat_log'] = []
    if 'current_cheat_count' not in st.session_state: st.session_state['current_cheat_count'] = 0
    if 'force_retake' not in st.session_state: st.session_state['force_retake'] = False 
    
    user = st.session_state.get('user_info', {})
    user_id = str(user.get('user_id', 'Guest'))
    
    # 2. Sync dữ liệu từ DB (Chỉ load khi không có dữ liệu tạm)
    # CẢI TIẾN: Khi st.session_state['my_course'] là None (do vừa bấm đăng ký môn mới), 
    # đoạn này sẽ ép hệ thống lấy dữ liệu môn mới nhất từ Database.
    if st.session_state['my_course'] is None and not st.session_state['force_retake'] and st.session_state['exam_result'] is None:
        if progress is None: 
            progress = get_user_progress(user_id)
            
        if progress and progress.get('course_id'):
            course_data = get_course_content(progress['course_id'])
            if course_data:
                st.session_state['my_course'] = course_data
                db_idx = int(float(progress.get('current_chapter', 0)))
                st.session_state['cur_chapter_idx'] = db_idx
                st.session_state['history_score'] = progress.get('score', 0)
                st.session_state['history_cheat'] = progress.get('cheat_count', 0)
                
                # FIX VĂNG NGÀY: Ưu tiên mở ngày đang học dở từ Database
                # Nếu là môn mới tinh (db_idx = 0), viewing_idx sẽ tự về 0
                st.session_state['viewing_idx'] = min(db_idx, len(course_data.get('chapters', [])) - 1) if course_data.get('chapters') else 0

    # 3. Phân chia giao diện Tabs
    tab_study, tab_archive, tab_exam = st.tabs(["📖 Lớp học hiện tại", "📚 Kho tàng tri thức", "🩺 Kiểm tra năng lực"])
    
    with tab_study:
        # Nếu đã có môn học (mới hoặc cũ) thì hiện lớp học
        if st.session_state['my_course']:
            _render_classroom(user_id)
        else:
            st.info("👋 Chào mừng bạn! Vui lòng qua Tab 'Kiểm tra năng lực' để bắt đầu lộ trình học tập.")

    with tab_archive:
        # CHIÊU MỚI: Tab này dùng để xem lại các môn cũ
        _render_knowledge_archive(user_id)

    with tab_exam:
        # Logic Router cho Tab thi
        # Nếu có kết quả thi (vừa thi xong hoặc vừa tốt nghiệp), hiện Report/Chứng chỉ
        if st.session_state['exam_result'] is not None:
            _render_analysis_report(user_id)
        # Nếu nhấn nút "Làm lại bài test"
        elif st.session_state['force_retake']:
            _render_smart_exam_realtime(user_id)
        # Nếu đã có môn học nhưng không ở trạng thái vừa thi xong -> Hiện lịch sử thi cũ
        elif st.session_state['my_course'] is not None:
            _render_exam_history(user_id)
        # Mặc định: Hiện phòng thi
        else:
            _render_smart_exam_realtime(user_id)

# --- MÀN HÌNH DASHBOARD THEO DÕI ---
def _render_student_dashboard(user_id):
    st.header("📊 BẢNG THEO DÕI TIẾN ĐỘ")
    progress = get_user_progress(user_id)
    if not progress:
        st.warning("Chưa có dữ liệu học tập."); return

    col1, col2, col3 = st.columns(3)
    col1.metric("Môn học", st.session_state['my_course']['title'] if st.session_state['my_course'] else "N/A")
    logs = json.loads(progress.get('violation_details', '[]'))
    col2.metric("Thời gian học tập", _calculate_total_learning_time(logs))
    col3.metric("Số vi phạm", f"{progress.get('cheat_count', 0)} lần")

    st.divider()
    st.subheader("🕒 Lịch sử hoạt động")
    if logs:
        df_show = pd.DataFrame(logs).rename(columns={"Lỗi": "Chi tiết/Cảnh báo"})
        st.dataframe(df_show, use_container_width=True)

# --- MÀN HÌNH LỊCH SỬ ---
def _render_exam_history(user_id):
    score = st.session_state.get('history_score', 0)
    cheat = st.session_state.get('history_cheat', 0)
    course = st.session_state.get('my_course')

    if score == 0 and st.session_state.get('exam_result') is not None:
        score = st.session_state['exam_result'].get('total_score', 0)

    st.markdown("""
    <div class="exam-header-container" style="background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);">
        <h2>📜 LỊCH SỬ KIỂM TRA</h2>
        <p>Hệ thống đã ghi nhận lộ trình học tập dựa trên năng lực của bạn.</p>
    </div>
    """, unsafe_allow_html=True)

    if score == 0:
        st.warning("⏳ Hệ thống đang đồng bộ kết quả mới nhất từ Cloud, vui lòng đợi trong giây lát...")

    c1, c2, c3 = st.columns(3)
    c1.metric("Điểm năng lực", f"{score}/100")
    c2.metric("Số vi phạm", f"{cheat} lần", delta_color="inverse")
    
    st.info(f"📚 Khóa học đang theo đuổi: **{course['title'] if course else 'N/A'}**")
    
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔄 LÀM LẠI BÀI TEST", use_container_width=True, key="btn_retake_from_history"):
            st.session_state['my_course'] = None
            st.session_state['exam_result'] = None
            st.session_state['current_cheat_log'] = []
            st.session_state['current_cheat_count'] = 0
            st.session_state['force_retake'] = True 
            st.rerun()
            
    with col_btn2:
        if st.button("🎓 VÀO LỚP HỌC TIẾP", type="primary", use_container_width=True, key="btn_go_to_class_from_history"):
            st.rerun()

# --- PHÒNG THI ĐẦU VÀO ---
def _render_smart_exam_realtime(user_id):
    st.markdown("""<div class="exam-header-container"><h2>🩺 PHÒNG THI GIÁM SÁT REAL-TIME</h2><p>Bắt buộc bật Camera để hiển thị đề thi.</p></div>""", unsafe_allow_html=True)
    
    df_q, df_c = load_data()
    col_exam, col_cam = st.columns([2, 1.2]) 
    
    webrtc_ctx = None
    with col_cam:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("**🔴 CAMERA GIÁM SÁT**")
        if AI_AVAILABLE:
            webrtc_ctx = webrtc_streamer(
                key="proctoring_exam_unique", 
                mode=WebRtcMode.SENDRECV, 
                video_processor_factory=VideoProcessor, 
                media_stream_constraints={"video": {"width": 320}, "audio": False}, 
                async_processing=True
            )
        else: st.error("⚠️ Lỗi AI.")
        if webrtc_ctx and webrtc_ctx.video_transformer:
            if webrtc_ctx.video_transformer.violation_count > 0:
                st.toast(f"⚠️ Cảnh báo: AI phát hiện {webrtc_ctx.video_transformer.violation_count} hành vi lạ!", icon="❌")
        st.markdown('</div>', unsafe_allow_html=True)

    is_camera_on = webrtc_ctx and webrtc_ctx.state.playing

    with col_exam:
        if not is_camera_on:
            st.warning("⚠️ Đề thi đang bị ẩn. Vui lòng bật Camera (Nút START).")
        else:
            with st.form("exam_form_v3"):
                st.markdown("### 📝 Bài làm")
                answers = {}
                if not df_q.empty:
                    diag_q = df_q[~df_q['id'].str.startswith('CHECK_')]
                    skills = diag_q['skill_tag'].unique()
                    for skill in skills:
                        st.markdown(f"#### 🔹 {skill}")
                        for idx, row in diag_q[diag_q['skill_tag'] == skill].iterrows():
                            st.markdown(f"**Câu {row['id']}:** {row['question_text']}")
                            c = st.radio("Chọn:", [row['option_a'], row['option_b'], row['option_c'], row['option_d']], key=f"q_real_{row['id']}", horizontal=True, index=None)
                            if c:
                                map_ans = {row['option_a']:'A', row['option_b']:'B', row['option_c']:'C', row['option_d']:'D'}
                                answers[row['id']] = map_ans.get(c, 'A')
                            st.divider()
                
                if st.form_submit_button("📤 NỘP BÀI & LƯU KẾT QUẢ", type="primary", use_container_width=True, key="btn_submit_exam_final"):
                    cheat_count = webrtc_ctx.video_transformer.violation_count if webrtc_ctx.video_transformer else 0
                    cheat_log = webrtc_ctx.video_transformer.violation_log if webrtc_ctx.video_transformer else []
                    
                    analysis_result = assign_personalized_course(answers, diag_q, df_c)
                    
                    st.session_state['exam_result'] = analysis_result
                    st.session_state['my_course'] = analysis_result['recommended_course']
                    st.session_state['current_cheat_count'] = cheat_count
                    st.session_state['current_cheat_log'] = cheat_log
                    st.session_state['force_retake'] = False

                    save_thread = threading.Thread(target=save_learning_progress, args=(
                        user_id, analysis_result['recommended_course']['course_id'], 
                        analysis_result['total_score'], cheat_count, 0, cheat_log
                    ))
                    save_thread.start() 
                    st.rerun()
# --- BÀI THI CHECKPOINT (BẢN FIX TRIỆT ĐỂ LỖI SKILL_TAG & DASHBOARD) ---
def _render_checkpoint_quiz(user_id, course, skill_tag):
    st.markdown(f"### 🚩 BÀI THI CHECKPOINT: {skill_tag.upper()}")
    st.info("💡 Bạn cần trả lời đúng tối thiểu 80% để hoàn thành lộ trình học này.")
    
    # 1. Tải dữ liệu câu hỏi
    df_q, _ = load_data()
    
    if df_q.empty:
        st.error("❌ Không thể tải dữ liệu câu hỏi. Vui lòng kiểm tra kết nối Google Sheets!")
        return

    # CHIÊU CHỐNG LỖI KEYERROR: Chuẩn hóa tên cột để tìm đúng 'skill_tag'
    # Ép tất cả tên cột về chữ thường và xóa khoảng trắng thừa
    df_q.columns = [str(c).strip().lower() for c in df_q.columns]
    
    if 'skill_tag' not in df_q.columns:
        st.error(f"❌ Lỗi CSDL: Cột 'skill_tag' không tồn tại trong bảng QUESTIONS!")
        st.info(f"Các cột hiện có: {list(df_q.columns)}")
        return

    # Lọc danh sách câu hỏi theo môn học
    pool = df_q[df_q['skill_tag'] == skill_tag].to_dict('records')
    
    if not pool: 
        st.warning(f"⚠️ Chưa có bộ câu hỏi cho kỹ năng: {skill_tag}")
        return

    # 2. Giao diện bài thi
    with st.form(f"checkpoint_form_{skill_tag}"):
        user_ans = {}
        for i, q in enumerate(pool):
            st.write(f"**Câu {i+1}: {q['question_text']}**")
            # Tạo các lựa chọn từ option_a đến option_d
            options = [q.get('option_a'), q.get('option_b'), q.get('option_c'), q.get('option_d')]
            user_ans[q['id']] = st.radio(
                "Chọn đáp án:", 
                options, 
                key=f"cp_{q['id']}"
            )
        
        submit_button = st.form_submit_button("NỘP BÀI VÀ KẾT THÚC", type="primary", key="btn_submit_checkpoint")

    # 3. Xử lý sau khi nộp bài
    if submit_button:
        correct = 0
        for q in pool:
            # So khớp đáp án người dùng chọn với đáp án đúng (A, B, C, D)
            mapping = {
                "A": q.get('option_a'), 
                "B": q.get('option_b'), 
                "C": q.get('option_c'), 
                "D": q.get('option_d')
            }
            if user_ans[q['id']] == mapping.get(str(q.get('correct_opt')).strip().upper()):
                correct += 1
        
        # Tính toán điểm số
        final_percent = int((correct / len(pool)) * 100)
        
        # Ghi nhật ký hoạt động
        checkpoint_log = {
            "Thời gian": datetime.now().strftime("%H:%M:%S"), 
            "Lỗi": f"Hoàn thành Checkpoint {skill_tag}: {final_percent}%"
        }
        
        # ĐỒNG BỘ RAM LẬP TỨC để Dashboard không bị về 0
        st.session_state['history_score'] = final_percent
        st.session_state['cur_chapter_idx'] = 8 # Khóa ở Ngày 8
        st.session_state['viewing_idx'] = len(course.get('chapters', [])) - 1
        
        if 'current_cheat_log' in st.session_state:
            st.session_state['current_cheat_log'].append(checkpoint_log)

        with st.spinner("Đang chốt điểm số lên hệ thống Cloud..."):
            # LƯU CLOUD: Ép ghi điểm số và chương 8
            success = save_learning_progress(
                user_id=user_id, 
                course_id=course['course_id'], 
                score=final_percent, 
                cheat_count=0, 
                current_chapter=8, 
                violation_log=[checkpoint_log]
            )
        
        if success:
            if final_percent >= 80:
                st.success(f"🎉 Tuyệt vời! Bạn đạt {final_percent}%. Chúc mừng bạn đã tốt nghiệp!")
                st.balloons()
            else:
                st.error(f"⚠️ Kết quả: {final_percent}%. Bạn cần tối thiểu 80% để đạt yêu cầu.")
            
            # Đợi người dùng đọc thông báo rồi làm mới trang để cập nhật chứng chỉ
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ Lỗi ghi dữ liệu: Không thể kết nối với Google Sheets. Vui lòng thử lại!")
            
# --- REPORT CHI TIẾT ---
def _render_analysis_report(user_id):
    result = st.session_state.get('exam_result', {})
    if not result:
        st.error("Không tìm thấy kết quả bài thi."); return
        
    course = result.get('recommended_course', {})
    cheat_count = st.session_state.get('current_cheat_count', 0)
    cheat_log = st.session_state.get('current_cheat_log', [])
    
    st.markdown(f"""
    <div class="exam-header-container" style="background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);">
        <h2>📊 KẾT QUẢ VỪA THI: {result.get('total_score', 0)}/100</h2>
        <p>Dữ liệu đã được ghim vào lộ trình học tập của bạn.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if cheat_count > 0:
        st.error(f"⚠️ Hệ thống ghi nhận {cheat_count} hành vi nghi vấn.")
        with st.expander("🔎 Xem nhật ký vi phạm"):
            st.dataframe(pd.DataFrame(cheat_log), use_container_width=True)
    else:
        st.success("✅ Giám sát AI xác nhận: Không vi phạm quy chế.")

    col_skills, col_rec = st.columns([1.5, 1])
    with col_skills:
        st.subheader("🎯 Bản đồ năng lực")
        skill_data = result.get('skill_breakdown', {})
        if skill_data:
            df_skills = pd.DataFrame({
                "Kỹ năng": list(skill_data.keys()), 
                "Mức độ (%)": [s.get('score', 0) for s in skill_data.values()]
            })
            st.bar_chart(df_skills.set_index("Kỹ năng"))

    with col_rec:
        st.info(f"💡 Lộ trình: **{course.get('title', 'N/A')}**")
        st.write(f"Cần cải thiện: **{result.get('weakest_skill', 'N/A')}**")
        st.write(f"Số câu đúng: **{result.get('correct_count', 'N/A')}/{result.get('total_questions', 'N/A')}**")

    # CHI TIẾT ĐÚNG/SAI
    st.subheader("📝 Chi tiết bài làm")
    with st.expander("🔎 Xem chi tiết đáp án từng câu", expanded=True):
        details = result.get('details', [])
        for i, item in enumerate(details):
            icon = "✅" if item.get('is_correct') else "❌"
            st.markdown(f"**Câu {i+1}:** {item.get('question')}")
            if item.get('is_correct'):
                st.markdown(f"<span style='color:green;'>{icon} Bạn chọn đúng: **{item.get('user_opt')}**</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red;'>{icon} Bạn chọn: {item.get('user_opt')}</span> | 👉 Đáp án đúng: **{item.get('correct_opt')}**", unsafe_allow_html=True)
            st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 LÀM LẠI BÀI TEST", use_container_width=True, key="btn_retake_final"):
            st.session_state['exam_result'] = None; st.session_state['force_retake'] = True; st.rerun()
    with col_btn2:
        if st.button("🎓 VÀO HỌC NGAY", type="primary", use_container_width=True, key="btn_start_study_final"):
            # CHỐT CHẶN DỮ LIỆU: Ép RAM nhận tiến độ mới nhất để không bị văng về Ngày 1
            st.session_state['my_course'] = course
            st.session_state['cur_chapter_idx'] = 0
            st.session_state['viewing_idx'] = 0
            st.session_state['history_score'] = result['total_score']
            st.session_state['exam_result'] = None
            st.rerun()

# --- LỚP HỌC (FIXED UI & LOGGING CHI TIẾT) ---
def _render_classroom(user_id):
    course = st.session_state.get('my_course')
    if not course: st.warning("⚠️ Chưa có lộ trình học."); return

    st.markdown(f"""<div style="background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><h1>📚 {course['title']}</h1><p style="margin:5px 0 0 0; opacity: 0.9; font-style: italic;">Lộ trình được cá nhân hóa cho BA</p></div>""", unsafe_allow_html=True)

    max_unlocked_idx = st.session_state.get('cur_chapter_idx', 0)
    chapters = course.get('chapters', [])
    if not chapters: st.error("Dữ liệu khóa học trống."); return

    progress_percent = min(int((max_unlocked_idx / len(chapters)) * 100), 100)
    st.write(f"🚀 **Tiến độ tổng thể:** {progress_percent}%")
    st.progress(progress_percent / 100)

    # FIX VĂNG NGÀY: Đồng bộ viewing_idx luôn bám theo tiến độ cao nhất nếu vừa vào tab
    if st.session_state.get('viewing_idx', 0) >= len(chapters): 
        st.session_state['viewing_idx'] = max_unlocked_idx
    
    cur_view_idx = st.session_state.get('viewing_idx', max_unlocked_idx)
    col_nav, col_content = st.columns([1, 2.8])

    with col_nav:
        st.subheader("📅 Lộ trình")
        for idx, ch in enumerate(chapters):
            is_locked = idx > max_unlocked_idx
            is_done = idx < max_unlocked_idx
            icon = "🔒" if is_locked else "✅" if is_done else "▶️"
            btn_type = "primary" if idx == cur_view_idx else "secondary"
            if st.button(f"{icon} Ngày {ch['day']}: {ch['title'][:12]}...", key=f"nav_btn_{idx}", use_container_width=True, disabled=is_locked, type=btn_type):
                st.session_state['viewing_idx'] = idx; st.rerun()

    with col_content:
        active_day = chapters[cur_view_idx]
        c_main, c_ai = st.columns([2, 1])
        with c_main:
            st.markdown(f"### 📌 {active_day['title']}")
            st.divider()
            is_quiz_day = False
            for l_idx, lesson in enumerate(active_day.get('lessons', [])):
                l_key = f"lesson_{cur_view_idx}_{l_idx}"
                if lesson['type'] == 'Video': st.video(lesson['url'])
                elif lesson['type'] == 'Reading': st.info(f"📖 [Tài liệu: {lesson['title']}]({lesson['url']})")
                elif lesson['type'] == 'Practice':
                    st.markdown(f"#### 🛠️ Thực hành: {lesson['title']}")
                    st.warning(f"📝 **Yêu cầu:** {lesson['desc']}")
                    if course.get('skill_tag') in ['Coding', 'Database']:
                        st.text_area("Môi trường Sandbox", key=f"code_in_{l_key}", height=150)
                        if st.button("🚀 Nộp bài", key=f"btn_sub_{l_key}"):
                            # Ghi log nộp bài thực hành
                            practice_log = {"Thời gian": datetime.now().strftime("%H:%M:%S"), "Lỗi": f"Nộp bài thực hành: {lesson['title']}"}
                            save_learning_progress(user_id, course['course_id'], None, 0, max_unlocked_idx, violation_log=[practice_log])
                            st.success("✅ Đã ghi nhận bài làm!"); 
                    else: st.file_uploader("Nộp bài (.pdf, .png, .docx)", key=f"file_up_{l_key}")
                elif lesson['type'] == 'Quiz': is_quiz_day = True
            
            if is_quiz_day:
                current_score = st.session_state.get('history_score', 0)
                if cur_view_idx >= 7 and current_score >= 80: 
                    _render_graduation_ceremony(st.session_state.user_info, course, current_score)
                else: 
                    _render_checkpoint_quiz(user_id, course, course.get('skill_tag', 'Coding'))
            elif cur_view_idx == max_unlocked_idx:
                if st.button("✅ HOÀN THÀNH & TIẾP TỤC", type="primary", use_container_width=True, key="btn_finish_ch_main"):
                    next_idx = cur_view_idx + 1
                    
                    # TẠO LOG HOÀN THÀNH CHI TIẾT ĐỂ HIỂN THỊ Ở DASHBOARD
                    finish_log = {
                        "Thời gian": datetime.now().strftime("%H:%M:%S"), 
                        "Lỗi": f"Đã học xong: {active_day['title']}" 
                    }
                    
                    if next_idx < len(chapters):
                        with st.spinner("Đang lưu tiến độ..."):
                            # Lưu đồng bộ để chắc chắn dữ liệu và Log đã lên Cloud
                            success = save_learning_progress(user_id, course['course_id'], None, 0, next_idx, violation_log=[finish_log])
                            if success:
                                st.session_state.update({'cur_chapter_idx': next_idx, 'viewing_idx': next_idx})
                                st.balloons(); time.sleep(0.5); st.rerun()
                            else:
                                st.error("❌ Lỗi kết nối Cloud, vui lòng thử lại.")
                    else: 
                        st.success("🎉 Bạn đã hoàn thành tất cả các bài học. Hãy thực hiện bài thi tốt nghiệp ở chương cuối!")
        with c_ai:
            st.markdown("### 🤖 Trợ lý AI")
            render_ai_tutor(active_day['title'])

# --- TAB KHO TÀNG TRI THỨC (CHỈ HIỆN KHÓA ĐÃ TỐT NGHIỆP) ---
def _render_knowledge_archive(user_id):
    st.markdown("""
    <div style="background: linear-gradient(90deg, #6366F1 0%, #A855F7 100%); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;">
        <h2 style="margin:0;">📚 KHO TÀNG TRI THỨC</h2>
        <p style="margin:0; opacity:0.9;">Nơi lưu trữ các môn học bạn đã chinh phục</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Lấy dữ liệu tiến độ của User
    progress = get_user_progress(user_id)
    
    # CHIÊU CHẶN: Nếu chưa học gì HOẶC chương hiện tại nhỏ hơn 8 (chưa xong môn)
    # thì không hiện ở đây.
    is_finished = False
    if progress:
        # Kiểm tra nếu đã cán mốc chương 8 (Checkpoint)
        if int(float(progress.get('current_chapter', 0))) >= 8:
            is_finished = True

    if not is_finished:
        st.info("🌟 Kho tàng này hiện đang trống. Hãy hoàn thành bài thi Checkpoint (Ngày 8) để lưu môn học vào đây nhé!")
        return

    # 2. Nếu đã xong, mới tiến hành lấy dữ liệu để hiện
    _, df_c = load_data()
    finished_course_id = str(progress.get('course_id'))
    row = df_c[df_c['course_id'].astype(str) == finished_course_id]

    if not row.empty:
        selected_name = row.iloc[0]['title']
        st.success(f"🎊 Chúc mừng! Bạn đã chinh phục thành công: **{selected_name}**")
        
        try:
            course_data = json.loads(row.iloc[0]['data_json'])
            with st.expander(f"📖 Xem lại toàn bộ tài liệu môn {selected_name}", expanded=True):
                for ch in course_data.get('chapters', []):
                    st.markdown(f"#### 📁 {ch.get('title', 'Chương học')}")
                    for lesson in ch.get('lessons', []):
                        l_title = lesson.get('title', 'Bài học')
                        l_url = lesson.get('url', '#')
                        l_type = lesson.get('type', 'Reading')
                        
                        if l_type == 'Video':
                            st.write(f"▶️ [Video] {l_title}")
                            if l_url != '#': st.video(l_url)
                        else:
                            st.write(f"📖 [Tài liệu] [{l_title}]({l_url})")
                    st.divider()
        except:
            st.error("Lỗi định dạng dữ liệu khóa học.")