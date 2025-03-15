import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports
import subprocess
import numpy as np
import sys
import select
import os
import threading
from picamera2 import Picamera2, Preview

def find_arduino():
    """自动查找Arduino端口"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "ttyUSB" in port.device or "ttyACM" in port.device:
            return port.device
    return None

def send_command(command):
    """向Arduino发送命令并读取响应"""
    try:
        ser.write((command + '\n').encode())
        print(f"发送: {command}")
        time.sleep(0.1)
        response = ser.readline().decode('utf-8').strip()
        if response:
            print(f"Arduino: {response}")
        return response
    except Exception as e:
        print(f"发送命令时出错: {e}")
        return None

def process_and_recognize(image):
    """处理图像并识别文本，应用多种增强方法"""
    # 设置ROI(感兴趣区域) - 可以根据实际情况调整
    height, width = image.shape[:2]
    # 只处理中心区域，这里取中心的60%区域
    y_start = int(height * 0.2)
    y_end = int(height * 0.8)
    x_start = int(width * 0.2)
    x_end = int(width * 0.8)
    roi = image[y_start:y_end, x_start:x_end]
    
    # 转换为灰度
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 应用多种处理方法并选择最佳结果
    results = []
    
    # 方法1: 基本二值化
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    results.append((binary, "binary"))
    
    # 方法2: 自适应阈值
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2)
    results.append((adaptive, "adaptive"))
    
    # 方法3: OTSU阈值
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append((otsu, "otsu"))
    
    # 应用形态学操作改进文本质量
    kernel = np.ones((1, 1), np.uint8)
    for i, (img, name) in enumerate(results):
        # 应用开运算去除小噪点
        opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        # 应用闭运算填充文本中的小孔
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        results[i] = (closing, name)
    
    # 为每种处理后的图像应用OCR
    texts = []
    debug_info = {}
    
    # 自定义Tesseract配置
    custom_config = r'--oem 3 --psm 7 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    for img, name in results:
        # 保存处理后的图像用于调试
        debug_path = f"debug_{name}.jpg"
        cv2.imwrite(debug_path, img)
        
        # 应用OCR
        text = pytesseract.image_to_string(img, config=custom_config).strip().upper()
        texts.append(text)
        debug_info[name] = text
        
    # 打印调试信息
    print("识别结果:")
    for method, text in debug_info.items():
        print(f"  {method}: '{text}'")
    
    # 选择最佳结果：优先选择出现次数最多的非空文本
    non_empty_texts = [t for t in texts if t]
    if non_empty_texts:
        # 统计每个文本出现的次数
        from collections import Counter
        text_counts = Counter(non_empty_texts)
        # 选择出现次数最多的文本
        most_common_text = text_counts.most_common(1)[0][0]
        return most_common_text
    
    return ""

class VideoProcessor:
    def __init__(self, arduino_serial):
        self.ser = arduino_serial
        self.last_command_time = 0
        self.command_cooldown = 1.0  # 命令之间的冷却时间(秒)
        self.running = False
        self.last_text = ""
        self.text_stability_count = 0
        self.stable_text = ""
        
    def send_command_with_cooldown(self, command):
        current_time = time.time()
        if current_time - self.last_command_time >= self.command_cooldown:
            send_command(command)
            self.last_command_time = current_time
            return True
        return False
    
    def process_text(self, text):
        """处理识别到的文本并执行相应命令"""
        if not text:
            return
            
        # 文本稳定性检查 - 同一文本需要连续识别多次才执行命令
        if text == self.last_text:
            self.text_stability_count += 1
        else:
            self.text_stability_count = 0
            self.last_text = text
            
        # 如果文本连续识别3次，认为它是稳定的
        if self.text_stability_count >= 3 and text != self.stable_text:
            self.stable_text = text
            print(f"稳定识别到的文本: {text}")
            
            # 执行相应命令
            if "STOP" in text:
                self.send_command_with_cooldown("x")
            elif "F" in text or "FORWARD" in text:
                self.send_command_with_cooldown("w")
            elif "B" in text or "BACK" in text:
                self.send_command_with_cooldown("s")
            elif "L" in text or "LEFT" in text:
                self.send_command_with_cooldown("a")
            elif "R" in text or "RIGHT" in text:
                self.send_command_with_cooldown("d")
    
    def start_processing(self):
        """启动视频处理"""
        self.running = True
        
        # 初始化Picamera2
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        
        print("视频处理已启动，按'q'退出")
        
        try:
            while self.running:
                # 捕获帧
                frame = picam2.capture_array()
                
                # 每隔几帧保存一张调试图像
                timestamp = int(time.time())
                if timestamp % 10 < 0.1:  # 每10秒左右保存一张
                    cv2.imwrite(f"debug_frame_{timestamp}.jpg", frame)
                
                # 处理图像并识别文本
                text = process_and_recognize(frame)
                
                # 处理识别到的文本
                self.process_text(text)
                
                # 检查输入以便退出
                if input_available():
                    if sys.stdin.readline().strip() == 'q':
                        print("收到退出命令")
                        self.running = False
                
                # 短暂延迟以减少CPU使用
                time.sleep(0.1)
                
        except Exception as e:
            print(f"视频处理时出错: {e}")
        finally:
            picam2.stop()
            print("视频处理已停止")

def input_available():
    """检查是否有可用输入（非阻塞）"""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# 主程序
def main():
    # 禁用GUI功能
    os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # 连接Arduino
    arduino_port = find_arduino()
    if not arduino_port:
        print("未找到Arduino！请检查连接。")
        exit(1)
    
    global ser
    try:
        ser = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print(f"已连接到Arduino，端口: {arduino_port}")
        
        # 创建并启动视频处理器
        processor = VideoProcessor(ser)
        processor.start_processing()
        
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except KeyboardInterrupt:
        print("\n由于键盘中断而退出...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口连接已关闭。")

if __name__ == "__main__":
    main()