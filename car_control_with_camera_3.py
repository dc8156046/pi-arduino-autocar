import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import subprocess
import numpy as np
import sys
import select
import os  # Add this import for os.environ

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
    """改进的图像处理与文本识别函数，提供更好的OCR效果"""
    # 将图像转换为灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 应用自适应阈值处理，这比简单的二值化更适合处理不均匀照明
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # 应用形态学操作改善文本连接性
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # 应用高斯模糊降噪，但保持文本清晰
    blur = cv2.GaussianBlur(opening, (1, 1), 0)
    
    # 应用锐化滤波器增强文本边缘
    kernel_sharpening = np.array([[-1,-1,-1], 
                                  [-1, 9,-1],
                                  [-1,-1,-1]])
    sharpened = cv2.filter2D(blur, -1, kernel_sharpening)
    
    # 保存处理后的图像用于调试
    cv2.imwrite("processed_improved.jpg", sharpened)
    
    # 使用Tesseract的更多选项提高识别率
    # --oem 3: 使用LSTM OCR引擎
    # --psm 6: 假设为单一文本块
    # -l eng: 使用英语字典
    # -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ: 只允许识别大写字母
    custom_config = r'--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    text = pytesseract.image_to_string(sharpened, config=custom_config).strip().upper()
    
    return text

def process_and_recognize(image, debug=True):
    """使用多种处理方法尝试识别文本，返回最可能的结果"""
    # 方法1: 基本处理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    text1 = pytesseract.image_to_string(binary, config='--psm 6').strip().upper()
    
    # 方法2: 自适应阈值
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    text2 = pytesseract.image_to_string(adaptive, config='--psm 6').strip().upper()
    
    # 方法3: 锐化
    kernel_sharpening = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharpening)
    _, binary_sharp = cv2.threshold(sharpened, 150, 255, cv2.THRESH_BINARY)
    text3 = pytesseract.image_to_string(binary_sharp, config='--psm 6').strip().upper()
    
    # 方法4: OTSU阈值
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text4 = pytesseract.image_to_string(otsu, config='--psm 6').strip().upper()
    
    if debug:
        # 保存所有处理后的图像用于比较
        cv2.imwrite("debug_binary.jpg", binary)
        cv2.imwrite("debug_adaptive.jpg", adaptive)
        cv2.imwrite("debug_sharpened.jpg", binary_sharp)
        cv2.imwrite("debug_otsu.jpg", otsu)
        
        print(f"Method 1 (Binary): '{text1}'")
        print(f"Method 2 (Adaptive): '{text2}'")
        print(f"Method 3 (Sharpened): '{text3}'")
        print(f"Method 4 (OTSU): '{text4}'")
    
    # 简单的"投票"系统 - 如果同一文本被多个方法识别，优先选择
    texts = [text1, text2, text3, text4]
    for text in texts:
        if text and texts.count(text) > 1:
            return text
    
    # 如果没有一致的结果，优先返回非空结果
    for text in texts:
        if text:
            return text
    
    return ""


def input_available():
    """Check if input is available without blocking."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# Disable GUI functionality
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

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
        
        text = process_and_recognize(image)
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