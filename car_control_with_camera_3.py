import cv2
import pytesseract
import time
import serial
import serial.tools.list_ports

# 自动查找 Arduino 端口
def find_arduino():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "ttyUSB" in port.device or "ttyACM" in port.device:
            return port.device
    return None

# 发送指令到 Arduino
def send_command(command):
    try:
        ser.write((command + '\n').encode())  # 发送命令
        print(f"Sent: {command}")
        time.sleep(0.1)  # 等待 Arduino 处理
        response = ser.readline().decode('utf-8').strip()  # 读取返回数据
        if response:
            print(f"Arduino: {response}")
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

# 识别摄像头中的文字
def recognize_text(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 转换为灰度图
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)  # 进行二值化处理
    text = pytesseract.image_to_string(thresh, config='--psm 6')  # OCR 识别文字
    text = text.strip().upper()  # 转换为大写
    return text

# 连接 Arduino
arduino_port = find_arduino()
if not arduino_port:
    print("No Arduino found! Please check the connection.")
    exit(1)

try:
    ser = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {arduino_port}")

    for i in range(5):  # Try indexes 0 to 4
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera detected at index {i}")
            break
        cap.release()

    if not cap.isOpened():
        print("No camera found")
        exit()

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image")
    else:
        cv2.imshow("Camera Test", frame)
        cv2.waitKey(0)

    cap.release()
    cv2.destroyAllWindows()
    exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            continue

        text = recognize_text(frame)
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

        # 显示摄像头画面
        cv2.imshow("Camera", frame)

        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    cap.release()
    cv2.destroyAllWindows()
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
