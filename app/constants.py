# Directory Constants

STORAGE_DIR = "/home/admin/storage"
CLIPS_DIR = "/home/admin/storage/clips"  
RECORDINGS_DIR = "/home/admin/storage/recordings"  
FRIGATE_DB_PATH = "/home/admin/config/frigate.db"  
EVENTS_DB_PATH = "/home/admin/config/events.db"  
CAMERA_NAME = 'GarageCamera'

#the period of watcher
SLEEP_INTERVAL = 120
REGULAR_CHECK_INTERVAL = 3600
#TFLite path
# LOGO_MODEL_FILENAME = './model/logo_model.tflite'  
LOGO_MODEL_FILENAME = './model/logo_best.pt'  
LOGO_LABELS_FILENAME = './model/logo_labels.txt'  
# PARCEL_MODEL_FILENAME = './model/parcel_model.tflite'  
PARCEL_MODEL_FILENAME = './model/parcel_best.pt'  
PARCEL_LABELS_FILENAME = './model/parcel_labels.txt'  


# MQTT Constants  
MQTT_TOPIC = "frigate/events/car"  
FRIGATE_SERVER_ADDRESS = "http://jupyterpi:5000"
CLIENT_ID = " "  
USERNAME = "admin"  
PASSWORD = "1BeachHouse@2023"  
BROKER = "192.168.0.63"  
PORT = 1884  
SUBSCRIBE_TOPIC = "frigate/events"  

# Detection Threshold  
PARCEL_CONFIDENCE_THRESHOLD = 0.7
LOGO_CONFIDENCE_THRESHOLD = 0.7