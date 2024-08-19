import json  
import time  
from datetime import datetime, timedelta  
import threading  
import logging  
import sqlite3  
import os  

import paho.mqtt.client as mqtt_client  
from image_processor import generate_recognized_logo_image  
from image_processor import generate_recognized_parcel_image  
from image_processor import generate_recognized_parcel_image_in_last  

from watcher import watcher  
import constants  

import sys  
import requests  
from io import BytesIO  
from PIL import Image  

import traceback  

log_handler = logging.StreamHandler(stream=sys.stdout)  

if  True:  
    logging.getLogger(None).handlers = [log_handler]  
    logging.getLogger(None).setLevel(logging.INFO)  
    logging.getLogger("elasticsearch").setLevel(logging.ERROR)  

class MqttHandler:  
    watch_status = False

    def __init__(self):  
        """  
        Initializes the MQTT Handler with client settings.  
        """  
        self.last_id = None  
        self.date_format = None  
        self.flag_parcel = None  
        self.flag_logo = None  
        self.obj = None  
        self.client = mqtt_client.Client()  
        self.client.username_pw_set(constants.USERNAME, constants.PASSWORD)  
        self.client.on_connect = self.on_connect  
        self.client.on_message = self.on_message  
        self.db_lock = threading.Lock()  # Initialize a lock for database operations  
        
        self.client.connect(constants.BROKER, constants.PORT, 60)  
        self.client.subscribe(constants.MQTT_TOPIC)  

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
            if event_id and isinstance(data.get('before', {}).get('label'), str) and ('car' in data['before']['label'] or 'truck' in data['before']['label'] or 'bus' in data['before']['label']):  
                self.obj = 'car'  
                if event_id != self.last_id:  
                    self.last_id = event_id  
                    self.flag_logo = time.time()  
                    logging.info(f"{ datetime.fromtimestamp(data['before']['frame_time']) }: Car detected!")  
                    self.date_format = str(datetime.fromtimestamp(data['before']['frame_time']))  
                    logging.info(f"Event_id: { event_id }")  
                elif data["after"]["snapshot"]['frame_time'] - data['after']['start_time'] <= 1:   
                    logging.info("Event is processing")  
                
                logging.info(f"flag logo : {self.flag_logo}")  
                current_time = time.time()  
                if self.flag_logo == None:  
                    period = 0  
                else:  
                    period = current_time - self.flag_logo  
                if period > 1:  
                    self.flag_logo = None  
                    logging.info("Since 1 second has passed, trying to get the best img until now ...")  
                    # Save the best snapshot img  
                    start_time = time.time()  
                    snapshot_image = self.fetch_best_snapshot(event_id)  
                    file_path = os.path.join(constants.CLIPS_DIR, f"{constants.CAMERA_NAME}-{event_id}-bestinsec.png")  
                    self.save_snapshot_image(snapshot_image, file_path)  
                    current_time = time.time()  
                    period = current_time - start_time  
                    logging.info(f"Saved the best snapshot in {period} seconds.")  

                    thread = threading.Thread(target=self.process_event, args=(data['after'],))  
                    thread.start()  


                if data['type'] == 'end' and self.flag_logo != None:  
                    event_length = data['after']['end_time'] - data['after']['start_time']  
                    logging.info("Event is finished.(%.1fs)" % event_length)  
                    logging.info("Processing snapshots.")  
                    self.flag_logo = None  
                    thread = threading.Thread(target=self.process_event, args=(data['after'],))  
                    thread.start()  
            
            # Check whether the person is detected.    
            if event_id and ('person' in data.get('before', {}).get('label', None)):  
                self.obj = 'person'  
                if event_id != self.last_id:  
                    self.last_id = event_id  
                    self.flag_parcel = time.time()  
                    logging.info(f"{ datetime.fromtimestamp(data['before']['frame_time']) }: Person detected!")  
                    self.date_format = str(datetime.fromtimestamp(data['before']['frame_time']))  
                    logging.info(f"Event_id: { event_id }")  
                elif data["after"]["snapshot"]['frame_time'] - data['after']['start_time'] <= 1:   
                    logging.info("Event is processing")  

                logging.info(f"flag parcel : {self.flag_parcel}")  
                current_time = time.time()  
                if self.flag_parcel == None:  
                    period = 0  
                else:  
                    period = current_time - self.flag_parcel  
                if period > 1:  
                    self.flag_parcel = None  
                    logging.info("Since 1 second has passed, trying to get the best img until now ...")  
                    # Save the best snapshot img  
                    start_time = time.time()  
                    snapshot_image = self.fetch_best_snapshot(event_id)  
                    file_path = os.path.join(constants.CLIPS_DIR, f"{constants.CAMERA_NAME}-{event_id}-bestinsec.png")  
                    self.save_snapshot_image(snapshot_image, file_path)  
                    current_time = time.time()  
                    period = current_time - start_time  
                    logging.info(f"Saved the best snapshot in {period} seconds.")  

                    thread = threading.Thread(target=self.process_event, args=(data['after'],))  
                    thread.start()  

                if data['type'] == 'end':  

                    start_time = time.time()  
                    snapshot_image = self.fetch_current_snapshot(event_id)  
                    file_path = os.path.join(constants.CLIPS_DIR, f"{constants.CAMERA_NAME}-{event_id}-last.png")  
                    self.save_snapshot_image(snapshot_image, file_path)  

                    if self.flag_parcel != None:   
                        event_length = data['after']['end_time'] - data['after']['start_time']  
                        logging.info("Event is finished.(%.1fs)" % event_length)  
                        logging.info("Processing snapshots.")  
                        self.flag_parcel = None  
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
        path = f"{constants.CLIPS_DIR}/GarageCamera-{event_id}-bestinsec.png"  
        if self.wait_for_file_creation(path):  
            start_time = time.time()  
            if self.obj == 'car':  
                logo_name, out_image_path, video_path = generate_recognized_logo_image(event_data, self.date_format)  
                logging.info(f"Processing event {event_id} finished in {time.time() - start_time} seconds. Recognized logo: {logo_name}")  
                
                # Create the payload combining both paths  
                payload = json.dumps({  
                    "snapshot_path": out_image_path,  
                    "logo_name": f"{logo_name} Truck was spotted.",  
                })   
                # Publish a message to the new topic  

                result = self.client.publish(constants.MQTT_TOPIC, payload)  

                # Check if the publish was successful  
                status = result.rc  
                if status == 0:  
                    logging.info(f"Sent `{payload}` to topic `{constants.MQTT_TOPIC}`")  
                else:  
                    logging.info(f"Failed to send message to topic {constants.MQTT_TOPIC}")  

                # Insert event data into the database
                if logo_name != "Logo is not detected.":  
                    start_time = time.time()  
                    event_data = self.fetch_frigate_event_data(event_id)  
                    self.insert_logo_event_data(event_data, logo_name, out_image_path, video_path)  
                    current_time = time.time()  
                    logging.info(f"Saving car event took {current_time - start_time} seconds.")  
            elif self.obj == 'person':  
                parcel, out_image_path, video_path = generate_recognized_parcel_image(event_data, self.date_format)  
                logging.info(f"Processing event {event_id} finished in {time.time() - start_time} seconds. {parcel}")  
                check = False  
                if parcel != "Parcel is not detected.":  
                    check = True  
                else:  
                    # check the last scene of the event to see if there is a parcel  
                    path = f"{constants.CLIPS_DIR}/GarageCamera-{event_id}-last.png"  
                    if self.wait_for_file_creation(path):  
                        start_time = time.time()  
                        parcel, out_image_path, video_path = generate_recognized_parcel_image_in_last(event_data, self.date_format)  
                        logging.info(f"Processing event {event_id} finished in {time.time() - start_time} seconds. {parcel}")  
                        if parcel != "Parcel is not detected.":  
                            check = True  

                if check:  
                    # Create the payload and publish the notification   
                    payload = json.dumps({  
                        "snapshot_path": out_image_path,  
                        "message": "Parcel was detected."  
                    })   
                    # Publish a message to the new topic  
                    result = self.client.publish(constants.MQTT_TOPIC, payload)  
                    # Check if the publish was successful  
                    status = result.rc  
                    if status == 0:  
                        logging.info(f"Sent `{payload}` to topic `{constants.MQTT_TOPIC}`")  
                    else:  
                        logging.info(f"Failed to send message to topic {constants.MQTT_TOPIC}")  

                    if MqttHandler.watch_status == True:
                        logging.info("Parcel protection mode is already running.")
                    else:
                        start_time = time.time()  
                        event_data = self.fetch_frigate_event_data(event_id)  
                        if event_data:  

                            datetime_object = datetime.strptime(self.date_format, "%Y-%m-%d %H:%M:%S.%f")  
                            formatted_time = datetime_object.strftime("%d%m%Y %I:%M%p").lower()  

                            self.insert_parcel_event_data(event_data, out_image_path, video_path, formatted_time)  
                            current_time = time.time()  
                            period = current_time - start_time  
                            logging.info(f"Saving parcel spot event took {period} seconds.")  
                            logging.info(f"Parcel was spotted at {self.date_format}")  
                            logging.info(f"Parcel protection mode turned on.")  

                            mode = True  
                            temp_time = datetime.strptime(self.date_format, "%Y-%m-%d %H:%M:%S.%f")   
                            temp_time += timedelta(seconds=constants.SLEEP_INTERVAL)  # Increment temp_time  
                            # Create the payload and publish the notification   
                            payload = json.dumps({  
                                "message": "Parcel Watch Activated."  
                            })   
                            # Publish a message to the new topic  
                            result = self.client.publish(constants.MQTT_TOPIC, payload)  
                            # Check if the publish was successful  
                            status = result.rc  
                            if status == 0:  
                                logging.info(f"Sent `{payload}` to topic `{constants.MQTT_TOPIC}`")  
                            else:  
                                logging.info(f"Failed to send message to topic {constants.MQTT_TOPIC}")  

                            time.sleep(constants.SLEEP_INTERVAL)  
                            try:  
                                if MqttHandler.watch_status == False:
                                    MqttHandler.watch_status == True
                                    while mode:  
                                        current_time_str = temp_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Formatting to include milliseconds if present  


                                        is_parcel_exist = watcher(current_time_str)  
                                        if is_parcel_exist == 0:  
                                            # Create the payload and publish the notification   
                                            payload = json.dumps({  
                                                "message": "Parcel Taken Detected."  
                                            })   
                                            # Publish a message to the new topic  
                                            result = self.client.publish(constants.MQTT_TOPIC, payload)  
                                            # Check if the publish was successful  
                                            status = result.rc  
                                            if status == 0:  
                                                logging.info(f"Sent `{payload}` to topic `{constants.MQTT_TOPIC}`")  
                                            else:  
                                                logging.info(f"Failed to send message to topic {constants.MQTT_TOPIC}")  

                                            logging.info("Parcel is taken. Parcel protection mode turning off.")  
                                            mode = False  
                                            take_person_name = self.extract_parcel_taken_name()  
                                            # Create the payload and publish the notification   
                                            payload = json.dumps({  
                                                "message": f"Parcel Taken by {take_person_name}."  
                                            })   
                                            # Publish a message to the new topic  
                                            result = self.client.publish(constants.MQTT_TOPIC, payload)  
                                            # Check if the publish was successful  
                                            status = result.rc  
                                            if status == 0:  
                                                logging.info(f"Sent `{payload}` to topic `{constants.MQTT_TOPIC}`")  
                                            else:  
                                                logging.info(f"Failed to send message to topic {constants.MQTT_TOPIC}")  
                                            formatted_time = temp_time.strftime("%d%m%Y %I:%M%p").lower()  
                                            logging.info(f"Parcel is taken by {take_person_name} at {formatted_time}")  
                                            self.insert_parcel_taken_event_data(event_data, out_image_path, video_path, take_person_name + " at " + str(formatted_time))  
                                            MqttHandler.watch_status = False
                                            break  
                                        time.sleep(constants.SLEEP_INTERVAL)  
                                        temp_time += timedelta(seconds=constants.SLEEP_INTERVAL)  # Increment temp_time  
                            except KeyboardInterrupt:  
                                logging.info("Monitoring stopped manually.")  

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
                with self.db_lock, sqlite3.connect(constants.FRIGATE_DB_PATH) as frigate_db_con:  
                    cursor = frigate_db_con.cursor()  
                    cursor.execute("SELECT id, label, camera, start_time, end_time, thumbnail FROM event WHERE id = ?", (event_id,))  
                    event_data = cursor.fetchone()  
                    if event_data and len(event_data) == 6:  
                        return event_data  
            except Exception as e:  
                logging.error(f"Error fetching event data: {e}")  
            time.sleep(1)  
        return None  

    def insert_logo_event_data(self, event_data, sub_label, out_image_path, video_path):  
        """  
        Inserts logo event data into the local events database.  
        
        Parameters:  
            event_data: The event data tuple.  
            out_image_path: Path to the output image.  
            video_path: Path to the associated video.  
        """  
        start_time = time.time()  
        while time.time() - start_time < 30:  
            try:  
                with self.db_lock, sqlite3.connect(constants.EVENTS_DB_PATH) as events_db_con:  
                    self.setup_database(events_db_con)  
                    events_cursor = events_db_con.cursor()  
                    events_cursor.execute(  
                        """  
                        INSERT INTO event (id, label, camera, start_time, end_time, thumbnail, sub_label, snapshot_path, video_path)  
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)  
                        ON CONFLICT(id) DO UPDATE SET  
                            sub_label = CASE  
                                            WHEN event.sub_label IS NULL THEN excluded.sub_label  
                                            ELSE event.sub_label || ', ' || excluded.sub_label  
                                        END  
                        """,  
                        (event_data[0], event_data[1], event_data[2], event_data[3], event_data[4], event_data[5], sub_label, out_image_path, video_path)  
                    )  
                    events_db_con.commit()  
                    break  
            except Exception as e:  
                logging.error(f"Error inserting event data: {e}")  
                logging.error(f"Exception type: {type(e).__name__}, Args: {e.args}")  
                logging.error("Traceback: %s", traceback.format_exc())  
                time.sleep(1)  

    def insert_parcel_event_data(self, event_data, out_image_path, video_path, stime):  
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
                with self.db_lock, sqlite3.connect(constants.EVENTS_DB_PATH) as events_db_con:  
                    self.setup_database(events_db_con)  
                    events_cursor = events_db_con.cursor()  
                    events_cursor.execute(  
                        """  
                        INSERT INTO event (  
                            id, label, camera, start_time, end_time, thumbnail,  
                            snapshot_path, video_path, parcel_spotted_time  
                        )  
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)  
                        ON CONFLICT (id) DO UPDATE SET  
                            parcel_spotted_time = excluded.parcel_spotted_time  
                        """,  
                        (event_data[0], event_data[1], event_data[2], event_data[3], event_data[4], event_data[5], out_image_path, video_path, stime)  
                    )  
                    events_db_con.commit()  
                    break  
            except Exception as e:  
                logging.error(f"Error inserting event data: {e}")  
                time.sleep(1)  

    def insert_parcel_taken_event_data(self, event_data, out_image_path, video_path, taken_time):  
        """  
        Inserts taken parcel event data into the local events database.  
        
        Parameters:  
            event_data: The event data tuple.  
            out_image_path: Path to the output image.  
            video_path: Path to the associated video.  
            taken_time: Time when the parcel was taken.  
        """  
        start_time = time.time()  
        while time.time() - start_time < 30:  
            try:  
                with self.db_lock, sqlite3.connect(constants.EVENTS_DB_PATH) as events_db_con:  
                    self.setup_database(events_db_con)  
                    events_cursor = events_db_con.cursor()  
                    events_cursor.execute(  
                        "UPDATE event SET parcel_taken_time = ? WHERE id = ?",  
                        (taken_time, event_data[0])  
                    )
                    events_db_con.commit()  
                    break  
            except Exception as e:  
                logging.error(f"Error inserting event data: {e}")  
                time.sleep(1)  

    def extract_parcel_taken_name(self):
        '''
        The most recent sub_label is extracted from the event table on condition that label is person.
        '''
        start_time = time.time()  
        while time.time() - start_time < 30:  
            try:  
                with sqlite3.connect(constants.EVENTS_DB_PATH) as events_db_con:  
                    self.setup_database(events_db_con)  
                    events_cursor = events_db_con.cursor()  
                    # Query to select all sub_labels where label is 'person'  
                    events_cursor.execute(  
                        "SELECT sub_label FROM event WHERE label = 'person'"  
                    )  

                    # Fetch all results  
                    results = events_cursor.fetchall() 
                    cnt = 1
                    if results:
                        sub_label = results[-cnt][0]
                        while sub_label == None:
                            cnt+=1
                            sub_label= results[-cnt][0]
                    events_db_con.commit()  
                    break  
            except Exception as e:  
                logging.error(f"Error inserting event data: {e}")  
                time.sleep(1)  
        return sub_label

    def fetch_best_snapshot(self, event_id, base_url= constants.FRIGATE_SERVER_ADDRESS):  
        # Construct the URL for accessing the best snapshot  
        snapshot_url = f"{base_url}/api/events/{event_id}/snapshot.jpg"  
        logging.info(snapshot_url)
        # Make the HTTP request to fetch the image  
        response = requests.get(snapshot_url)  
        
        if response.status_code == 200:  
            # Load the response content as an image  
            image = Image.open(BytesIO(response.content))  
            return image  
        else:  
            print(f"Failed to fetch snapshot. Status code: {response.status_code}")  
            return None  

    def fetch_current_snapshot(self, event_id, base_url = constants.FRIGATE_SERVER_ADDRESS):  
        snapshot_url = f"{base_url}/api/{constants.CAMERA_NAME}/latest.jpg"  
        logging.info(f"Fetching current snapshot from: {snapshot_url}")  
        response = requests.get(snapshot_url)  

        if response.status_code == 200:  
            # Load the response content as an image  
            image = Image.open(BytesIO(response.content))  
            return image  
        else:  
            print(f"Failed to fetch snapshot. Status code: {response.status_code}")  
            return None  

    def save_snapshot_image(self, image, file_path):  
        try:  
            # Ensure the directory exists  
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  
            # Save the image  
            image.save(file_path)  
            print(f"Snapshot saved at: {file_path}")  
        except Exception as err:  
            print(f"Failed to save image: {err}") 

    def regular_parcel_check(self, state):

        while True:
            time.sleep(constants.REGULAR_CHECK_INTERVAL)
            start_time = time.time()
            snapshot_image = self.fetch_current_snapshot()
            file_path = os.path.join(constants.CLIPS_DIR, f"{constants.CAMERA_NAME}-{start_time}-bestinasec.png")
            self.save_snapshot_image(snapshot_image, file_path)

            #check if there is a parcel
            parcel, out_image_path, video_path = generate_recognized_parcel_image(start_time, self.date_format)
            logging.info(f"Regular check in {start_time} finished in {time.time() - start_time} seconds. {parcel}")

            


    @staticmethod  
    def setup_database(connection):  
        """  
        Sets up the events database schema.  
        
        Parameters:  
            connection: SQLite database connection.  
        """  
        cursor = connection.cursor()  
        
        # Create the table if it does not exist  
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
        
        # Check if 'parcel_spotted_time' and 'parcel_taken_time' columns exist  
        cursor.execute("PRAGMA table_info(event)")  
        existing_columns = [info[1] for info in cursor.fetchall()]  
        
        if 'parcel_spotted_time' not in existing_columns:  
            cursor.execute("ALTER TABLE event ADD COLUMN parcel_spotted_time TEXT")  
            
        if 'parcel_taken_time' not in existing_columns:  
            cursor.execute("ALTER TABLE event ADD COLUMN parcel_taken_time TEXT")  
        
        # Commit the changes  
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
