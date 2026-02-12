import cv2
import os

def extract_frames(video_path, output_dir, every_n_frames=5):
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    frames = []

    index = 0
    saved_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if index % every_n_frames == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_index}.png")
            cv2.imwrite(frame_path, frame)
            frames.append((saved_index, frame_path))
            saved_index += 1

        index += 1

    cap.release()
    return frames
