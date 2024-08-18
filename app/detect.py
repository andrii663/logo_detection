import sys  
import tensorflow as tf  
import numpy as np  
from PIL import Image, ImageDraw, ImageFont  
from logo_object_detection import ObjectDetection  
from parcel_object_detection import ObjectDetection  

from ultralytics import YOLO  
import cv2  
import numpy as np  


import constants


class TFLiteObjectDetection(ObjectDetection):  
    """Object Detection class for TensorFlow Lite"""  
    def __init__(self, model_filename, labels):  
        super(TFLiteObjectDetection, self).__init__(labels)  
        self.interpreter = tf.lite.Interpreter(model_path=model_filename)  
        self.interpreter.allocate_tensors()  
        self.input_index = self.interpreter.get_input_details()[0]['index']  
        self.output_index = self.interpreter.get_output_details()[0]['index']  

    def predict(self, preprocessed_image):  
        inputs = np.array(preprocessed_image, dtype=np.float32)[np.newaxis, :, :, (2, 1, 0)]  # RGB -> BGR and add 1 dimension.  

        # Resize input tensor and re-allocate the tensors.  
        self.interpreter.resize_tensor_input(self.input_index, inputs.shape)  
        self.interpreter.allocate_tensors()  

        self.interpreter.set_tensor(self.input_index, inputs)  
        self.interpreter.invoke()  
        return self.interpreter.get_tensor(self.output_index)[0]  


def draw_logo_boxes(image, predictions):  
    """Draw bounding boxes with labels and confidence scores on the image."""  
    draw = ImageDraw.Draw(image)  
    
    try:  
        # Load a TTF font for drawing  
        font = ImageFont.truetype("arial.ttf", 15)  
    except IOError:  
        # Use default bitmap font if TTF font is not available  
        font = ImageFont.load_default()  
    
    for prediction in predictions:  
        bbox = prediction['boundingBox']  
        left = bbox['left'] * image.width  
        top = bbox['top'] * image.height  
        width = bbox['width'] * image.width  
        height = bbox['height'] * image.height  
        draw.rectangle([left, top, left + width, top + height], outline='red', width=2)  
        
        text = f"{prediction['tagName']} ({prediction['probability']:.2f})"  
        
        # Calculate text size using getbbox() for bounding box dimensions  
        text_width, text_height = font.getbbox(text)[2:]  
        text_background = [(left, top - text_height), (left + text_width, top)]  
        draw.rectangle(text_background, fill="red")  
        draw.text((left, top - text_height), text, fill="white", font=font) 
        break
    
    return image  


def detect_logo(image):  

    if constants.LOGO_MODEL_FILENAME.endswith(".pt"):         
            # Load YOLO model  
        logo_detector = YOLO(constants.LOGO_MODEL_FILENAME)  
        
        # Convert PIL image to OpenCV format  
        open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  
        
        # Perform detection on the image  
        results = logo_detector(open_cv_image)[0]  
        
        # Extract the bounding box data  
        boxes = results.boxes.data.tolist()  
        
        # Draw bounding boxes on the image  
        for box in boxes:  
            x1, y1, x2, y2, score, class_id = box  
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  
            
            # Draw the rectangle  
            cv2.rectangle(open_cv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  
            
            # Add text label  
            label_text = f"Class ID: {int(class_id)}, Conf: {score:.2f}"  
            cv2.putText(open_cv_image, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)  
        
        # Convert BGR to RGB for conversion to PIL format  
        result_img_rgb = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)  
        
        # Convert to PIL Image format  
        img_with_boxes = Image.fromarray(result_img_rgb)  
        # Determine if a parcel was detected  
        detected_label = None  
        for box in boxes:  
            x1, y1, x2, y2, score, class_id = box  
            if score > constants.LOGO_CONFIDENCE_THRESHOLD and (x2 - x1) * (y2 - y1) / (results.orig_img.shape[0] * results.orig_img.shape[1]) < 0.3:  
                if class_id == 0:
                    detected_label = 'Auspost'
                if class_id == 1:
                    detected_label = "courierplease" 
                if class_id == 2:
                    detected_label = "DHL"
                if class_id == 3:
                    detected_label = "fedex" 
                if class_id == 4:
                    detected_label = "startrack" 
                else:
                    detected_label = "Toll"
                break  
        
        return img_with_boxes, detected_label

    else:
        # Load labels  
        with open(constants.LOGO_LABELS_FILENAME, 'r') as f:  
            labels = [label.strip() for label in f.readlines()]  

        od_model = TFLiteObjectDetection(constants.LOGO_MODEL_FILENAME, labels)  

        predictions = od_model.predict_image(image)  
        
        if not predictions:  
            return None, None  # No predictions were made  

        # Draw boxes on the image  
        image_with_boxes = draw_logo_boxes(image, predictions)  
        # return image_with_boxes, predictions[0]['tagName']
        if predictions:
            if predictions[0]['probability'] > constants.LOGO_CONFIDENCE_THRESHOLD and predictions[0]['boundingBox']['height']*predictions[0]['boundingBox']['width'] < 0.4:
                return image_with_boxes, predictions[0]['tagName']
        return image_with_boxes, None


