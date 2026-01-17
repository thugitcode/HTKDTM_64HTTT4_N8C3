import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

# --- CẤU HÌNH ĐƯỜNG DẪN TUYỆT ĐỐI ---
# Giúp code luôn tìm thấy file credentials.json dù bạn chạy code ở đâu
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Thư mục chứa file này (src/services)
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR)) # Thư mục gốc dự án
KEY_FILE = os.path.join(ROOT_DIR, 'credentials.json')

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_connection():
    """Hàm kết nối tới Google Sheets"""
    try:
        if not os.path.exists(KEY_FILE):
            st.error(f"❌ Lỗi: Không tìm thấy file key tại: {KEY_FILE}")
            print(f"❌ Lỗi: Không tìm thấy file key tại: {KEY_FILE}")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        err_msg = f"❌ Lỗi kết nối Google API: {e}"
        # In ra terminal để dễ debug
        print(err_msg)
        try:
            st.error(err_msg)
        except:
            pass
        return None

def get_all_users():
    """Hàm lấy danh sách User từ Sheet USERS"""
    client = get_connection()
    if client:
        try:
            sheet = client.open("Ebsis_DB").worksheet("USERS")
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Lỗi đọc sheet USERS: {e}")
            return pd.DataFrame()
    return pd.DataFrame()