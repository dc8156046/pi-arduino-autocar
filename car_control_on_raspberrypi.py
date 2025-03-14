#!/usr/bin/env python3
import time

import serial

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1.0)
    #time.sleep(3)
    ser.reset_input_buffer()
    
    def send_command(command):
        ser.write((command + '\n').encode())  # Send command
        print(f"Sent: {command}")
        line = ser.readline().decode('utf-8').rstrip()
        print(line)
        time.sleep(2)  # Small delay

    try:
        while True:
            cmd = input("Enter command (w: Forward, s: Backward, a: Left, d: Right, x: Stop, q: Quit): ")
            if cmd == 'q':
                break
            send_command(cmd)

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        ser.close()
