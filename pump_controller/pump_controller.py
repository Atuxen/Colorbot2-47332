import serial
import serial.tools.list_ports
import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os 
import datetime
import torch
from .utils import read_logfile, write_to_logfile
from .mqtt_utils import HiveMQ
import threading, json, time
from queue import Queue, Empty
from pathlib import Path
import secrets_mqtt as mqtt

class PumpController:
    def __init__(self, ser_port, baud_rate = 9600, cell_volume = 20.0, drain_time = 20.0, config_file = 'config.json'):

        """
        Initializes a PumpController instance with the specified serial port and baud rate.
        The cell volume and drain time can also be defined.

        Parameters:
        - ser_port (str): Serial port used for communication.
        - baud_rate (int): Baud rate at which to communicate over the serial port.
        - cell_volume (float): Maximum volume of test cell
        - drain_time (float): Time to run the drain pump in order to empty the cell
        - config_file (str): Config File

        Returns:
        - None

        Notes:
        - This method sets up a serial connection using the provided serial port and baud rate.
        - It prints information about the opened serial port and waits for the Arduino to be ready.
        - Retrieves the pump configuration from 'config.json' and stores it in the 'pump_config' attribute.
        """
          # -------------------------------- USB branch --------------------------------
        if ser_port:
            self.ser = serial.Serial(ser_port, baud_rate)
            print(f"Serial port {ser_port} opened @ {baud_rate}")
            self.wait_for_arduino()
        else:
            self.ser = None


          
        
        
        self.cell_volume = cell_volume
        self.drain_time = drain_time


        
        # Try to resolve path from cwd if not absolute
        config_file = Path(config_file)
        if not config_file.is_absolute():
            config_file = Path(__file__).resolve().parent.parent / config_file

        if not config_file.exists():
            raise FileNotFoundError(f"Could not find config file at {config_file}")

        self.config_file = config_file

        self.config_file = config_file
        self.pump_config = self.get_config()



      # ---------- MQTT branch -----------------------------------------------------
        if self.ser is None:
            

            self.mqtt = HiveMQ(mqtt.BROKER_HOST, mqtt.PORT,
                               mqtt.USERNAME, mqtt.PASSWORD)
            self.mqtt.start()                     # loop thread
            print(f"MQTT connected → {mqtt.BROKER_HOST}:{mqtt.PORT}")
           

            # ---- shared state for color replies ----
            self.last_color  = None
            self.color_event = threading.Event()

            topic_data = mqtt.TOPIC_DATA

            def _color_listener(client, userdata, msg, *, _self=self):
                try:
                    d = json.loads(msg.payload)
                    if "color_sense" in d:
                        rgb = d["color_sense"]
                        _self.last_color = [rgb["r"], rgb["g"], rgb["b"]]
                        _self.color_event.set()
                except Exception as e:
                    print("listener parse error:", e)

            self.mqtt.client.message_callback_add(topic_data, _color_listener)
            self.mqtt.client.subscribe(topic_data, qos=1)

            # optional: subscribe to status topic
            self.mqtt.client.subscribe(mqtt.STATUS_TPC, qos=1)

        self.target_mixture = [0.25, 0.25, 0.25, 0.25]
        self.target_color = [255, 255, 255]

        self.last_color   = None
        self.color_event  = threading.Event()

        # Create "logs" folder if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Create a log file with the current date and time and write column names
        now = datetime.datetime.now()
        self.log_file = f"logs/log_{now.strftime('%d%m%Y_%H%M%S')}.csv"
        log_df = pd.DataFrame(columns=['mixture', 'measurement', 'target_mixture', 'target_measurement'])
        log_df.to_csv(self.log_file, index=False)

        


    ### COMMS ###

    def send_to_arduino(self, send_str):

        """
        Sends a string message to the Arduino over the established serial connection.

        Parameters:
        - send_str (str): The string message to be sent to the Arduino.

        Returns:
        - None

        Notes:
        - The message is encoded as UTF-8 before being sent to the Arduino.
        - The 'ser' attribute must represent a valid and open serial connection.
        """

        self.ser.write(send_str.encode('utf-8'))

    def recv_from_arduino(self, timeout = 10.0):

        """
        Receives data from the Arduino over the established serial connection.

        Parameters:
        - timeout (float): Maximum time (in seconds) to wait for a response from the Arduino.

        Returns:
        - str: The received data from the Arduino.

        Raises:
        - TimeoutError: If the Arduino does not respond within the specified timeout.

        Notes:
        - This method reads data from the Arduino until it encounters the end marker (ASCII 62).
        - It decodes the received data as UTF-8 and returns the complete message.
        - The method has a timeout mechanism to prevent waiting indefinitely for a response.
        - If a timeout occurs, it raises a TimeoutError with a suggestion to reset the device.
        """
        
        start_marker = 60
        end_marker = 62

        start_time = time.time()

        ck = ""
        x = "z"
        byte_count = -1

        while time.time() - start_time < timeout:
            while ord(x) != start_marker:
                x = self.ser.read()

            while ord(x) != end_marker:
                if ord(x) != start_marker:
                    ck = ck + x.decode("utf-8")
                    byte_count += 1
                x = self.ser.read()

            return ck
        
        raise TimeoutError("Arduino did not respond within timeout. Try resetting the device.")
    
    def wait_for_arduino(self):

        """
        Waits for the Arduino to indicate readiness for communication.

        Parameters:
        - None

        Returns:
        - None

        Notes:
        - This method continuously checks for the "Arduino is ready" message from the Arduino.
        - It uses the `recv_from_arduino` method to receive data and prints the received message.
        - The method waits until there is data available in the serial buffer (`in_waiting` > 0).
        - The process continues until the Arduino signals readiness, as indicated by the message.
        """

        msg = ""
        while msg.find("Colorbot is ready") == -1:
            while self.ser.in_waiting == 0:
                pass
            msg = self.recv_from_arduino()
            print(msg)

    def clear_serial_buffer(self):

        """
        Clears the serial buffer by reading and discarding any available data.

        Parameters:
        - None

        Returns:
        - None

        Notes:
        - This method continuously reads and discards data from the serial buffer while it is not empty.
        - It ensures that any residual or unwanted data in the buffer is removed.
        - Useful to prepare the serial connection for new data transmission or reception.
        """

        while self.ser.in_waiting > 0:
            self.ser.read()

    def run_test(self, test_str):

        """
        Executes a command by sending a message to the Arduino and waiting for a response in return.

        Parameters:
        - test_str (str): The test message to be sent to the Arduino.

        Returns:
        - None

        Notes:
        - This method clears the serial buffer to ensure a clean slate for receiving data.
        - It sends the test message to the Arduino using the `send_to_arduino` method.
        - Waits for a response by continuously checking the serial buffer until data is available.
        - Prints the sent test message, received reply, and a separator for clarity.
        """

        self.clear_serial_buffer()

        waiting_for_reply = False

        if not waiting_for_reply:
            self.send_to_arduino(test_str)
            print("Sent from PC -- TEST STR -- " + test_str)
            waiting_for_reply = True

        if waiting_for_reply:
            while self.ser.in_waiting == 0:
                pass

            data_received = self.recv_from_arduino()
            print("Reply Received  " + data_received)
            waiting_for_reply = False

            print("===========")


    ### COLORS ### 
            
    def get_rgb(self):

        """
        Retrieves RGB values from the Arduino by waiting for a message containing 'RGB'.

        Parameters:
        - None

        Returns:
        - list: A list of RGB values [R, G, B] received from the Arduino.

        Notes:
        - This method continuously checks for a message containing 'RGB' from the Arduino.
        - It uses the `recv_from_arduino` method to receive data and extracts RGB values from the message.
        - The RGB values are expected to be in the format 'RGB:XX,YY,ZZ'.
        """

        msg = ""
        while msg.find("RGB") == -1:
            while self.ser.in_waiting == 0:
                pass

            msg = self.recv_from_arduino()
            rgb_vals = list(map(int, msg.split(':')[1].split(',')))

        return rgb_vals
       
    
    ### CONTROLS ### 

    def get_config(self):

        """
        Reads and loads the pump configuration from a JSON file named 'config.json'.

        Parameters:
        - None

        Returns:
        - dict: A dictionary containing pump configuration data.

        Notes:
        - This method reads the 'config.json' file, assumed to be in the current directory.
        - The file is expected to contain a JSON-formatted configuration for pump settings.
        - The configuration data is returned as a dictionary.
        """
        
        

        try:
            with open(self.config_file, "r") as file:
                pump_config = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: {self.config_file} file not found. Please make sure the file exists in the current directory.")
        
        return pump_config
    
    

    def _color_listener(client, userdata, msg):
        try:
            d = json.loads(msg.payload)
            if "color_sense" in d:
                rgb = d["color_sense"]
                # store as [r,g,b]
                self.last_color = [rgb["r"], rgb["g"], rgb["b"]]
                self.color_event.set()
        except Exception as e:
            print("listener parse error:", e)

   

    
    def measure(self, timeout=8):
        """
        Publishes {"Meas":True}, waits up to *timeout* s for color_sense,
        returns [r,g,b] list or raises TimeoutError.
        """
        if self.ser:
            self.run_test("<Meas>")
            return self.get_rgb()

        # MQTT path ---------------------------------------------------
        self.color_event.clear()        # forget previous result
        self.last_color = None

        self.mqtt.publish(mqtt.TOPIC_CMD,
                          {"Meas": True})
        print("Meas request sent…")

        if not self.color_event.wait(timeout):
            raise TimeoutError("No color_sense within %s s" % timeout)

        return self.last_color         # always fresh, matched by callback





    def _await_color(self, timeout=5.0):
        """
        Wait for a single 'color_sense' message on TOPIC_DATA.
        Returns [r,g,b] or raises TimeoutError.
        """
        topic_data = mqtt.TOPIC_DATA
        result_q   = Queue(maxsize=1)
        done       = threading.Event()

        # local callback
        def _once(client, userdata, msg):
            try:
                payload = json.loads(msg.payload)
                if "color_sense" in payload:
                    rgb = payload["color_sense"]
                    result_q.put([rgb["r"], rgb["g"], rgb["b"]])
                    done.set()
            except Exception as e:
                print("Parse error in _await_color:", e)

        # attach + subscribe
        self.mqtt.client.message_callback_add(topic_data, _once)
        self.mqtt.client.subscribe(topic_data, qos=1)

        # wait
        if not done.wait(timeout):
            # clean up even on timeout
            self.mqtt.client.message_callback_remove(topic_data)
            raise TimeoutError("No color_sense message within timeout")

        # clean up + return data
        self.mqtt.client.message_callback_remove(topic_data)
        try:
            return result_q.get_nowait()
        except Empty:
            raise RuntimeError("Color queue empty after event was set")

    
    
    # Single Control Functions

    def purge_pump(self, pump, purge_time = 10.0):

        """
        Initiates a pump purging (priming) process to fill the hose with liquid.

        Parameters:
        - pump (str): The identifier for the pump to be purged.
        - purge_time (float): The duration (in seconds) for which the pump will be purged.

        Returns:
        - None

        Notes:
        - This method retrieves the pump pin from the pump configuration.
        - It purges the specified pump for the specified duration using the `run_test` method.
        - The purging process is used to ensure accurate liquid pumping during subsequent operations.
        """

        pump_pin = self.pump_config['pumps'][pump]['pin']

        if self.ser:
            self.run_test(f"<Mix,{pump_pin},{purge_time}>")

        else: 
            self.mqtt.publish(mqtt.TOPIC_CMD, {"Mix":pump_pin, "duration": purge_time})
            print(f"Purging pump {pump} for {purge_time} seconds...")

    def run_pump(self, pump, volume):

        """
        Initiates a pump operation to dispense a specified volume of liquid.

        Parameters:
        - pump (str): The identifier for the pump to be run.
        - volume (float): The volume of liquid to be dispensed by the pump.

        Returns:
        - None

        Notes:
        - This method retrieves the pump pin and calibration parameters from the pump configuration.
        - Calculates the pump operation time based on the specified volume and calibration parameters.
        - Operates the specified pump for the calculated pump operation time using the `run_test` method.
        - If the specified volume or the calculated run time is 0 or less, the pump is not activated.
        """

        pump_pin = self.pump_config['pumps'][pump]['pin']
        if volume > 0:
            a = self.pump_config['pumps'][pump]['a']
            b = self.pump_config['pumps'][pump]['b']
            pump_time = a * volume + b
            if pump_time > 0:
                self.run_test(f"<Mix,{pump_pin},{pump_time}>")

    def flush(self):

        """
        Initiates a flush operation using the water pump to fill the test cell.

        Parameters:
        - None

        Returns:
        - None

        Notes:
        - This method uses the `run_pump` method to initiate a flush operation using the water pump ('W').
        - The specified cell volume determines the amount of water to be dispensed during the flush.
        """

        self.run_pump('W', self.cell_volume)

    def drain(self, drain_time = None):

        """
        Initiates a drain operation using the drain pump to drain liquid for a specified duration.

        Parameters:
        - drain_time (float): Amount of time to drain. If None, the time defined in instance definition is used.
            If None, drain time is the pre-defined drain time
            If float, the cell is drained for the provided amount of time

        Returns:
        - None

        Notes:
        - This method uses the `purge_pump` method to initiate a drain operation using the drain pump ('D').
        - The specified drain time determines how long the drain pump will be activated for liquid purging.
        """
        if drain_time == None:
            self.purge_pump('D', self.drain_time)
        else:
            self.purge_pump('D', drain_time)

    # Sequence Control Functions
        
    def reset(self):

        """
        Performs a system reset by draining, flushing, and draining again for new measurements.

        Parameters:
        - None

        Returns:
        - None

        Notes:
        - This method uses the `drain` and `flush` methods to perform a system reset.
        - Drains the system for the specified duration, flushes with water, and drains again.
        """

        self.drain()
        time.sleep(1)
        
        self.flush()
        time.sleep(1)
        
        self.drain()
        time.sleep(1)

    def mix_color(self, col_list, changing_target = False):

        """
        Initiates a color mixing process by running pumps based on a specified color composition.

        Parameters:
        - col_list (list): A list of color composition values [R, G, B, Y].
        - changing_target (Bool): An indicator of the target being changed

        Returns:
        - list: A list of RGB values [R, G, B] obtained after the color mixing process.

        Notes:
        - This method ensures that the sum of color composition values adds up to 1.0.
        - Adjusts the color composition values based on the maximum volume specified.
        - Runs pumps for each color (R, G, B, Y) to achieve the desired color composition.
        - Pauses for 2 seconds, measures the resulting color using the `measure` method, and resets the system.
        - Logs the mixture and measurement, along with the target mixture and color.
        - Returns the RGB values obtained after the color mixing process.
        """

        # Normalization
        col_list = np.array(col_list).reshape(4,) # Make sure that input list has np shape (4,)
        col_list[col_list < 0] = 0
        if col_list.sum() == 0:
            col_list = [0.25, 0.25, 0.25, 0.25]
        else:
            col_list = np.divide(col_list, col_list.sum())
        
        log_col_list = col_list
        
        col_list = [i * self.cell_volume for i in col_list]
        self.run_pump('R', col_list[0])
        time.sleep(1)
        self.run_pump('G', col_list[1])
        time.sleep(1)
        self.run_pump('B', col_list[2])
        time.sleep(1)
        self.run_pump('Y', col_list[3])

        time.sleep(1)

        rgb_measurement = self.measure()

        time.sleep(1)

        self.reset()

        if not changing_target:
            # Append color mixture and measurement data to the log file
            write_to_logfile(log_col_list, rgb_measurement, self.target_mixture, self.target_color, self.log_file)

        return rgb_measurement
    

    def change_target(self, target_mixture):
        """
        Mixes a color using given mixture, measures it and stores it as target.

        Parameters:
        - target_mixture (list): A list of color composition values [R, G, B, Y] for the target color mixture.

        Returns:
        - list: A list of RGB values [R, G, B] obtained for the target color mixture.

        Notes:
        - This method sets the target color mixture and measures it using the `mix_color` method.
        """
        self.target_mixture = target_mixture
        self.target_color = self.mix_color(target_mixture, changing_target = True)
        #self.target_color = self.mix_color(target_mixture)

        print(f"Target changed to {self.target_color}. Created by {self.target_mixture}.")

        return self.target_color

    



    
    


       