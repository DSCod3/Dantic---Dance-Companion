import socket
import time
import random  # For testing with random intensity values

ESP_IP = "192.168.72.124"  # Replace with your ESP32's actual IP
ESP_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # intensity1 = random.randint(0, 100)  # Simulate sensor values
    # intensity2 = random.randint(0, 100)
    intensity1 = 100
    intensity2 = 100
    data = f"{intensity1},{intensity2}\n"  # Format: "intensity1,intensity2"
    sock.sendto(data.encode(), (ESP_IP, ESP_PORT))
    print(f"Sent: {data.strip()}")  # Debugging output
    time.sleep(1 / 60)  # Maintain 60 Hz
