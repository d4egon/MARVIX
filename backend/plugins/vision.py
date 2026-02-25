import cv2
import os
import datetime
import threading # Tilføjet for at sikre trådsikkerhed

class MarvixVision:
    def __init__(self):
        self.camera_on = True # Default state
        self.cap = None
        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'snapshots')
        
        # Gem den sidste frame her for at undgå hardware-konflikt
        self.last_frame = None
        self.lock = threading.Lock() # Sikrer at vi ikke læser/skriver samtidigt

        if not os.path.exists(self.snapshot_path):
            os.makedirs(self.snapshot_path)

    def toggle_camera(self, state):
        self.camera_on = state
        # Use getattr to safely check for the attribute
        cap = getattr(self, 'cap', None)
        
        if not state and cap:
            cap.release()
            self.cap = None # Clear it after releasing
            print("--- Marvix closed his eyes ---")
        elif state:
            import cv2
            self.cap = cv2.VideoCapture(0)
            print("--- Marvix opened his eyes ---")

    def take_snapshot(self): # Omdøbt fra capture_snapshot så det matcher dit kald i backend
        with self.lock:
            if self.last_frame is not None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snap_{timestamp}.jpg"
                full_path = os.path.join(self.snapshot_path, filename)
                cv2.imwrite(full_path, self.last_frame)
                print(f"DEBUG: Snapshot gemt: {filename}")
                return filename 
        return None

    def generate_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success: 
                break
            
            # Vend billedet rigtigt
            frame = cv2.flip(frame, -1)
            
            # Opdater 'last_frame' så snapshot-funktionen har noget at arbejde med
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