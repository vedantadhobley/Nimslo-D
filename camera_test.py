import subprocess
import os
from datetime import datetime

# Camera devices
CAMERA_DEVICES = ['/dev/video0', '/dev/video1', '/dev/video2', '/dev/video3']
RESOLUTION = '1920x1080'
PIX_FMT = 'yuyv422'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def set_camera_format(device_path):
    subprocess.run([
        'v4l2-ctl', '--device', device_path,
        '--set-fmt-video=width=1920,height=1080,pixelformat=YUYV'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

import time

def capture_from_camera(device_path, filename):
    raw_path = filename.replace('.jpg', '.raw')

    try:
        # Set format
        subprocess.run([
            'v4l2-ctl', '--device', device_path,
            '--set-fmt-video=width=1920,height=1080,pixelformat=YUYV'
        ], timeout=2, check=True)

        # Capture raw frame
        subprocess.run([
            'v4l2-ctl', '--device', device_path,
            '--stream-mmap', '--stream-count=1',
            f'--stream-to={raw_path}'
        ], timeout=5, check=True)

        # Convert to JPEG
        subprocess.run([
            'ffmpeg', '-y', '-f', 'rawvideo',
            '-pixel_format', PIX_FMT,
            '-video_size', RESOLUTION,
            '-i', raw_path, filename
        ], timeout=5, check=True)

        os.remove(raw_path)
        print(f"[OK] Captured {filename}")

    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout while capturing from {device_path}")
    except subprocess.CalledProcessError:
        print(f"[ERROR] Command failed for {device_path}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    time.sleep(1.0)  # Allow USB bus to settle


def create_wigglegram(image_paths, output_dir):
    ordered = image_paths + image_paths[-2:0:-1]
    list_file = os.path.join(output_dir, 'wiggle_list.txt')

    with open(list_file, 'w') as f:
        for path in ordered:
            f.write(f"file '{path}'\n")
            f.write("duration 0.15\n")
        f.write(f"file '{ordered[0]}'\n")  # Clean loop

    # MP4 output
    mp4_path = os.path.join(output_dir, 'wigglegram.mp4')
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-vsync', 'vfr',
        '-pix_fmt', 'yuv420p', mp4_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"MP4 wigglegram saved: {mp4_path}")

    # GIF output
    gif_path = os.path.join(output_dir, 'wigglegram.gif')
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-vf', 'fps=10,scale=640:-1:flags=lanczos',
        '-loop', '0', gif_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"GIF wigglegram saved: {gif_path}")

    os.remove(list_file)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(BASE_DIR, f"capture_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    image_paths = []

    for i, dev in enumerate(CAMERA_DEVICES):
        filename = os.path.join(output_dir, f'cam{i+1}.jpg')
        capture_from_camera(dev, filename)
        image_paths.append(filename)

    create_wigglegram(image_paths, output_dir)

if __name__ == "__main__":
    main()
