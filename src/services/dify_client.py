import requests
import json
import streamlit as st

DIFY_BASE_URL = "https://page-greyish-setaceously.ngrok-free.dev/v1"

DIFY_API_KEY = "app-QEf2ApMSVRWQPr33SUOnWxM1" 

def chat_with_dify(query, user_id, conversation_id=None):
    """
    Gửi tin nhắn sang Dify và nhận phản hồi (Dựa trên Request Body chuẩn)
    """
    url = f"{DIFY_BASE_URL}/chat-messages"

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {}, 
        "query": query,
        "response_mode": "blocking", 
        "conversation_id": conversation_id if conversation_id else "",
        "user": str(user_id),
        "files": [] 
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()

            return {
                "status": "success",
                "answer": data.get('answer', 'Không có nội dung trả lời.'),
                "conversation_id": data.get('conversation_id', ''),
                "usage": data.get('metadata', {}).get('usage', {})
            }
        else:
            return {
                "status": "error",
                "answer": f"Lỗi API ({response.status_code}): {response.text}",
                "conversation_id": conversation_id
            }

    except Exception as e:
        return {
            "status": "error",
            "answer": f"Lỗi kết nối tới Dify: {str(e)}\n(Gợi ý: Nếu đang dùng WSL, hãy thử đổi URL thành http://host.docker.internal/v1)",
            "conversation_id": conversation_id
        }