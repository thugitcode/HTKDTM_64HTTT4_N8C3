import streamlit as st

def load_custom_css():
    st.markdown("""
    <style>
        /* 1. FONT & BODY */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* 2. CUSTOM BUTTONS (Nút bấm xịn) */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease-in-out;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        /* Nút chính (Primary) */
        button[kind="primary"] {
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
            color: white;
        }

        /* 3. CARD CONTAINER (Khung chứa nội dung) */
        .st-card {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
            border: 1px solid #E2E8F0;
        }

        /* 4. EXAM HEADER (Tiêu đề phòng thi) */
        .exam-header-container {
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
            text-align: center;
        }

        /* 5. SIDEBAR ITEM (Mục lục khóa học) */
        .sidebar-item {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .sidebar-item:hover {
            background-color: #F1F5F9;
        }
        .sidebar-item.active {
            background-color: #EFF6FF;
            border-left: 4px solid #2563EB;
            color: #1D4ED8;
            font-weight: bold;
        }
        .sidebar-item.locked {
            opacity: 0.6;
            cursor: not-allowed;
            background-color: #F8FAFC;
        }

        /* 6. STATUS BADGES */
        .badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-danger { background-color: #FEE2E2; color: #DC2626; }
        .badge-success { background-color: #DCFCE7; color: #16A34A; }

        /* Ẩn cái Menu Hamburger mặc định của Streamlit cho pro */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)