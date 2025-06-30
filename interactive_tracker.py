# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

import time

import cv2

from ultralytics import YOLO
from ultralytics.utils import LOGGER
from ultralytics.utils.plotting import Annotator, colors
from opencv_gazebo import Video
import socket
import json 



enable_gpu = True  # Defina como True se estiver rodando com CUDA
model_file = "/home/marcos/multivehicle/projeto_final/mavsdk_drone_show-0.2/best.pt"  # Caminho para o arquivo do modelo
show_fps = True  # Se True, mostra o FPS atual no canto superior esquerdo
show_conf = True  # Exibe ou oculta a pontuação de confiança
save_video = True  # Defina como True para salvar o vídeo de saída
video_output_path = "interactive_tracker_output.avi"  # Nome do arquivo de vídeo de saída


conf = 0.6  # Confiança mínima para deteção de objetos (menor = mais deteções, possivelmente mais falsos positivos)
iou = 0.5  # Limite de IoU para NMS (maior = menos sobreposição permitida)
max_det = 20  # Máximo de objetos por imagem (aumente para cenas mais cheias)

tracker = "bytetrack.yaml"  # Configuração do tracker: 'bytetrack.yaml', 'botsort.yaml', etc.
track_args = {
    "persist": True,  # Mantém o histórico dos frames como um stream para rastreamento contínuo
    "verbose": False,  # Exibe informações de debug do tracker
}

window_name = "YOLO Tracking"  # Nome da janela de saída

LOGGER.info("🚀 Inicializando o modelo...")
if enable_gpu:
    LOGGER.info("Usando GPU...")
    model = YOLO(model_file)
    model.to("cuda")
else:
    LOGGER.info("Usando CPU...") 
    model = YOLO(model_file, task="detect")

classes = model.names  # Armazena os nomes das classes do modelo

#cap = cv2.VideoCapture("/home/marcos/videos_escolhidos/videos/videos/00_09_30_to_00_10_09(1).mp4") #caminho do vídeo
video = Video(port=5600)  # ou a porta que estiver usando

# Inicializa o gravador de vídeo
vw = None

selected_object_id = None
selected_bbox = None
selected_center = None

# ------------------------------------------------

UDP_IP = "127.0.0.1"  # IP do receptor, nesse caso, localhost
UDP_PORT = 9999       # Porta UDP para enviar os dados
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Cria o socket UDP
last_udp_send = time.time()  # Marca o tempo do último envio UDP

# -----------------------------------------------


 
def get_center(x1, y1, x2, y2): 
    """
    Calcula o ponto central de uma caixa delimitadora (bounding box).

    Args:
        x1 (int): Coordenada X do canto superior esquerdo.
        y1 (int): Coordenada Y do canto superior esquerdo.
        x2 (int): Coordenada X do canto inferior direito.
        y2 (int): Coordenada Y do canto inferior direito.

    Retorna:
        (int, int): Ponto central (x, y) da caixa delimitadora.
    """
    return (x1 + x2) // 2, (y1 + y2) // 2


