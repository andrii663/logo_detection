import json  
import time  
from datetime import datetime  
import threading  
import logging  
import sqlite3  
import os  

import paho.mqtt.client as mqtt_client  
from image_processor import generate_recognized_logo_image  
import constants  

logging.basicConfig(level=logging.INFO)  

class MqttHandler:  
    def __init__(self):  
        """  
        Initializes the MQTT Handler with client settings.  
        """  
        self.last_id = None  
        self.date_format = None  

        self.client = mqtt_client.Client()  
        self.client.username_pw_set(constants.USERNAME, constants.PASSWORD)  
        self.client.on_connect = self.on_connect  
        self.client.on_message = self.on_message  

        self.client.connect(constants.BROKER, constants.PORT, 60)  
        self.client.subscribe(constants.SUBSCRIBE_TOPIC)  

    def on_connect(self, client, userdata, flags, rc):  
        """  
        Callback when the client connects to the MQTT broker.  
        
        Parameters:  
            client: The MQTT client instance.  
            userdata: The private user data.  
            flags: Response flags sent by the broker.  
            rc: The connection result.  
        """  
        logging.info(f"Connected with result code { rc }")  

    def on_message(self, client, userdata, msg):  
        """  
        Callback when a message is received from the MQTT broker.  
        
        Parameters:  
            client: The MQTT client instance.  
            userdata: The private user data.  
            msg: The MQTT message.  
        """  
        payload = msg.payload.decode()  
        try:  
            data = json.loads(payload)  
            event_id = data.get('before', {}).get('id', None)  
            if event_id and ('car' in data.get('before', {}).get('label', None)) or ('truck' in data.get('before', {}).get('label', None)) or ('bus' in data.get('before', {}).get('label', None)):  
                if event_id != self.last_id:  
                    self.last_id = event_id  
                    logging.info(f"{ datetime.fromtimestamp(data['before']['frame_time']) }: Car detected!")  
                    self.date_format = str(datetime.fromtimestamp(data['before']['frame_time']))  
                    logging.info(f"Event_id: { event_id }")  
                else:  
                    logging.info("Event is processing")  
                if data['type'] == 'end':  
                    event_length = data['after']['end_time'] - data['after']['start_time']  
                    logging.info("Event is finished.(%.1fs)" % event_length)  
                    logging.info("Processing snapshots.")  
                    thread = threading.Thread(target=self.process_event, args=(data['after'],))  
                    thread.start()  
        except json.JSONDecodeError:  
            logging.error("Payload is not in JSON format")  

    def process_event(self, event_data):  
        """  
        Processes an event after it is completed.  
        
        Parameters:  
            event_data: The event data dictionary.  
        """  
        event_id = event_data['id']  
        path = f"{constants.CLIPS_DIR}/GarageCamera-{event_id}-clean.png"  
        if self.wait_for_file_creation(path):  
            start_time = time.time()  
            logo_name, out_image_path, video_path = generate_recognized_logo_image(event_data, self.date_format)  
            logging.info(f"Processing event {event_id} finished in {time.time() - start_time} seconds. Recognized logo: {logo_name}")  

            start_time = time.time()  
            event_data = self.fetch_frigate_event_data(event_id)  
            if event_data:  
                # self.insert_event_data(event_data, car_name, out_image_path, video_path)  
                self.insert_event_data(event_data, logo_name, out_image_path, video_path)  

    def fetch_frigate_event_data(self, event_id):  
        """  
        Fetches event data from the Frigate database.  
        
        Parameters:  
            event_id: The ID of the event.  
        
        Returns:  
            event_data: A tuple containing the event data or None if not found.  
        """  
        start_time = time.time()  
        while time.time() - start_time < 30:  
            try:  
                with sqlite3.connect(constants.FRIGATE_DB_PATH) as frigate_db_con:  
                    cursor = frigate_db_con.cursor()  
                    cursor.execute("SELECT id, label, camera, start_time, end_time, thumbnail FROM event WHERE id = ?", (event_id,))  
                    event_data = cursor.fetchone()  
                    if event_data and len(event_data) == 6:  
                        return event_data  
            except Exception as e:  
                logging.error(f"Error fetching event data: {e}")  
            time.sleep(1)  
        return None  

    def insert_event_data(self, event_data, sub_label, out_image_path, video_path):  
        """  
        Inserts event data into the local events database.  
        
        Parameters:  
            event_data: The event data tuple.  
            out_image_path: Path to the output image.  
            video_path: Path to the associated video.  
        """  
        start_time = time.time()  
        while time.time() - start_time < 30:  
            try:  
                with sqlite3.connect(constants.EVENTS_DB_PATH) as events_db_con:  
                    self.setup_database(events_db_con)  
                    events_cursor = events_db_con.cursor()  
                    events_cursor.execute(  
                        "INSERT INTO event (id, label, camera, start_time, end_time, thumbnail, sub_label, snapshot_path, video_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)",  
                        (event_data[0], event_data[1], event_data[2], event_data[3], event_data[4], event_data[5], sub_label, out_image_path, video_path)  
                    )  
                    events_db_con.commit()  
                    break  
            except Exception as e:  
                logging.error(f"Error inserting event data: {e}")  
                time.sleep(1)  

    @staticmethod  
    def setup_database(connection):  
        """  
        Sets up the events database schema.  
        
        Parameters:  
            connection: SQLite database connection.  
        """  
        cursor = connection.cursor()  
        cursor.execute("""  
            CREATE TABLE IF NOT EXISTS event (  
                id TEXT PRIMARY KEY,   
                label TEXT,   
                camera TEXT,   
                start_time DATETIME,  
                end_time DATETIME,  
                thumbnail TEXT,  
                sub_label TEXT,  
                snapshot_path TEXT,  
                video_path TEXT  
            )  
        """)  
        connection.commit()  

    @staticmethod  
    def wait_for_file_creation(file_path, timeout=10, check_interval=0.5):  
        """  
        Waits for a file to be created and become readable.  
        
        Parameters:  
            file_path: Path to the file.  
            timeout: Maximum time to wait (in seconds).  
            check_interval: Interval between checks (in seconds).  
        
        Returns:  
            bool: True if the file exists and is readable, False otherwise.  
        """  
        start_time = time.time()  
        while time.time() - start_time < timeout:  
            if os.path.exists(file_path):  
                try:  
                    with open(file_path, 'rb') as f:  
                        f.read()  
                    return True  
                except IOError:  
                    pass  
            time.sleep(check_interval)  
        logging.warning(f"Timeout reached. File not found or not ready: {file_path}")  
        return False  

    def run(self):  
        """  
        Starts the MQTT client loop.  
        """  
        self.client.loop_forever()