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

#the period of watcher
SLEEP_INTERVAL = 120

#TFLite path
LOGO_MODEL_FILENAME = './model/logo_model.tflite'  
LOGO_LABELS_FILENAME = './model/logo_labels.txt'  
# PARCEL_MODEL_FILENAME = './model/parcel_model.tflite'  
PARCEL_MODEL_FILENAME = './model/parcel_best.pt'  
PARCEL_LABELS_FILENAME = './model/parcel_labels.txt'  


# MQTT Constants  
CLIENT_ID = " "  
USERNAME = "admin"  
PASSWORD = "1BeachHouse@2023"  
BROKER = "192.168.0.63"  
PORT = 1883  
SUBSCRIBE_TOPIC = "frigate/events"  

# Detection Threshold  
PARCEL_CONFIDENCE_THRESHOLD = 0.7
LOGO_CONFIDENCE_THRESHOLD = 0.2