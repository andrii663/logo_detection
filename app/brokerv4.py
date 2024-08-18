from mqtt_handler import MqttHandler  

if __name__ == "__main__":  
    """  
    Entry point of the application. Initializes and runs the MQTT handler.  
    """  
    state = False
    mqtt_handler = MqttHandler()  
    mqtt_handler.run()