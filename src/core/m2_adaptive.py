import pandas as pd
import json
import streamlit as st
from src.services.db_connector import get_connection

@st.cache_data(ttl=60)
def load_data():
    """Load câu hỏi và khung chương trình từ Sheet"""
    try:
        client = get_connection()
        q_data = client.open("Ebsis_DB").worksheet("QUESTIONS").get_all_records()
        c_data = client.open("Ebsis_DB").worksheet("CURRICULUM").get_all_records()
        return pd.DataFrame(q_data), pd.DataFrame(c_data)
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

def analyze_and_generate_path(user_answers, df_questions, df_curriculum):
    """
    ENGINE PHÂN TÍCH LỘ TRÌNH (RULE-BASED AI)
    """
    # 1. Chấm điểm từng kỹ năng
    scores = {'Coding': 0, 'Database': 0, 'Network': 0, 'SE': 0}
    max_scores = {'Coding': 0, 'Database': 0, 'Network': 0, 'SE': 0}
    
    # Duyệt qua các câu hỏi đã làm
    for q_id, choice in user_answers.items():
        # Tìm thông tin câu hỏi trong DB
        row = df_questions[df_questions['id'] == q_id]
        if row.empty: continue
        
        row = row.iloc[0]
        tag = row['skill_tag']
        
        max_scores[tag] = max_scores.get(tag, 0) + 1
        if choice == row['correct_opt']:
            scores[tag] = scores.get(tag, 0) + 1
            
    # Tính % năng lực (0-100)
    performance = {}
    for tag in max_scores:
        if max_scores[tag] > 0:
            performance[tag] = round((scores[tag] / max_scores[tag]) * 100)
        else:
            performance[tag] = 0

    # 2. Xây dựng lộ trình (Mapping điểm số -> Hành động)
    personalized_path = []
    
    if not df_curriculum.empty:
        for _, row in df_curriculum.iterrows():
            topic = row['topic']
            user_score = performance.get(topic, 0)
            
            # --- LUẬT CỦA AI (AI RULES) ---
            if user_score < 50:
                status = "🔴 CẤP THIẾT (Yếu)"
                action = "Bạn đang hổng kiến thức phần này. Yêu cầu học kỹ video và làm lại bài tập."
                color = "red"
                is_open = True # Tự động mở bài học ra đập vào mắt
            elif user_score < 80:
                status = "🟡 CẦN CẢI THIỆN (Khá)"
                action = "Kiến thức nền ổn, nhưng còn sai sót tiểu tiết. Nên xem lại tài liệu đọc."
                color = "orange"
                is_open = False
            else:
                status = "🟢 HOÀN THÀNH (Tốt)"
                action = "Bạn đã nắm vững module này. Có thể lướt qua để tiết kiệm thời gian."
                color = "green"
                is_open = False
                
            # Parse tài liệu từ JSON string
            try: materials = json.loads(row['materials_json'])
            except: materials = []
            
            week_item = {
                "week": row['week'],
                "title": row['title'],
                "description": row['description'],
                "score": user_score,
                "status": status,
                "action": action,
                "color": color,
                "is_open": is_open,
                "materials": materials
            }
            personalized_path.append(week_item)
        
    return performance, personalized_path