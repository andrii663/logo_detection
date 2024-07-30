import cv2  
import logging  
import os  

import constants  
from detect import detect_logo


import csv  
import json  

def generate_recognized_logo_image(event_data, date_format):  
    """  
    Processes an image from an event to recognize car details and generate an output image.  
    
    Parameters:  
        event_data: The event data dictionary.  
        date_format: The date and time format string.  
    
    Returns:  
        Tuple: (logo_name, license_text, out_image_path, video_path)  
    """  
    event_id = event_data['id']  
    box = event_data['snapshot']['box']  
    source_img_path = f'{constants.CLIPS_DIR}/GarageCamera-{event_id}-clean.png'  
    out_image_path = f'{constants.CLIPS_DIR}/GarageCamera-{event_id}-rec.jpg'  

    subfolder_num = int(date_format[11:13]) - 10 if int(date_format[11:13]) - 10 > 0 else int(date_format[11:13]) + 14  
    subfolder_num_str = str(subfolder_num).zfill(2)  
    video_path = f'{constants.RECORDINGS_DIR}/{date_format[:10]}/{subfolder_num_str}/GarageCamera/{date_format[14:16]}.{date_format[17:19]}.mp4'  

    img = cv2.imread(source_img_path)  

    if img is None:  
        logging.error("Image not loaded. Check the path.")  
        return "unknown", None, None, None  

    out_img, logo_name = detect_logo(img)
    cv2.imwrite(out_image_path, out_img)  
    if logo_name:  
        return logo_name, out_image_path, video_path  
    else:
        return "car_with_no_logo", out_image_path, video_path