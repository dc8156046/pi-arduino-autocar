import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import subprocess
import numpy as np
import sys
import select

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
        print("Still capture image received")
        image = cv2.imread(image_path)
        return image
    except Exception as e:
        print(f"Error capturing image: {e}")
        return None

def recognize_text(image):
    """Processes the image and extracts text using Tesseract OCR."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Save the processed image for debugging
    cv2.imwrite("processed.jpg", thresh)
    
    text = pytesseract.image_to_string(thresh, config='--psm 6').strip().upper()
    return text

def input_available():
    """Check if input is available without blocking."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

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
    
    print("Press ENTER at any time to quit")
    
    # Set OpenCV's useOptimized flag
    cv2.setUseOptimized(True)
    
    # Disable GUI functionality
    os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    while True:
        # Check for quit command
        if input_available():
            if sys.stdin.readline().strip() == 'q':
                print("Quit command received")
                break
        
        image = capture_image()
        if image is None:
            print("Failed to capture image, retrying...")
            time.sleep(1)
            continue
        
        # Save a debug image occasionally
        timestamp = int(time.time())
        if timestamp % 30 < 1:  # Save roughly every 30 seconds
            debug_filename = f"debug_image_{timestamp}.jpg"
            cv2.imwrite(debug_filename, image)
            print(f"Saved debug image: {debug_filename}")
        
        text = recognize_text(image)
        if text:
            print(f"Recognized: {text}")
            
            if "STOP" in text:
                send_command("x")
            elif "F" in text:
                send_command("w")
            elif "B" in text:
                send_command("s")
            elif "L" in text or "A" in text:  # Added L as alternative to A for left
                send_command("a")
            elif "R" in text or "D" in text:  # Added R as alternative to D for right
                send_command("d")
        else:
            print("No text recognized")
        
        # Small delay to prevent CPU overload
        time.sleep(0.5)
        
except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting due to keyboard interrupt...")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")