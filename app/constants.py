# Directory Constants  
CLIPS_DIR = "/home/admin/storage/clips"  
RECORDINGS_DIR = "/home/admin/storage/recordings"  
FRIGATE_DB_PATH = "/home/admin/config/frigate.db"  
EVENTS_DB_PATH = "/home/admin/config/events.db"  
MODEL_LICENSE_PLATE_DETECTOR = "./models/license_plate_detector.pt"  
MODEL_COCO = "./models/yolov8n.pt"  
LICENSE_PLATES_IMGS_DETECTED_DIR = "./licenses_plates_imgs_detected"  
CSV_DETECTIONS_DIR = "./csv_detections"  
# COCO vehicle class IDs (an example, these need to match your model's classes)  
VEHICLE_CLASSES = [2, 5, 7]  # IDs for car, bus, truck, etc.  

#TFLite path
MODEL_FILENAME = './model/model.tflite'  
LABELS_FILENAME = './model/labels.txt'  

# MQTT Constants  
CLIENT_ID = " "  
USERNAME = "admin"  
PASSWORD = "1BeachHouse@2023"  
BROKER = "192.168.0.63"  
PORT = 1883  
SUBSCRIBE_TOPIC = "frigate/events"  

# Detection Threshold  
THRESHOLD = 0.15