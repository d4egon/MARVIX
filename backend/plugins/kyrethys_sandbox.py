import cv2

def find_cameras(limit=5):
    active_cameras = []
    print("Søger efter kameraer... Tryk 'q' for at lukke et vindue.")

    for i in range(limit):
        # Vi bruger CAP_DSHOW for at undgå langsom opstart på Windows
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"[SUCCESS] Kamera fundet på indeks: {i}")
            active_cameras.append(i)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                cv2.imshow(f'Kamera Test - Indeks {i}', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        else:
            print(f"[FEJL] Intet kamera på indeks: {i}")
    return active_cameras

if __name__ == "__main__":
    found = find_cameras()
    print(f"\nFærdig! Fundne indeks: {found}")