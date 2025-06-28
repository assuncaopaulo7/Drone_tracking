# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

import time
from typing import Tuple

import cv2

from ultralytics import YOLO
from ultralytics.utils import LOGGER
from ultralytics.utils.plotting import Annotator, colors

enable_gpu = False  # Set True if running with CUDA
model_file = "yolo11s.pt"  # Path to model file
show_fps = False  # FPS não faz sentido para imagem única
show_conf = False  # Display or hide the confidence score
save_image = True  # Salvar imagem anotada
image_output_path = "interactive_tracker_output.png"  # Output image file name

conf = 0.3  # Min confidence for object detection (lower = more detections, possibly more false positives)
iou = 0.3  # IoU threshold for NMS (higher = less overlap allowed)
max_det = 20  # Maximum objects per image (increase for crowded scenes)

tracker = "bytetrack.yaml"  # Tracker config: 'bytetrack.yaml', 'botsort.yaml', etc.
track_args = {
    "persist": True,  # Keep frames history as a stream for continuous tracking
    "verbose": False,  # Print debug info from tracker
}

window_name = "Ultralytics YOLO Interactive Tracking"  # Output window name

LOGGER.info("🚀 Initializing model...")
if enable_gpu:
    LOGGER.info("Using GPU...")
    model = YOLO(model_file)
    model.to("cuda")
else:
    LOGGER.info("Using CPU...")
    model = YOLO(model_file, task="detect")

classes = model.names  # Store model class names

im = cv2.imread("/home/marcos/Pictures/Screenshots/Screenshot from 2025-02-24 10-46-25.png")
if im is None:
    raise ValueError("Imagem não encontrada!")

selected_object_id = None
selected_bbox = None
selected_center = None

def get_center(x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int]:
    return (x1 + x2) // 2, (y1 + y2) // 2

def extend_line_from_edge(mid_x: int, mid_y: int, direction: str, img_shape: Tuple[int, int, int]) -> Tuple[int, int]:
    h, w = img_shape[:2]
    if direction == "left":
        return 0, mid_y
    if direction == "right":
        return w - 1, mid_y
    if direction == "up":
        return mid_x, 0
    if direction == "down":
        return mid_x, h - 1
    return mid_x, mid_y

def draw_tracking_scope(im, bbox: tuple, color: tuple) -> None:
    x1, y1, x2, y2 = bbox
    mid_top = ((x1 + x2) // 2, y1)
    mid_bottom = ((x1 + x2) // 2, y2)
    mid_left = (x1, (y1 + y2) // 2)
    mid_right = (x2, (y1 + y2) // 2)
    cv2.line(im, mid_top, extend_line_from_edge(*mid_top, "up", im.shape), color, 2)
    cv2.line(im, mid_bottom, extend_line_from_edge(*mid_bottom, "down", im.shape), color, 2)
    cv2.line(im, mid_left, extend_line_from_edge(*mid_left, "left", im.shape), color, 2)
    cv2.line(im, mid_right, extend_line_from_edge(*mid_right, "right", im.shape), color, 2)

def click_event(event: int, x: int, y: int, flags: int, param) -> None:
    global selected_object_id
    if event == cv2.EVENT_LBUTTONDOWN:
        detections = results[0].boxes.data if results[0].boxes is not None else []
        if detections is not None:
            min_area = float("inf")
            best_match = None
            for track in detections:
                track = track.tolist()
                if len(track) >= 6:
                    x1, y1, x2, y2 = map(int, track[:4])
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        area = (x2 - x1) * (y2 - y1)
                        if area < min_area:
                            class_id = int(track[-1])
                            track_id = int(track[4]) if len(track) == 7 else -1
                            min_area = area
                            best_match = (track_id, model.names[class_id])
            if best_match:
                selected_object_id, label = best_match
                print(f"🔵 TRACKING STARTED: {label} (ID {selected_object_id})")

# Processa a imagem única
results = model.track(im, conf=conf, iou=iou, max_det=max_det, tracker=tracker, **track_args)
annotator = Annotator(im)
detections = results[0].boxes.data if results[0].boxes is not None else []
detected_objects = []
for track in detections:
    track = track.tolist()
    if len(track) < 6:
        continue
    x1, y1, x2, y2 = map(int, track[:4])
    class_id = int(track[6]) if len(track) >= 7 else int(track[5])
    track_id = int(track[4]) if len(track) == 7 else -1
    color = colors(track_id, True)
    txt_color = annotator.get_txt_color(color)
    label = f"{classes[class_id]} ID {track_id}" + (f" ({float(track[5]):.2f})" if show_conf else "")
    if track_id == selected_object_id:
        draw_tracking_scope(im, (x1, y1, x2, y2), color)
        center = get_center(x1, y1, x2, y2)
        cv2.circle(im, center, 6, color, -1)
        pulse_radius = 8 + int(4 * abs(time.time() % 1 - 0.5))
        cv2.circle(im, center, pulse_radius, color, 2)
        annotator.box_label([x1, y1, x2, y2], label=f"ACTIVE: TRACK {track_id}", color=color)
    else:
        for i in range(x1, x2, 10):
            cv2.line(im, (i, y1), (i + 5, y1), color, 3)
            cv2.line(im, (i, y2), (i + 5, y2), color, 3)
        for i in range(y1, y2, 10):
            cv2.line(im, (x1, i), (x1, i + 5), color, 3)
            cv2.line(im, (x2, i), (x2, i + 5), color, 3)
        (tw, th), bl = cv2.getTextSize(label, 0, 0.7, 2)
        cv2.rectangle(im, (x1 + 5 - 5, y1 + 20 - th - 5), (x1 + 5 + tw + 5, y1 + 20 + bl), color, -1)
        cv2.putText(im, label, (x1 + 5, y1 + 20), 0, 0.7, txt_color, 1, cv2.LINE_AA)

cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, click_event)
cv2.imshow(window_name, im)
if save_image:
    cv2.imwrite(image_output_path, im)
cv2.waitKey(0)
cv2.destroyAllWindows()