import cv2  
import logging  
import os  
from PIL import Image, ImageDraw, ImageFont  

import constants  
from detect import detect_logo
from detect import detect_parcel

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

    out_img, logo_name = detect_logo(source_img_path)
    if out_img:
        out_img.save(out_image_path)  
    if logo_name:  
        return logo_name, out_image_path, video_path  
    else:
        return "Logo is not detected.", out_image_path, video_path
    

def generate_recognized_parcel_image(event_data, date_format):  
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

    if int(date_format[11:13]) - 10 < 0:
        # date_format[8:10] = str(int(date_format[8:10])-1).zfill(2)
        date_format = date_format[:8] + str(int(date_format[8:10]) - 1).zfill(2) + date_format[10:]
    video_path = f'{constants.RECORDINGS_DIR}/{date_format[:10]}/{subfolder_num_str}/GarageCamera/{date_format[14:16]}.{date_format[17:19]}.mp4'  

    image = Image.open(source_img_path)

    if image is None:
        logging.error("Image not loaded. Check the path.")  
        return "unknown", None, None, None  
    out_img, parcel = detect_parcel(image)
    out_img.save(out_image_path)  
    if parcel:  
        return "Parcel is detected. Parcel protection mode is working...", out_image_path, video_path  
    else:
        return "Parcel is not detected.", out_image_path, video_path
