import sys  
import tensorflow as tf  
import numpy as np  
from PIL import Image, ImageDraw, ImageFont  
from object_detection import ObjectDetection  

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


def draw_boxes(image, predictions):  
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


def detect_logo(image_filename):  
    # Load labels  
    with open(constants.LABELS_FILENAME, 'r') as f:  
        labels = [label.strip() for label in f.readlines()]  

    od_model = TFLiteObjectDetection(constants.MODEL_FILENAME, labels)  

    image = Image.open(image_filename)  
    predictions = od_model.predict_image(image)  
    

    # Draw boxes on the image  
    image_with_boxes = draw_boxes(image, predictions)  
    return image_with_boxes, predictions[0]['tagName']
