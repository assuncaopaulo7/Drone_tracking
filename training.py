from ultralytics import YOLO
import torch
from multiprocessing import freeze_support 

if __name__ == '__main__':
    freeze_support()

    print("GPU Available: ", torch.cuda.is_available())
    print("GPU Name: ", torch.cuda.get_device_name(0))

    # Carrega um modelo YOLO11n pré-treinado no COCO
    model = YOLO("yolo11n.pt")

    # Treina o modelo no dataset de exemplo COCO8 por 100 épocas
    results = model.train(
        data="/home/marcos/multivehicle/mavsdk_drone_show-0.2/fine-tuning-drones/UAVs-2/data.yaml", 
        epochs=200, 
        imgsz=640,
        device=0,
        name="train"
        )
    
    # Avalia o desempenho do modelo no conjunto de validação
    metrics = model.val()

    # Realiza detecção de objetos em uma imagem
    results = model("/home/marcos/multivehicle/mavsdk_drone_show-0.2/fine-tuning-drones/drone-classification-1/train/images/Screenshot-from-2025-05-08-09-08-51_png.rf.6b829b41ee6eff27feddf407fbfb87cc.jpg")
    results[0].show()

    # Exporta o modelo para o formato ONNX
    path = model.export(format="onnx")  # retorna o caminho para o modelo exportado