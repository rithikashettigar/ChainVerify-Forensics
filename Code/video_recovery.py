import cv2
import os

def recover_video(original_frames_dir, output_path, fps=10):
    frame_files = sorted(
        [f for f in os.listdir(original_frames_dir) if f.endswith(".png")],
        key=lambda x: int(x.split("_")[1].split(".")[0])
    )

    if not frame_files:
        return False

    first_frame = cv2.imread(os.path.join(original_frames_dir, frame_files[0]))
    height, width, _ = first_frame.shape

    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    for frame_file in frame_files:
        frame = cv2.imread(os.path.join(original_frames_dir, frame_file))
        out.write(frame)

    out.release()
    return True
