# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

import time

import cv2

from ultralytics import YOLO
from ultralytics.utils import LOGGER
from ultralytics.utils.plotting import Annotator, colors
from opencv_gazebo import Video
import socket
import json



enable_gpu = True  # Set True if running with CUDA
model_file = "/home/marcos/multivehicle/projeto_final/mavsdk_drone_show-0.2/best.pt"  # Path to model file
show_fps = True  # If True, shows current FPS in top-left corner
show_conf = True  # Display or hide the confidence score
save_video = True  # Set True to save output video
video_output_path = "interactive_tracker_output.avi"  # Output video file name


conf = 0.6  # Min confidence for object detection (lower = more detections, possibly more false positives)
iou = 0.5  # IoU threshold for NMS (higher = less overlap allowed)
max_det = 20  # Maximum objects per im (increase for crowded scenes)

tracker = "bytetrack.yaml"  # Tracker config: 'bytetrack.yaml', 'botsort.yaml', etc.
track_args = {
    "persist": True,  # Keep frames history as a stream for continuous tracking
    "verbose": False,  # Print debug info from tracker
}

window_name = "YOLO Tracking"  # Output window name

LOGGER.info("🚀 Initializing model...")
if enable_gpu:
    LOGGER.info("Using GPU...")
    model = YOLO(model_file)
    model.to("cuda")
else:
    LOGGER.info("Using CPU...") 
    model = YOLO(model_file, task="detect")

classes = model.names  # Store model classes names

#cap = cv2.VideoCapture("/home/marcos/videos_escolhidos/videos/videos/00_09_30_to_00_10_09(1).mp4") #video path
video = Video(port=5600)  # ou o porto que estiver usando

# Initialize video writer
vw = None

selected_object_id = None
selected_bbox = None
selected_center = None

# ------------------------------------------------

UDP_IP = "127.0.0.1"  # ou o IP do receptor
UDP_PORT = 9999       # escolha uma porta livre
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

last_udp_send = time.time()

# -----------------------------------------------


 
def get_center(x1, y1, x2, y2): 
    """
    Calculates the center point of a bounding box.

    Args:
        x1 (int): Top-left X coordinate.
        y1 (int): Top-left Y coordinate.
        x2 (int): Bottom-right X coordinate.
        y2 (int): Bottom-right Y coordinate.

    Returns:
        (int, int): Center point (x, y) of the bounding box.
    """
    return (x1 + x2) // 2, (y1 + y2) // 2


def extend_line_from_edge(mid_x, mid_y, direction, img_shape):
    """
    Calculates the endpoint to extend a line from the center toward an image edge.

    Args:
        mid_x (int): X-coordinate of the midpoint.
        mid_y (int): Y-coordinate of the midpoint.
        direction (str): Direction to extend ('left', 'right', 'up', 'down').
        img_shape (tuple): Image shape in (height, width, channels).

    Returns:
        (int, int): Endpoint coordinate of the extended line.
    """
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


