import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta, timezone
from azure.eventhub import EventHubProducerClient, EventData

# Replace with your Event Hub connection string (from namespace) and Event Hub name
CONNECTION_STRING = "your connection string"
EVENT_HUB_NAME = "your eventhub name"

producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STRING, eventhub_name=EVENT_HUB_NAME)

class IoTSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Temperature Simulator")
        self.root.geometry("300x250")
        self.root.configure(padx=20, pady=20)

        self.device_on = False
        self.temperature = tk.IntVar(value=0)

        self.setup_ui()

        # send initial data
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

        print("Sending to Azure Event Hub:", data)

        # Send event data
        event_data_batch = producer.create_batch()
        event_data_batch.add(EventData(json.dumps(data)))
        producer.send_batch(event_data_batch)

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTSimulator(root)
    root.mainloop()
