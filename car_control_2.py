#!/usr/bin/env python3
import time
import serial
import serial.tools.list_ports


# auto-detect Arduino port
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


# send command to Arduino
def send_command(command):
    try:
        ser.write((command + "\n").encode())  # send command
        print(f"Sent: {command}")
        time.sleep(0.1)  # wait for command to be processed on Arduino
        response = (
            ser.readline().decode("utf-8").strip()
        )  # read serial response from Arduino
        if response:
            print(f"Arduino: {response}")
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None


# Read distance from ultrasonic sensor
def get_distance():
    send_command("distance")
    time.sleep(0.1)
    distance = ser.readline().decode("utf-8").strip()
    if "Distance:" in distance:
        return int(distance.split(":")[1].strip())  # return distance in cm
    return None


# find Arduino port
arduino_port = find_arduino()
if not arduino_port:
    print("No Arduino found! Please check the connection.")
    exit(1)

try:
    ser = serial.Serial(
        arduino_port, 9600, timeout=1
    )  # open serial port with 1s timeout for reading
    time.sleep(2)  # wait for Arduino to reset
    ser.reset_input_buffer()  # clear input buffer
    print(f"Connected to Arduino on {arduino_port}")

    while True:
        # check for obstacles
        distance = get_distance()
        if distance and distance < 15:
            print("Obstacle detected! Auto-stopping...")
            send_command("x")  # auto-stop

        cmd = input("Enter command (w/s/a/d/x + speed, d? for distance, q to quit): ")

        if cmd.lower() == "q":  # quit
            break
        elif cmd.lower() == "d?":  # read distance
            distance = get_distance()
            if distance:
                print(f"Current Distance: {distance} cm")
            else:
                print("Failed to read distance.")
        elif cmd[0] in ["w", "s", "a", "d", "x"]:
            send_command(cmd)
        else:
            print("Invalid command! Use w/s/a/d/x + optional speed (e.g., w150)")

except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    if "ser" in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
