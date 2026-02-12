import cv2
import os

# CHANGED: Default fps from 30 to 6 to match the "1 frame every 5" extraction rate.
def reconstruct_video_from_frames(frames_dir, output_path, fps=6):
    """
    Reads all .png frames from the directory and stitches them into an .mp4 video.
    """
    try:
        # 1. Get all frames
        if not os.path.exists(frames_dir):
            print(f"Frames directory not found: {frames_dir}")
            return False

        images = [img for img in os.listdir(frames_dir) if img.endswith(".png")]
        
        # 2. Sort them numerically (frame_0, frame_1, ... frame_10)
        images.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

        if not images:
            print("No frames found to reconstruct.")
            return False

        # 3. Read first frame to get size
        frame_path = os.path.join(frames_dir, images[0])
        frame = cv2.imread(frame_path)
        height, width, layers = frame.shape

        # 4. Initialize Video Writer
        # We use the updated 'fps' (6) here so the video plays at normal speed.
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # 5. Write frames
        for image in images:
            img_path = os.path.join(frames_dir, image)
            video.write(cv2.imread(img_path))

        cv2.destroyAllWindows()
        video.release()
        return True

    except Exception as e:
        print(f"Error reconstructing video: {e}")
        return False