def draw_tracking_scope(im, bbox, color):
    """
    Draws tracking scope lines extending from the bounding box to image edges.

    Args:
        im (ndarray): Image array to draw on.
        bbox (tuple): Bounding box coordinates (x1, y1, x2, y2).
        color (tuple): Color in BGR format for drawing.
    """
    x1, y1, x2, y2 = bbox
    mid_top = ((x1 + x2) // 2, y1)
    mid_bottom = ((x1 + x2) // 2, y2)
    mid_left = (x1, (y1 + y2) // 2)
    mid_right = (x2, (y1 + y2) // 2)
    cv2.line(im, mid_top, extend_line_from_edge(*mid_top, "up", im.shape), color, 2)
    cv2.line(im, mid_bottom, extend_line_from_edge(*mid_bottom, "down", im.shape), color, 2)
    cv2.line(im, mid_left, extend_line_from_edge(*mid_left, "left", im.shape), color, 2)
    cv2.line(im, mid_right, extend_line_from_edge(*mid_right, "right", im.shape), color, 2)


def click_event(event, x, y, flags, param):
    """
    Handles mouse click events to select an object for focused tracking.

    Args:
        event (int): OpenCV mouse event type.
        x (int): X-coordinate of the mouse event.
        y (int): Y-coordinate of the mouse event.
        flags (int): Any relevant flags passed by OpenCV.
        param (any): Additional parameters (not used).
    """
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


cv2.namedWindow(window_name)
cv2.moveWindow(window_name, 0, 0)  # <-- força a abrir no canto superior esquerdo
cv2.setMouseCallback(window_name, click_event)

fps_counter, fps_timer, fps_display = 0, time.time(), 0

while True:
    if not video.frame_available():
        continue

    im = video.frame()
    print(f"✅ Frame recebido: shape={im.shape}")


    # Inicializa VideoWriter quando o primeiro frame estiver disponível
    if save_video and vw is None:
        h, w = im.shape[:2]
        vw = cv2.VideoWriter(video_output_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (w, h))  # ajuste o FPS conforme necessário

    results = model.track(im, conf=conf, iou=iou, max_det=max_det, tracker=tracker, **track_args)
    annotator = Annotator(im)
    detections = results[0].boxes.data if results[0].boxes is not None else []
    detected_objects = []

    # --------------------------------------------------
    object_detected = False
    object_position = None
    # --------------------------------------------------

    for track in detections:
        track = track.tolist()
        if len(track) < 6:
            continue

        x1, y1, x2, y2 = map(int, track[:4])
        class_id = int(track[6]) if len(track) >= 7 else int(track[5])
        track_id = int(track[4]) if len(track) == 7 else -1

        if not object_detected:  # é mesmo aqui?
            cx, cy = get_center(x1, y1, x2, y2)
            object_position = (cx, cy)
            object_detected = True

        color = colors(track_id, True)
        txt_color = annotator.get_txt_color(color)
        label = f"{classes[class_id]} ID {track_id}" + (f" ({float(track[5]):.2f})" if show_conf else "")
        if track_id == selected_object_id:
            draw_tracking_scope(im, (x1, y1, x2, y2), color)
            center = get_center(x1, y1, x2, y2)
            cv2.circle(im, center, 6, color, -1)
            #pulse_radius = 8 + int(4 * abs(time.time() % 1 - 0.5))
            #cv2.circle(im, center, pulse_radius, color, 2)
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

    if show_fps:
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            fps_display = fps_counter
            fps_counter = 0
            fps_timer = time.time()

        fps_text = f"FPS: {fps_display}"
        cv2.putText(im, fps_text, (10, 25), 0, 0.7, (255, 255, 255), 1)
        (tw, th), bl = cv2.getTextSize(fps_text, 0, 0.7, 2)
        cv2.rectangle(im, (10 - 5, 25 - th - 5), (10 + tw + 5, 25 + bl), (255, 255, 255), -1)
        cv2.putText(im, fps_text, (10, 25), 0, 0.7, (104, 31, 17), 1, cv2.LINE_AA)


    # Redimensiona o frame para metade do tamanho antes de exibir
    im_resized = cv2.resize(im, (im.shape[1], im.shape[0]))

    # -----------------------------------------------------------------
    current_time = time.time()
    if current_time - last_udp_send >= 0.3:
        data = {
            "detected": object_detected,
            "position": object_position if object_position else [None, None]
        }
        message = json.dumps(data).encode('utf-8')
        try:
            sock.sendto(message, (UDP_IP, UDP_PORT))
            print(f"📤 Enviado UDP: {data}")
        except Exception as e:
            print(f"Erro ao enviar UDP: {e}")
        last_udp_send = current_time

    # -----------------------------------------------------------------
    # ...dentro do loop principal, após receber o frame 'im'...

    h, w = im.shape[:2]
    center = (w // 2, h // 2)
    cv2.circle(im, center, 8, (0, 0, 0), -1)  # preto, raio 2, preenchido

    cv2.imshow(window_name, im_resized)
    if save_video and vw is not None:
        vw.write(im)

    LOGGER.info(f"🟡 DETECTED {len(detections)} OBJECT(S): {' | '.join(detected_objects)}")

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("c"):
        LOGGER.info("🟢 TRACKING RESET")
        selected_object_id = None

if save_video and vw is not None:
    vw.release()
cv2.destroyAllWindows()