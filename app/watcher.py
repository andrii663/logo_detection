import constants
import cv2  
from datetime import datetime  
from PIL import Image  
import numpy as np  
import os  
import logging
import time
from detect import detect_parcel


def cv2_to_pil(cv2_image):  
    """  
    Convert an OpenCV image (NumPy array) to a Pillow image.  
    """  
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))  

def watch_video(video_path):  
    # Open a connection to the video file  
    cap = cv2.VideoCapture(video_path)  # Use the video file path  

    logging.info("Watching video...")
    if not cap.isOpened():  
        print(f"Error: Could not open video file: {video_path}")  
        return  None

    mod = 1
    is_parcel_exist = None
    frame_index = 0  

    while True:  
        # Read a frame from the video  
        ret, frame = cap.read()  
        if not ret:  
            print("Reached end of video file or encountered an error")  
            break  
        print(f"Processing frame {frame_index}")  
        frame_index += 1  
        # Convert the OpenCV frame to a Pillow image  
        pil_image = cv2_to_pil(frame)  

        # if frame_index>130:
        #     pil_image.show()
        result = detect_parcel(pil_image)  
        if result is None:  
            # print("detect_parcel returned None")  
            continue  # handle this case appropriately 
        _, is_parcel_exist = result
        # Detect parcel in the Pillow image  
        
        # print(is_parcel_exist)
        if is_parcel_exist == None:  
            mod = 0  
            break
        # Get the current date and time in the specified format  
        # current_time = datetime.now().strftime(date_format)  
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  

        # Print the current mode and timestamp to the console (for debugging)  
        print(f'{current_time} - Mode: {mod}')  
        
        # # Show the frame 
        # if frame_index>200:
        # cv2.imshow('Video', frame)  

        # Break the loop if 'q' is pressed  
        if cv2.waitKey(1) & 0xFF == ord('q'):  
            break  
    cap.release()  
    cv2.destroyAllWindows()  
    return mod

def watcher(date_format):
    '''
    search video clip  whether the parcel is taken.
    '''
    subfolder_num = int(date_format[11:13]) - 10 if int(date_format[11:13]) - 10 >= 0 else int(date_format[11:13]) + 14  
    subfolder_num_str = str(subfolder_num).zfill(2)  
    
    logging.info("Watcher script is running.")

    if int(date_format[11:13]) - 10 < 0:
        # date_format[8:10] = str(int(date_format[8:10])-1).zfill(2)
        date_format = date_format[:8] + str(int(date_format[8:10]) - 1).zfill(2) + date_format[10:]

    video_folder = f'{constants.RECORDINGS_DIR}/{date_format[:10]}/{subfolder_num_str}/GarageCamera/'  

    # Call the function to get matching files  
    matching_files = find_video_path(video_folder, date_format)  

    mod = 1
    # Print matching file paths  
    for file_path in matching_files:  
       mod = watch_video(file_path)
       break
    return mod

def find_video_path(video_folder, date_format):

    try:
        #Find the video in the folder
        logging.info("Finding the video...")
        # Extract the required components from date_format  
        prefix = date_format[14:16]  
        prefix_opt = int(date_format[14:16]) - 1  
        prefix_opt = f"{prefix_opt:02d}" 

        max_number = int(date_format[17:19])  
        if max_number>=10:
            min_number = max_number - 10  
        else:    
            min_number = max_number + 50

        logging.info(f"prefix:{prefix}")

        time.sleep(10)
        # List all files in the directory  
        files = os.listdir(video_folder)  
        logging.info(f"{files}")
        # Filter files based on the specified conditions  
        matching_files = []  
        for file in files:  
            if file.startswith(prefix) and max_number>=10:  
                logging.info("1")
                parts = file.split('.')  
                logging.info(f"parts : {parts}")

                if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():  
                    
                    second_num = int(parts[1])
                    if min_number < second_num < max_number:  
                        matching_files.append(os.path.join(video_folder, file)) 
            else:  
                if file.startswith(prefix_opt) and max_number<10:
                    logging.info("2")

                    parts = file.split('.')  
                    logging.info(f"parts : {parts}")

                    if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():  
                        
                        second_num = int(parts[1])
                        if min_number < second_num :  
                            matching_files.append(os.path.join(video_folder, file)) 

        logging.info(f"matching filename: {matching_files}")
        return matching_files  

    except Exception as e:  
        print(f"An error occurred: {e}")  
        return []  