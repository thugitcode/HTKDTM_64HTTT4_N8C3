import cv2
import numpy as np
import mediapipe as mp

class FaceEngine:
    def __init__(self):
        # --- CÁCH KHỞI TẠO CHUẨN ---
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Cấu hình Face Mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,       # Chế độ ảnh tĩnh (vì mình chụp ảnh)
            max_num_faces=1,              # Chỉ lấy 1 mặt
            refine_landmarks=True,        # Lấy chi tiết mắt/môi
            min_detection_confidence=0.5
        )

    def process_image(self, image_file):
        """
        Chuyển đổi file ảnh từ Streamlit (Bytes) sang định dạng OpenCV
        """
        # Đọc file thành mảng bytes
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        # Decode thành ảnh
        image = cv2.imdecode(file_bytes, 1)
        # Chuyển từ BGR (OpenCV) sang RGB (MediaPipe)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def get_face_embedding(self, image_rgb):
        """
        Quét khuôn mặt và trả về 'Vector đặc trưng' (Dãy số tọa độ)
        """
        results = self.face_mesh.process(image_rgb)
        
        # Nếu không tìm thấy mặt nào
        if not results.multi_face_landmarks:
            return None 
        
        # Lấy khuôn mặt đầu tiên tìm thấy
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Chọn các điểm mốc quan trọng (Keypoints) để định danh
        # (Mắt trái, Mắt phải, Mũi, Miệng, Cằm...)
        key_indices = [1, 33, 61, 199, 263, 291, 0, 11, 13, 14, 17, 152]
        
        embedding = []
        for idx in key_indices:
            pt = landmarks[idx]
            # Lưu tọa độ x, y, z
            embedding.extend([pt.x, pt.y, pt.z])
            
        return np.array(embedding)

    def compare_faces(self, known_embedding, new_embedding, threshold=0.1):
        """
        So sánh 2 vector khuôn mặt.
        - threshold: Ngưỡng sai số (Càng nhỏ càng khắt khe).
        """
        if known_embedding is None or new_embedding is None:
            return False
            
        # Tính khoảng cách Euclidean (Khoảng cách giữa 2 điểm trong không gian)
        diff = np.linalg.norm(known_embedding - new_embedding)
        
        # Nếu khoảng cách nhỏ hơn ngưỡng -> Là cùng 1 người
        return diff < threshold
    
    def detect_head_pose(self, image_rgb):
        """Phát hiện gian lận (Quay đầu)"""
        results = self.face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            return "Không tìm thấy mặt"

        img_h, img_w, _ = image_rgb.shape
        face_landmarks = results.multi_face_landmarks[0]

        # 1. Lấy tọa độ 2D và 3D của các điểm mốc
        points_2d = []
        points_3d = []
        key_indices = [1, 152, 33, 263, 61, 291] # Mũi, Cằm, Mắt trái/phải, Miệng trái/phải
        
        for idx in key_indices:
            lm = face_landmarks.landmark[idx]
            x, y = int(lm.x * img_w), int(lm.y * img_h)
            points_2d.append([x, y])
            points_3d.append([x, y, lm.z])

        points_2d = np.array(points_2d, dtype=np.float64)
        points_3d = np.array(points_3d, dtype=np.float64)

        # 2. Giả lập Camera Matrix
        focal_length = 1 * img_w
        cam_matrix = np.array([[focal_length, 0, img_h / 2],
                               [0, focal_length, img_w / 2],
                               [0, 0, 1]])
        dist_matrix = np.zeros((4, 1), dtype=np.float64)

        # 3. Giải bài toán PnP để tìm góc quay
        success, rot_vec, trans_vec = cv2.solvePnP(points_3d, points_2d, cam_matrix, dist_matrix)
        rmat, jac = cv2.Rodrigues(rot_vec)
        
        # --- ĐÂY LÀ DÒNG BỊ LỖI (ĐÃ SỬA) ---
        # Hàm này trả về 6 giá trị: angles, mtxR, mtxQ, Qx, Qy, Qz
        angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

        # 4. Phân tích góc quay (Đơn vị: độ)
        # x: Pitch (Lên/Xuống), y: Yaw (Trái/Phải), z: Roll (Nghiêng)
        pitch = angles[0] * 360 
        yaw = angles[1] * 360   
        
        if yaw < -10: return "Quay phải ⚠️"
        elif yaw > 10: return "Quay trái ⚠️"
        elif pitch < -8: return "Cúi xuống ⚠️"
        elif pitch > 10: return "Ngước lên ⚠️"
        
        return "Nhìn thẳng ✅"