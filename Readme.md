# Logo and parcel detection  

This project uses Frigate, MQTT, logo & parcel detection model, and SQLite including real-time analysis. Below is the developer's guide to set up and run the project.  

## Developer's Guide  

### Setting up the Development Environment  
1. **Clone the repository**  
2. **Make sure Python (>3.11.2) is installed.**  

### Running the Project  

#### Development with Docker & Local  

1. **Deploy the project in a virtual environment**:  
   ```shell  
   python local.py
2. **Run the server in a Docker container**:  
   
    This will run the FaceNet server in a Docker container. Start the server with:  
    ```shell  
    sudo docker compose up --build

#### File Organization 🗄️

```shell
├── Logo & parcel detection (Current Directory)  
    ── app  
        ├── brokerv4.py
        ├── constants.py
        ├── detect.py
        ├── image_processor.py
        ├── logo_object_detection.py
        ├── parcel_object_detection.py
        ├── mqtt_handler.py
        ├── watcher.py
    ├── models  
        ├── logo_labels.txt 
        ├── logo_model.tflite
        ├── parcel_best.pt
        ├── parcel_labels.txt 
        ├── parcel_model.tflite  
    └── Readme.md  
    └── Dockerfile  
    └── docker-compose.yml
```

#### How to try with the customized model

1. For logo detection model, please place it in the /model directory.
   Here, logo_labels include the logo classes like DHL, toll, etc. So replace it with new one.
2. For parcel detection model, please place it in the /model directory.
   Here, parcel_labels may include classes like parcel, box, etc.
   Current pipeline absords both tflite model and pt model. So if you want to try your tflite model, then copy that model in /models directory and change the PARCEL_MODEL_FILENAME in constants.py.
3. In constants.py, PARCEL_CONFIDENCE_THRESHOLD,LOGO_CONFIDENCE_THRESHOLD means the confidence score for parcel and logo respectively.
