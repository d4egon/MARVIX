import cv2
import os
import datetime
import threading
import mediapipe as mp

class KyrethysVision:
    def __init__(self):
        self.camera_on = True 
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'snapshots')
        self.last_frame = None
        self.lock = threading.Lock()

        # --- MediaPipe Setup ---
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.latest_expression_summary = "Neutral" # Default state
        # -----------------------

        if not os.path.exists(self.snapshot_path):
            os.makedirs(self.snapshot_path)

    def toggle_camera(self, state):
        self.camera_on = state
        if state:
            if not self.camera.isOpened():
                self.camera.open(0)
            print("--- Kyrethys opened his eyes ---")
        else:
            print("--- Kyrethys closed his eyes ---")

    def analyze_face(self, landmarks):
        """
        Translates raw landmark dots into a human-readable string.
        Kyrethys uses this string to 'understand' your face.
        """
        # Example logic: Detect smile via mouth corner distance (Landmarks 61 and 291)
        upper_lip = landmarks.landmark[13]
        lower_lip = landmarks.landmark[14]
        mouth_opening = abs(upper_lip.y - lower_lip.y)
        
        if mouth_opening > 0.05:
            return "Speaking/Surprised"
        
        # You can add more complex math here for brows, eyes, etc.
        return "Calm/Observing"

    def analyze_face(self, landmarks):
        """Return a short emotional summary Kyrethys can understand"""
        if not landmarks:
            return "Neutral"
        
        # Simple but effective: mouth + eye tension
        upper_lip = landmarks.landmark[13].y
        lower_lip = landmarks.landmark[14].y
        mouth_open = abs(upper_lip - lower_lip)
        
        if mouth_open > 0.06:
            return "Speaking / Surprised"
        elif mouth_open > 0.03:
            return "Smiling"
        else:
            return "Calm / Focused"

    def take_snapshot(self):
        with self.lock:
            if self.last_frame is not None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snap_{timestamp}.jpg"
                full_path = os.path.join(self.snapshot_path, filename)
                cv2.imwrite(full_path, self.last_frame)
                
                return {
                    "filename": filename,
                    "expression": self.latest_expression_summary
                }
        return {"filename": None, "expression": "No frame"}

    def generate_frames(self):
        while True:
            if not self.camera_on:
                continue

            success, frame = self.camera.read()
            if not success: 
                break
            
            frame = cv2.flip(frame, -1)
            
            # --- Face Detection Logic ---
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                self.latest_expression_summary = self.analyze_face(landmarks)
                
                # Optional: Draw the dots on the live feed for debugging
                # mp.solutions.drawing_utils.draw_landmarks(frame, landmarks)
            # ----------------------------

            with self.lock:
                self.last_frame = frame.copy()
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    def __del__(self):
        if hasattr(self, 'camera') and self.camera.isOpened():
            self.camera.release()