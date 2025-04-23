import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta, timezone
from azure.iot.device import IoTHubDeviceClient, Message
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
import threading  # For threading.Lock()

# Get connection string from Azure Key Vault
KEY_VAULT_NAME = "your key vault name"
SECRET_NAME = "your secret name"
KVUri = f"https://{KEY_VAULT_NAME}.vault.azure.net"

# Replace with your actual instrumentation key
APP_INSIGHTS_CONNECTION_STRING = "Your connection string"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler for terminal logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Try to initialize AzureLogHandler
try:
    azure_handler = AzureLogHandler(connection_string=APP_INSIGHTS_CONNECTION_STRING)
    
    # Ensure the handler has a lock, if not, assign one
    if azure_handler.lock is None:
        azure_handler.lock = threading.Lock()

    # Add the handler to the logger
    logger.addHandler(azure_handler)
    logger.info("Logger initialized with AzureLogHandler")
except Exception as e:
    logger.error(f"Failed to initialize AzureLogHandler: {e}")
    # Fallback logging to console
    logger.info("Fallback logging initialized")

try:
    credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=KVUri, credential=credential)
    retrieved_secret = vault_client.get_secret(SECRET_NAME)
    CONNECTION_STRING = retrieved_secret.value
    logger.info("IoT Hub connection string retrieved from Key Vault")
except Exception as e:
    logger.exception("Failed to retrieve IoT Hub connection string from Key Vault")
    raise

try:
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    logger.info("IoT Hub client created successfully")
except Exception as e:  
    logger.exception("Failed to create IoT Hub client")
    raise

class IoTSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Temperature Simulator")
        self.root.geometry("300x250")
        self.root.configure(padx=20, pady=20)

        self.device_on = False
        self.temperature = tk.IntVar(value=0)

        self.setup_ui()

        # Send initial data of Off
        self.send_simulated_data()

    def setup_ui(self):
        ttk.Label(self.root, text="Living room thermostat temperature", font=("Segoe UI", 10)).pack(pady=(0, 10))

        self.value_label = ttk.Label(self.root, text="0°C", font=("Segoe UI", 10))
        self.value_label.pack()

        self.slider = ttk.Scale(
            self.root,
            from_=0,
            to=100,
            orient='horizontal',
            variable=self.temperature,
            command=self.update_temperature_label,
            length=200
        )
        self.slider.pack(pady=5)

        self.toggle_button = ttk.Button(self.root, text="Toggle ON/OFF", command=self.toggle_device)
        self.toggle_button.pack(pady=10)

        self.status_label = ttk.Label(self.root, text="Living room thermostat - OFF", font=("Segoe UI", 10))
        self.status_label.pack()

        self.canvas = tk.Canvas(self.root, width=20, height=20, highlightthickness=0)
        self.status_circle = self.canvas.create_oval(2, 2, 18, 18, fill="red")
        self.canvas.pack(pady=5)

        logger.info("IoT Simulator GUI initialized")  # Log GUI initialization

    def update_temperature_label(self, event=None):
        temp = self.temperature.get()
        self.value_label.config(text=f"{temp}°C")
        status_text = "ON" if self.device_on else "OFF"
        self.status_label.config(text=f"Living room thermostat - {status_text}")

    def toggle_device(self):
        self.device_on = not self.device_on
        color = "green" if self.device_on else "red"
        self.canvas.itemconfig(self.status_circle, fill=color)
        self.update_temperature_label()

        logger.info(f"Device toggled {'ON' if self.device_on else 'OFF'}")  # Log device toggle
        self.send_simulated_data()

        if self.device_on:
            self.root.after(2000, self.simulate_data)

    def simulate_data(self):
        if self.device_on:
            self.send_simulated_data()
            self.root.after(2000, self.simulate_data)

    def send_simulated_data(self):
        gmt_plus_5 = timezone(timedelta(hours=5))
        current_time = datetime.now(gmt_plus_5).strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "status": "ON" if self.device_on else "OFF",
            "temperature": self.temperature.get(),
            "timestamp": current_time
        }

        message = Message(json.dumps(data))
        logger.info(f"Sending to Azure IoT Hub: {data}")  # Log data sent
        client.send_message(message)

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTSimulator(root)
    root.mainloop()
