from datetime import datetime
import smtplib
import os
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch

# ==========================================
# 1. HÀM TẠO CHỨNG CHỈ PDF (TỐT NGHIỆP)
# ==========================================
def create_pdf_certificate(student_name, course_name, score):
    # CHIÊU CỨU CÁNH: Ép kiểu student_name về chuỗi để tránh lỗi .replace() với ID số
    name_str = str(student_name)
    file_path = f"Certificate_{name_str.replace(' ', '_')}.pdf"
    
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # 1. Vẽ viền kép sang trọng
    c.setStrokeColor(colors.goldenrod)
    c.setLineWidth(5)
    c.rect(20, 20, width-40, height-40) # Viền ngoài
    c.setLineWidth(2)
    c.rect(30, 30, width-60, height-60) # Viền trong

    # 2. Watermark EBSIS
    c.setFont("Helvetica-Bold", 60)
    c.setStrokeColor(colors.lightgrey)
    c.drawCentredString(width/2, height/2 + 100, "EBSIS") 

    # 3. Tiêu đề
    c.setFillColor(colors.darkblue)
    c.setFont("Times-BoldItalic", 45)
    c.drawCentredString(width/2, height - 150, "CERTIFICATE")
    
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 200, "OF COMPLETION")

    # 4. Nội dung xác nhận
    c.setFont("Times-Italic", 18)
    c.drawCentredString(width/2, height - 300, "This is to certify that")

    # Tên học viên (Làm nổi bật)
    c.setFont("Helvetica-Bold", 35)
    c.setFillColor(colors.darkred)
    c.drawCentredString(width/2, height - 360, name_str.upper())

    # Chi tiết khóa học
    c.setFillColor(colors.black)
    c.setFont("Times-Italic", 18)
    c.drawCentredString(width/2, height - 420, "has successfully mastered the course")
    
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height - 460, f"[{str(course_name).upper()}]")

    # 5. Điểm số và Ngày tháng
    c.setFont("Helvetica", 15)
    c.drawCentredString(width/2, height - 550, f"Final Performance Score: {score}%")
    
    today = datetime.now().strftime("%B %d, %Y")
    c.drawCentredString(width/2, height - 580, f"Issued on: {today}")

    # 6. Chữ ký giả định
    c.setLineWidth(1)
    c.line(width/2 - 100, height - 700, width/2 + 100, height - 700)
    c.setFont("Times-Italic", 12)
    c.drawCentredString(width/2, height - 715, "EBSIS Academic Director")

    c.save()
    return file_path

# ==========================================
# 2. HÀM GỬI EMAIL TỐT NGHIỆP
# ==========================================
def send_graduation_email(receiver_email, student_name, course_name, final_score):
    sender_email = "luuanhthuwannaone@gmail.com"  # Email của Thư
    password = "svetjdyknbtyuhlg"                # App Password

    # Tạo file PDF
    pdf_file = create_pdf_certificate(student_name, course_name, final_score)

    # Cấu hình Email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🎓 Chúc mừng {student_name} tốt nghiệp khóa {course_name}!"

    body = f"Chào {student_name},\n\nChúc mừng bạn đã hoàn thành xuất sắc khóa học {course_name}. Vui lòng xem chứng chỉ đính kèm dưới đây.\n\nTrân trọng,\nEBSIS Academic Team"
    msg.attach(MIMEText(body, 'plain'))

    # Đính kèm file PDF
    try:
        with open(pdf_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {pdf_file}")
            msg.attach(part)

        # Gửi Mail qua SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        # Xóa file tạm sau khi gửi
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
            
        return True, "Đã gửi mail kèm chứng chỉ!"
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. HÀM TẠO PDF NHẬN XÉT (INSIGHT REPORT)
# ==========================================
def generate_insight_pdf(user_name, score, chap, cheats):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 1. Trang trí tiêu đề
    c.setFillColor(colors.darkblue)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "EBSIS LEARNING ANALYTICS REPORT")
    
    # 2. Thông tin học viên
    c.setStrokeColor(colors.lightgrey)
    c.line(50, height - 70, width - 50, height - 70)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 100, f"Student Name: {str(user_name)}")
    c.drawString(50, height - 120, f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 3. Chỉ số KPI
    c.setFont("Helvetica", 12)
    c.rect(50, height - 250, 500, 100)
    c.drawString(70, height - 180, f"- Logic/IQ Score: {score}%")
    c.drawString(70, height - 200, f"- Course Progress: {chap}/8 Chapters")
    c.drawString(70, height - 220, f"- Integrity Index: {max(0, 100-(cheats*5))}% (AI Monitored)")

    # 4. Nhận xét từ AI
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 300, "AI Behavioral Insights:")
    c.setFont("Helvetica-Oblique", 11)
    text = f"The student shows strong focus in logic-based modules. Cheat count: {cheats}."
    c.drawString(50, height - 320, text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer