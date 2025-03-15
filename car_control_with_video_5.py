from picamera2 import Picamera2
import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import torch
import numpy as np
import os
from ultralytics import YOLO


# auto detect arduino port
def find_arduino():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if (
            "Arduino" in port.description
            or "ttyUSB" in port.device
            or "ttyACM" in port.device
        ):
            return port.device
    return None


# send command to arduino
def send_command(command):
    try:
        ser.write((command + "\n").encode())  # send command to Arduino
        print(f"Sent: {command}")
        time.sleep(0.1)  # wait for command to be processed
        response = ser.readline().decode("utf-8").strip()  # read response from Arduino
        if response:
            print(f"Arduino: {response}")
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None


# recognize text from image
def recognize_text(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # convert to grayscale
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Save processed image occasionally for debugging
    if int(time.time()) % 30 < 1:  # Save roughly every 30 seconds
        cv2.imwrite(f"processed_text_{int(time.time())}.jpg", processed)

    text = pytesseract.image_to_string(processed, config="--psm 6").strip().upper()
    return text


# use YOLOv8 to detect person
def detect_person(frame, model):
    results = model(frame)  # use YOLOv8 to detect objects
    person_detected = False
    person_box = None

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # get class ID
            if cls == 0:  # person class
                person_detected = True
                person_box = box.xyxy[0].tolist()  # get box coordinates

                # Save debug image with bounding box occasionally
                if int(time.time()) % 30 < 1:  # Save roughly every 30 seconds
                    debug_frame = frame.copy()
                    x1, y1, x2, y2 = map(int, person_box)
                    cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.imwrite(f"person_detected_{int(time.time())}.jpg", debug_frame)

    return person_detected, person_box


# Configure for headless operation
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# find Arduino port
arduino_port = find_arduino()
if not arduino_port:
    print("No Arduino found! Please check the connection.")
    exit(1)

try:
    ser = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {arduino_port}")

    # initialize YOLOv8
    model = YOLO("yolov8n.pt")  # load YOLOv8 model
    print("YOLO model loaded successfully")

    # initialize PiCamera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("Camera initialized successfully")

    follow_mode = True  # default to follow mode
    last_command_time = 0
    command_cooldown = 0.5  # seconds between commands

    # Counter for command stability
    text_command_counter = 0
    last_text_command = ""

    print("System running. Press Ctrl+C to exit.")

    while True:
        frame = picam2.capture_array()  # capture frame from camera
        frame = cv2.cvtColor(
            frame, cv2.COLOR_RGB2BGR
        )  # convert to BGR format for OpenCV

        current_time = time.time()

        # Save raw frame occasionally for debugging
        if int(current_time) % 60 < 1:  # Save roughly every minute
            cv2.imwrite(f"raw_frame_{int(current_time)}.jpg", frame)

        # detect person
        person_detected, person_box = detect_person(frame, model)

        # Process text commands
        text = recognize_text(frame)
        if text:
            print(f"Recognized: {text}")

            # Determine command from text
            command = None
            if "STOP" in text:
                command = "x"
            elif "W" in text or "FORWARD" in text:
                command = "w"
            elif "S" in text or "BACK" in text:
                command = "s"
            elif "A" in text or "LEFT" in text:
                command = "a"
            elif "D" in text or "RIGHT" in text:
                command = "d"

            # If valid command found
            if command:
                # Check for command stability (same command detected multiple times)
                if command == last_text_command:
                    text_command_counter += 1
                else:
                    text_command_counter = 1
                    last_text_command = command

                # If command is stable (detected 3 times in a row)
                if text_command_counter >= 3:
                    follow_mode = False  # disable follow mode
                    if current_time - last_command_time > command_cooldown:
                        send_command(command)
                        last_command_time = current_time
                        text_command_counter = 0  # Reset after sending command

        # Handle person follow mode
        if follow_mode and person_detected:
            print("Person detected, following...")
            if current_time - last_command_time > command_cooldown:
                send_command("follow")
                last_command_time = current_time
        elif follow_mode and not person_detected:
            print("No person detected, stopping...")
            if current_time - last_command_time > command_cooldown:
                send_command("x")
                last_command_time = current_time

        # Short sleep to prevent CPU overload
        time.sleep(0.1)

except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    picam2.close()
    if "ser" in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
    print("Done.")
