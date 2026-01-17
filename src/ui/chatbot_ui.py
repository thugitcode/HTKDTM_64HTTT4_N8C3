import streamlit as st
import time
import random

def render_ai_tutor(current_lesson_title):
    """
    Hiển thị giao diện Chatbot AI (Ebsis Bot)
    """
    # CSS cho khung chat đẹp hơn
    st.markdown("""
    <style>
        .chat-header {
            font-weight: bold;
            color: #2563EB;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='chat-header'>🤖 Trợ lý AI (Hỗ trợ bài: {current_lesson_title})</div>", unsafe_allow_html=True)

    # 1. Khởi tạo lịch sử chat trong Session
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"Chào bạn! Tôi là trợ lý ảo AI. Bạn có thắc mắc gì về bài học **'{current_lesson_title}'** không?"}
        ]

    # 2. Hiển thị lịch sử chat (Dùng container để có thanh cuộn)
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

    # 3. Khung nhập liệu (Chat Input)
    if prompt := st.chat_input("Hỏi tôi về bài học này..."):
        # Hiển thị câu hỏi của User
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user").write(prompt)

        # AI Trả lời (Giả lập logic thông minh)
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("AI đang suy nghĩ..."):
                    time.sleep(1) # Delay giả lập độ trễ mạng
                    
                    # Logic trả lời đơn giản (Rule-based)
                    response = ""
                    prompt_lower = prompt.lower()
                    
                    if "xin chào" in prompt_lower or "hi" in prompt_lower:
                        response = "Chào bạn! Chúc bạn một ngày học tập hiệu quả."
                    elif "khó" in prompt_lower or "không hiểu" in prompt_lower:
                        response = f"Đừng lo lắng! Bài '{current_lesson_title}' có một số concept trừu tượng. Bạn hãy thử xem lại video từ phút thứ 2 nhé."
                    elif "giải thích" in prompt_lower or "là gì" in prompt_lower:
                        response = f"Dựa trên ngữ cảnh bài học, khái niệm này được hiểu là cách máy tính xử lý dữ liệu đầu vào..."
                    elif "code" in prompt_lower or "ví dụ" in prompt_lower:
                        response = "Đây là một ví dụ minh họa cho bạn:\n```python\ndef hello():\n    print('Ebsis AI Tutor')\n```"
                    else:
                        list_answers = [
                            "Câu hỏi rất hay! Theo tài liệu thì vấn đề này liên quan đến cấu trúc dữ liệu.",
                            "Bạn có thể tham khảo thêm ở mục 'Tài liệu đọc thêm' nhé.",
                            "Chính xác! Tư duy của bạn rất tốt.",
                            "Tôi hiểu ý bạn. Hãy thử thực hành bài Lab số 1 để hiểu rõ hơn."
                        ]
                        response = random.choice(list_answers)
                    
                    st.write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})