def extend_line_from_edge(mid_x, mid_y, direction, img_shape):
    """
    Calcula o ponto final para estender uma linha do centro até a borda da imagem.

    Args:
        mid_x (int): Coordenada X do ponto médio.
        mid_y (int): Coordenada Y do ponto médio.
        direction (str): Direção para estender ('left', 'right', 'up', 'down').
        img_shape (tuple): Formato da imagem (altura, largura, canais).

    Returns:
        (int, int): Coordenada do ponto final da linha estendida.
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
    Desenha linhas de escopo de rastreamento estendendo da caixa delimitadora até as bordas da imagem.

    Args:
        im (ndarray): Array da imagem para desenhar.
        bbox (tuple): Coordenadas da caixa delimitadora (x1, y1, x2, y2).
        color (tuple): Cor em formato BGR para desenhar.
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
    Lida com eventos de clique do mouse para selecionar um objeto para rastreamento focado.

    Args:
        event (int): Tipo de evento do mouse do OpenCV.
        x (int): Coordenada X do evento do mouse.
        y (int): Coordenada Y do evento do mouse.
        flags (int): Quaisquer flags relevantes passadas pelo OpenCV.
        param (any): Parâmetros adicionais (não usado).
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


# Inicializa a janela de visualização
cv2.namedWindow(window_name)
cv2.moveWindow(window_name, 0, 0)  # força a abrir no canto superior esquerdo
cv2.setMouseCallback(window_name, click_event)

fps_counter, fps_timer, fps_display = 0, time.time(), 0

# Loop principal
while True:
    if not video.frame_available():
        continue

    im = video.frame()  # Captura o frame atual do vídeo
    print(f"✅ Frame recebido: shape={im.shape}")


    # Inicializa VideoWriter quando o primeiro frame estiver disponível
    if save_video and vw is None:
        h, w = im.shape[:2]
        vw = cv2.VideoWriter(video_output_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (w, h))  # ajuste o FPS conforme necessário

    results = model.track(im, conf=conf, iou=iou, max_det=max_det, tracker=tracker, **track_args)  # Executa o rastreamento no frame atual
    annotator = Annotator(im)                                                                      # Cria um objeto Annotator para desenhar caixas e rótulos
    detections = results[0].boxes.data if results[0].boxes is not None else []                     # Obtém as deteções do primeiro resultado
    detected_objects = []                                                                          # Lista para armazenar os objetos detetados
    object_detected = False                                                                        # Variável para verificar se algum objeto foi detetado
    object_position = None                                                                         # Posição do objeto detetado                                              

    for track in detections:                                                                  
        track = track.tolist()
        if len(track) < 6:       # Verifica se a deteção tem informações suficientes
            continue

        x1, y1, x2, y2 = map(int, track[:4])                                                        # Extrai as coordenadas da caixa delimitadora
        class_id = int(track[6]) if len(track) >= 7 else int(track[5])                              # Extrai o ID da classe (6º índice se estiver presente, caso contrário 5º índice) 
        track_id = int(track[4]) if len(track) == 7 else -1                                         # Extrai o ID do rastreamento (4º índice se estiver presente, caso contrário -1)

        if not object_detected:                 # Ao detetar:
            cx, cy = get_center(x1, y1, x2, y2)  # Calcula o centro da caixa delimitadora
            object_position = (cx, cy)           # Armazena a posição do objeto detetado
            object_detected = True               # Marca que um objeto foi detetado

        color = colors(track_id, True)          
        txt_color = annotator.get_txt_color(color)
        label = f"{classes[class_id]} ID {track_id}" + (f" ({float(track[5]):.2f})" if show_conf else "")
        if track_id == selected_object_id:    
            draw_tracking_scope(im, (x1, y1, x2, y2), color)    # Desenha linhas de rastreamento
            center = get_center(x1, y1, x2, y2)                 # Calcula o centro da janela 
            cv2.circle(im, center, 6, color, -1)                # Desenha um círculo no centro da janela
            annotator.box_label([x1, y1, x2, y2], label=f"ACTIVE: TRACK {track_id}", color=color) 
        else:
            for i in range(x1, x2, 10):  # Desenha linhas horizontais na parte superior e inferior da caixa delimitadora
                cv2.line(im, (i, y1), (i + 5, y1), color, 3)
                cv2.line(im, (i, y2), (i + 5, y2), color, 3)
            for i in range(y1, y2, 10):  # Desenha linhas verticais na parte esquerda e direita da caixa delimitadora
                cv2.line(im, (x1, i), (x1, i + 5), color, 3)
                cv2.line(im, (x2, i), (x2, i + 5), color, 3)
            (tw, th), bl = cv2.getTextSize(label, 0, 0.7, 2)
            cv2.rectangle(im, (x1 + 5 - 5, y1 + 20 - th - 5), (x1 + 5 + tw + 5, y1 + 20 + bl), color, -1)
            cv2.putText(im, label, (x1 + 5, y1 + 20), 0, 0.7, txt_color, 1, cv2.LINE_AA)


    # Exibe o FPS atual no canto superior esquerdo
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

    # Envia dados via UDP a cada 0.3 segundos
    current_time = time.time()
    if current_time - last_udp_send >= 0.3:
        data = {
            "detected": object_detected,  # (True/False) 
            "position": object_position if object_position else [None, None] # (x,y) ou [None, None] se não detetado
        }
        message = json.dumps(data).encode('utf-8')
        try:
            sock.sendto(message, (UDP_IP, UDP_PORT))
            print(f"📤 Enviado UDP: {data}")
        except Exception as e:
            print(f"Erro ao enviar UDP: {e}")
        last_udp_send = current_time



    h, w = im.shape[:2]     
    center = (w // 2, h // 2) 
    cv2.circle(im, center, 8, (0, 0, 0), -1)  

    cv2.imshow(window_name, im_resized)   # Mostra o frame redimensionado na janela
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