# -------------------------------------------------------
# Below is about parcel detection model.


def draw_parcel_boxes(image, predictions):  
    # Sort predictions by confidence score in ascending order  
    sorted_predictions = sorted(predictions, key=lambda x: x['probability'])  

    draw = ImageDraw.Draw(image)  
    try:  
        # Load a font  
        font = ImageFont.truetype("arial.ttf", 15)  
    except IOError:  
        # If font file does not exist, load default font  
        font = ImageFont.load_default()  
        
    for prediction in sorted_predictions:  
        box = prediction['boundingBox']  
        left = int(box['left'] * image.width)  
        top = int(box['top'] * image.height)  
        width = int(box['width'] * image.width)  
        height = int(box['height'] * image.height)  
        right = left + width  
        bottom = top + height  

        # Draw the bounding box  
        draw.rectangle([left, top, right, bottom], outline='red', width=2)  

        # Draw the label and probability  
        label = f"{prediction['tagName']}: {prediction['probability']:.2f}"  
        text_size = draw.textbbox((0, 0), label, font=font)  
        text_width = text_size[2] - text_size[0]  
        text_height = text_size[3] - text_size[1]  
        text_background = [left, top - text_height - 5, left + text_width, top]  
        draw.rectangle(text_background, fill='red')  
        draw.text((left, top - text_height - 5), label, fill='white', font=font)  

    return image  

def detect_parcel(image):  
    # Load labels  
    if constants.PARCEL_MODEL_FILENAME.endswith(".pt"):         
         # Load YOLO model  
        parcel_detector = YOLO(constants.PARCEL_MODEL_FILENAME)  
        
        # Convert PIL image to OpenCV format  
        open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  
        
        # Perform detection on the image  
        results = parcel_detector(open_cv_image)[0]  
        
        # Extract the bounding box data  
        boxes = results.boxes.data.tolist()  
        
        # Draw bounding boxes on the image  
        for box in boxes:  
            x1, y1, x2, y2, score, class_id = box  
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  
            
            # Draw the rectangle  
            cv2.rectangle(open_cv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  
            
            # Add text label  
            label_text = f"Class ID: {int(class_id)}, Conf: {score:.2f}"  
            cv2.putText(open_cv_image, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)  
        
        # Convert BGR to RGB for conversion to PIL format  
        result_img_rgb = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)  
        
        # Convert to PIL Image format  
        img_with_boxes = Image.fromarray(result_img_rgb)  
        # Determine if a parcel was detected  
        detected_label = None  
        for box in boxes:  
            x1, y1, x2, y2, score, class_id = box  
            if score > constants.PARCEL_CONFIDENCE_THRESHOLD and (x2 - x1) * (y2 - y1) / (results.orig_img.shape[0] * results.orig_img.shape[1]) < 0.3:  
                detected_label = 'parcel' if class_id == 0 else None  
                break  
        
        return img_with_boxes, detected_label


    else:
        with open(constants.PARCEL_LABELS_FILENAME, 'r') as f:  
            labels = [label.strip() for label in f.readlines()]  

        od_model = TFLiteObjectDetection(constants.PARCEL_MODEL_FILENAME, labels)  

        # image = Image.open(image_filename)  
        predictions = od_model.predict_image(image)  
        
        # Draw boxes on the image  
        image_with_boxes = draw_parcel_boxes(image, predictions)
        if predictions:
            if predictions[0]['probability'] > 0.26 and predictions[0]['boundingBox']['height']*predictions[0]['boundingBox']['width'] < 0.3:
                return image_with_boxes, predictions[0]['tagName']
        return image_with_boxes, None
