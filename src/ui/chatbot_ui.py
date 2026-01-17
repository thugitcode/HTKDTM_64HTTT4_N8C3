import streamlit as st
from src.services.dify_client import chat_with_dify

def render_ai_tutor(current_lesson_title):
    """
    Hiển thị khung chat AI bên phải màn hình
    """
    user_info = st.session_state.get('user_info', {})
    user_id = user_info.get('user_id', 'guest_user')

    st.markdown("""
    <style>
        .chat-header {
            color: #0F172A;
            font-weight: 700;
            padding: 10px 0;
            border-bottom: 2px solid #E2E8F0;
            margin-bottom: 15px;
        }
        div[data-testid="stChatMessage"] {
            padding: 10px;
            border-radius: 12px;
            margin-bottom: 8px;
        }
        div[data-testid="stChatMessage"][data-testid="user"] {
            background-color: #DBEAFE;
        }
        div[data-testid="stChatMessage"][data-testid="assistant"] {
            background-color: #F1F5F9;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='chat-header'>🤖 AI Tutor: {current_lesson_title}</div>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Chào bạn! Tôi có thể giúp gì về bài **{current_lesson_title}**?"}
        ]
    
    if "dify_conv_id" not in st.session_state:
        st.session_state.dify_conv_id = ""

    chat_container = st.container(height=500)

    with chat_container:
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Nhập câu hỏi của bạn...", key="chat_input_area"):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user").write(prompt)

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("AI đang suy nghĩ..."):
                    
                    response = chat_with_dify(
                        query=prompt, 
                        user_id=user_id, 
                        conversation_id=st.session_state.dify_conv_id
                    )
                    
                    if response["status"] == "success":
                        bot_reply = response["answer"]
                        st.session_state.dify_conv_id = response["conversation_id"]
                    else:
                        bot_reply = f"⚠️ {response['answer']}"

                    st.write(bot_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})