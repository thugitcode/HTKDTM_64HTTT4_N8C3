import sys
import os
from datetime import datetime
import json

# Setup đường dẫn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.db_connector import get_connection

def test_write_google_sheet():
    print("🚀 ĐANG KẾT NỐI GOOGLE SHEETS...")
    
    # 1. Lấy kết nối
    client = get_connection()
    if not client:
        print("❌ LỖI: Không tìm thấy file credentials.json hoặc cấu hình sai!")
        return

    try:
        # 2. Mở File Sheet
        print("📂 Đang mở file 'Ebsis_DB'...")
        sh = client.open("Ebsis_DB")
        
        # 3. Mở (hoặc tạo) Tab PROGRESS
        try:
            ws = sh.worksheet("PROGRESS")
            print("✅ Đã tìm thấy tab 'PROGRESS'")
        except:
            print("⚠️ Chưa có tab PROGRESS, đang tạo mới...")
            ws = sh.add_worksheet("PROGRESS", 1000, 10)
            ws.append_row(["user_id", "course_id", "score", "cheat_count", "current_chapter", "last_updated", "violation_details"])

        # 4. Ghi thử dữ liệu mẫu
        print("✍️ Đang ghi dòng test...")
        fake_data = [
            "TEST_USER_001", 
            "TEST_COURSE", 
            100, 
            5, 
            1, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            json.dumps([{"Lỗi": "Test Log"}])
        ]
        
        ws.append_row(fake_data)
        print("🎉 THÀNH CÔNG! Hãy mở Google Sheet và kiểm tra dòng cuối cùng.")
        
    except Exception as e:
        print("\n❌ GHI THẤT BẠI! Nguyên nhân:")
        print(f"👉 {e}")
        
        if "SpreadsheetNotFound" in str(e):
            print("💡 GỢI Ý: Bạn đã đổi tên file Sheet chưa? Hoặc chưa Share quyền cho Service Account?")
        if "PERMISSION_DENIED" in str(e) or "403" in str(e):
            print("💡 GỢI Ý: Bạn CHƯA SHARE file Sheet cho email trong credentials.json!")

if __name__ == "__main__":
    test_write_google_sheet()