import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import subprocess
import numpy as np

def find_arduino():
    """Automatically finds the Arduino port."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "ttyUSB" in port.device or "ttyACM" in port.device:
            return port.device
    return None

def send_command(command):
    """Sends a command to the Arduino and reads response."""
    try:
        ser.write((command + '\n').encode())
        print(f"Sent: {command}")
        time.sleep(0.1)
        response = ser.readline().decode('utf-8').strip()
        if response:
            print(f"Arduino: {response}")
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def capture_image():
    """Captures an image using libcamera and returns the image as an OpenCV array."""
    image_path = "capture.jpg"
    try:
        subprocess.run(["libcamera-still", "-o", image_path, "--nopreview", "-t", "1"], check=True)
        image = cv2.imread(image_path)
        return image
    except Exception as e:
        print(f"Error capturing image: {e}")
        return None

def recognize_text(image):
    """Processes the image and extracts text using Tesseract OCR."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(thresh, config='--psm 6').strip().upper()
    return text

# Connect to Arduino
arduino_port = find_arduino()
if not arduino_port:
    print("No Arduino found! Please check the connection.")
    exit(1)

try:
    ser = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {arduino_port}")
    
    while True:
        image = capture_image()
        if image is None:
            continue
        
        text = recognize_text(image)
        if text:
            print(f"Recognized: {text}")
            
            if "STOP" in text:
                send_command("x")
            elif "F" in text:
                send_command("w")
            elif "B" in text:
                send_command("s")
            elif "A" in text:
                send_command("a")
            elif "D" in text:
                send_command("d")
        
        cv2.imshow("Captured Image", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    cv2.destroyAllWindows()
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
