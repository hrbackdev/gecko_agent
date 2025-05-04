import torch
import cv2

class YOLODetector:
    def __init__(self, image_path='prueba.jpg', model_path='yolov5s.pt', label_path='label.txt'):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        self.image_path = image_path
        self.classes_to_detect = self.load_labels(label_path)

    def load_labels(self, label_path):
        try:
            with open(label_path, 'r') as f:
                labels = [line.strip() for line in f if line.strip()]
            return labels
        except FileNotFoundError:
            print(f"No se encontró el archivo {label_path}. Se usarán todas las clases.")
            return []

    def detect(self):
        frame = cv2.imread(self.image_path)
        if frame is None:
            print("No se pudo cargar la imagen.")
            return

        results = self.model(frame)
        detections = results.pandas().xyxy[0]

        if self.classes_to_detect:
            detections = detections[detections['name'].isin(self.classes_to_detect)]

        for _, row in detections.iterrows():
            x1, y1, x2, y2 = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
            label = f"{row['name']} {row['confidence']:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Detección YOLOv5", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    detector = YOLODetector(image_path='prueba.jpg')
    detector.detect()
