import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

# Đường dẫn đến file chìa khóa
KEY_FILE = 'credentials.json'
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_connection():
    """Hàm kết nối tới Google Sheets"""
    try:
        # Kiểm tra xem file key có tồn tại không
        if not os.path.exists(KEY_FILE):
            st.error(f"❌ Lỗi: Không tìm thấy file '{KEY_FILE}'. Bạn đã bỏ nó vào thư mục dự án chưa?")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {e}")
        return None

def get_all_users():
    """Hàm lấy danh sách User từ Sheet USERS"""
    client = get_connection()
    if client:
        try:
            # Mở file sheet theo tên
            sheet = client.open("Ebsis_DB").worksheet("USERS")
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.warning(f"Không đọc được dữ liệu: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Test thử xem chạy được không (Chỉ chạy khi run file này trực tiếp)
if __name__ == "__main__":
    print("Đang thử kết nối...")
    df = get_all_users()
    print("Kết quả lấy được:")
    print(df)