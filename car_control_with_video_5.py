from picamera2 import Picamera2
import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import torch
import numpy as np
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
    text = pytesseract.image_to_string(processed, config="--psm 6").strip().upper()
    return text


# use YOLOv8 to detect person
def detect_person(frame, model):
    results = model(frame)  # use YOLOv8 to detect objects
    person_detected = False

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # get class ID
            if cls == 0:  # person class
                person_detected = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # get box coordinates
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # draw box

    return person_detected


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

    # initialize PiCamera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()

    follow_mode = True  # default to follow mode

    while True:
        frame = picam2.capture_array()  # capture frame from camera
        frame = cv2.cvtColor(
            frame, cv2.COLOR_RGB2BGR
        )  # convert to BGR format for OpenCV
        # detect person
        person_detected = detect_person(frame, model)

        if person_detected:
            print("Person detected, following...")
            if follow_mode:
                send_command("follow")  # send follow command
        else:
            print("No person detected, stopping...")
            send_command("x")  # send stop command

        # recognize text
        text = recognize_text(frame)
        if text:
            print(f"Recognized: {text}")
            follow_mode = False  # disable follow mode

            if "STOP" in text:
                send_command("x")
            elif "W" in text:
                send_command("w")
            elif "S" in text:
                send_command("s")
            elif "A" in text:
                send_command("a")
            elif "D" in text:
                send_command("d")

        # display frame
        cv2.imshow("Camera", frame)

        # check for key press
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    picam2.close()
    cv2.destroyAllWindows()
    if "ser" in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
