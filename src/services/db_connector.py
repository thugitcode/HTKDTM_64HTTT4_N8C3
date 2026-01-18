import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

# --- CẤU HÌNH ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
KEY_FILE = os.path.join(ROOT_DIR, 'credentials.json')
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource # CHIÊU THỨ 1: Giữ kết nối vĩnh viễn trong 1 phiên làm việc
def get_connection():
    try:
        if not os.path.exists(KEY_FILE): return None
        creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        return None

def get_all_users():
    """Lấy danh sách User (Ưu tiên dùng Cache)"""
    client = get_connection()
    if client:
        try:
            # Chỉ đọc dữ liệu từ Cloud nếu chưa có trong bộ nhớ tạm
            sheet = client.open("Ebsis_DB").worksheet("USERS")
            return pd.DataFrame(sheet.get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()