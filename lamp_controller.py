#!/usr/bin/env python3
"""
Smart Lamp Controller GUI
Controls Tuya-based RGB smart lamps on your local network
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import tinytuya
import json
from datetime import datetime


class LampController:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Lamp Controller")
        self.root.geometry("600x500")

        # Variables
        self.devices = []
        self.selected_device = None
        self.status_var = tk.StringVar(value="Ready")

        # Create GUI
        self.setup_gui()

        # Auto-discover devices on startup
        self.root.after(1000, self.discover_devices)

    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            main_frame, text="Neo RGB Lamp Controller", font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Device discovery section
        device_frame = ttk.LabelFrame(main_frame, text="Device Discovery", padding="10")
        device_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.discover_btn = ttk.Button(
            device_frame, text="Discover Devices", command=self.discover_devices
        )
        self.discover_btn.grid(row=0, column=0, padx=5)

        self.refresh_btn = ttk.Button(
            device_frame, text="Refresh List", command=self.refresh_device_list
        )
        self.refresh_btn.grid(row=0, column=1, padx=5)

        # Device list
        list_frame = ttk.LabelFrame(main_frame, text="Found Devices", padding="10")
        list_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )

        # Create Treeview for device list
        columns = ("ID", "IP Address", "Name", "Type")
        self.device_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=6
        )

        # Define headings
        self.device_tree.heading("ID", text="Device ID")
        self.device_tree.heading("IP Address", text="IP Address")
        self.device_tree.heading("Name", text="Name")
        self.device_tree.heading("Type", text="Type")

        # Configure column widths
        self.device_tree.column("ID", width=150)
        self.device_tree.column("IP Address", width=120)
        self.device_tree.column("Name", width=150)
        self.device_tree.column("Type", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.device_tree.yview
        )
        self.device_tree.configure(yscrollcommand=scrollbar.set)

        self.device_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Bind selection event
        self.device_tree.bind("<<TreeviewSelect>>", self.on_device_select)

        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Lamp Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # Power controls
        power_frame = ttk.Frame(control_frame)
        power_frame.grid(row=0, column=0, columnspan=4, pady=5)

        self.power_on_btn = ttk.Button(
            power_frame,
            text="💡 Turn ON",
            command=lambda: self.control_lamp(True),
            state="disabled",
        )
        self.power_on_btn.grid(row=0, column=0, padx=5)

        self.power_off_btn = ttk.Button(
            power_frame,
            text="🌙 Turn OFF",
            command=lambda: self.control_lamp(False),
            state="disabled",
        )
        self.power_off_btn.grid(row=0, column=1, padx=5)

        # Brightness control
        ttk.Label(control_frame, text="Brightness:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.brightness_var = tk.IntVar(value=100)
        self.brightness_scale = ttk.Scale(
            control_frame,
            from_=1,
            to=100,
            variable=self.brightness_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_brightness_change,
        )
        self.brightness_scale.grid(row=1, column=1, columnspan=2, pady=5)
        self.brightness_label = ttk.Label(control_frame, text="100%")
        self.brightness_label.grid(row=1, column=3, pady=5)

        # Color temperature (if supported)
        ttk.Label(control_frame, text="Color Temp:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.temp_var = tk.IntVar(value=50)
        self.temp_scale = ttk.Scale(
            control_frame,
            from_=0,
            to=100,
            variable=self.temp_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_temp_change,
        )
        self.temp_scale.grid(row=2, column=1, columnspan=2, pady=5)
        self.temp_label = ttk.Label(control_frame, text="Neutral")
        self.temp_label.grid(row=2, column=3, pady=5)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)

    def log_status(self, message):
        """Update status bar with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")
        self.root.update_idletasks()

    def discover_devices(self):
        """Discover Tuya devices on the network"""
        self.log_status("Discovering devices...")
        self.discover_btn.config(state="disabled")

        # Run discovery in background thread
        threading.Thread(target=self._discover_thread, daemon=True).start()

    def _discover_thread(self):
        """Background thread for device discovery"""
        try:
            # Discover devices using tinytuya
            devices = tinytuya.deviceScan()

            # Update GUI in main thread
            self.root.after(0, self._update_device_list, devices)

        except Exception as e:
            self.root.after(0, self._discovery_error, str(e))
        finally:
            self.root.after(0, lambda: self.discover_btn.config(state="normal"))

    def _update_device_list(self, devices):
        """Update the device list with discovered devices"""
        self.devices = []

        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)

        if not devices:
            self.log_status("No devices found")
            messagebox.showinfo(
                "Discovery",
                "No Tuya devices found on your network.\n"
                "Make sure your lamp is connected to WiFi and "
                "your computer is on the same network.",
            )
            return

        # Add devices to list
        for ip, device_info in devices.items():
            device_id = device_info.get("gwId", "Unknown")
            version = device_info.get("version", "3.1")

            # Try to connect and get more info
            try:
                d = tinytuya.Device(device_id, ip, version)
                status = d.status()
                name = status.get("1", f"Lamp_{device_id[:8]}")
                device_type = "RGB Lamp"

                self.devices.append(
                    {
                        "id": device_id,
                        "ip": ip,
                        "version": version,
                        "name": name,
                        "type": device_type,
                        "device": d,
                    }
                )

                # Add to tree
                self.device_tree.insert(
                    "", "end", values=(device_id, ip, name, device_type)
                )

            except:
                # Add with basic info if can't connect
                self.devices.append(
                    {
                        "id": device_id,
                        "ip": ip,
                        "version": version,
                        "name": f"Lamp_{device_id[:8]}",
                        "type": "Unknown",
                        "device": None,
                    }
                )

                self.device_tree.insert(
                    "",
                    "end",
                    values=(device_id, ip, f"Lamp_{device_id[:8]}", "Unknown"),
                )

        self.log_status(f"Found {len(self.devices)} devices")

    def _discovery_error(self, error_msg):
        """Handle discovery errors"""
        self.log_status(f"Discovery failed: {error_msg}")
        messagebox.showerror(
            "Discovery Error", f"Failed to discover devices:\n{error_msg}"
        )

    def refresh_device_list(self):
        """Refresh the current device list"""
        self._update_device_list({})
        self.log_status("Device list cleared")

    def on_device_select(self, event):
        """Handle device selection"""
        selection = self.device_tree.selection()
        if not selection:
            self.selected_device = None
            self.power_on_btn.config(state="disabled")
            self.power_off_btn.config(state="disabled")
            return

        # Get selected device
        item = self.device_tree.item(selection[0])
        device_id = item["values"][0]

        # Find device in our list
        for device in self.devices:
            if device["id"] == device_id:
                self.selected_device = device
                self.power_on_btn.config(state="normal")
                self.power_off_btn.config(state="normal")

                # Try to get current status
                threading.Thread(
                    target=self._get_device_status, args=(device,), daemon=True
                ).start()
                break

    def _get_device_status(self, device):
        """Get current device status"""
        try:
            if device["device"]:
                status = device["device"].status()
                self.root.after(0, self._update_controls_from_status, status)
        except Exception as e:
            self.root.after(0, lambda: self.log_status(f"Failed to get status: {e}"))

    def _update_controls_from_status(self, status):
        """Update controls based on device status"""
        if "20" in status:  # Brightness
            brightness = int(status["20"])
            self.brightness_var.set(brightness)
            self.brightness_label.config(text=f"{brightness}%")

        if "21" in status:  # Color temperature
            temp = int(status["21"])
            self.temp_var.set(temp)
            self.temp_label.config(text=self._get_temp_label(temp))

        if "1" in status:  # Power state
            is_on = status["1"] == "True"
            self.log_status(f"Device {'ON' if is_on else 'OFF'}")

    def control_lamp(self, turn_on):
        """Turn lamp on/off"""
        if not self.selected_device:
            messagebox.showwarning("No Device", "Please select a device first")
            return

        if not self.selected_device["device"]:
            messagebox.showerror("Connection Error", "Device not properly connected")
            return

        self.log_status(f"Turning lamp {'ON' if turn_on else 'OFF'}...")

        # Run control in background thread
        threading.Thread(
            target=self._control_lamp_thread, args=(turn_on,), daemon=True
        ).start()

    def _control_lamp_thread(self, turn_on):
        """Background thread for lamp control"""
        try:
            device = self.selected_device["device"]

            # Send power command
            result = device.set_status(turn_on, 1)  # Switch 1 = power

            if result.get("Error"):
                raise Exception(result["Error"])

            self.root.after(
                0,
                lambda: self.log_status(
                    f"Lamp turned {'ON' if turn_on else 'OFF'} successfully"
                ),
            )

        except Exception as e:
            error_msg = f"Failed to control lamp: {e}"
            self.root.after(0, lambda: self.log_status(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Control Error", error_msg))

    def on_brightness_change(self, value):
        """Handle brightness change"""
        brightness = int(float(value))
        self.brightness_label.config(text=f"{brightness}%")

        if self.selected_device and self.selected_device["device"]:
            threading.Thread(
                target=self._set_brightness, args=(brightness,), daemon=True
            ).start()

    def _set_brightness(self, brightness):
        """Set lamp brightness"""
        try:
            device = self.selected_device["device"]
            result = device.set_status(brightness, 20)  # DPS 20 = brightness

            if result.get("Error"):
                raise Exception(result["Error"])

            self.root.after(
                0, lambda: self.log_status(f"Brightness set to {brightness}%")
            )

        except Exception as e:
            self.root.after(
                0, lambda: self.log_status(f"Failed to set brightness: {e}")
            )

    def on_temp_change(self, value):
        """Handle color temperature change"""
        temp = int(float(value))
        self.temp_label.config(text=self._get_temp_label(temp))

        if self.selected_device and self.selected_device["device"]:
            threading.Thread(
                target=self._set_temperature, args=(temp,), daemon=True
            ).start()

    def _set_temperature(self, temp):
        """Set color temperature"""
        try:
            device = self.selected_device["device"]
            result = device.set_status(temp, 21)  # DPS 21 = color temperature

            if result.get("Error"):
                raise Exception(result["Error"])

            self.root.after(
                0,
                lambda: self.log_status(
                    f"Color temperature set to {self._get_temp_label(temp)}"
                ),
            )

        except Exception as e:
            self.root.after(
                0, lambda: self.log_status(f"Failed to set temperature: {e}")
            )

    def _get_temp_label(self, temp):
        """Get color temperature label"""
        if temp < 33:
            return "Warm"
        elif temp < 66:
            return "Neutral"
        else:
            return "Cool"


def main():
    root = tk.Tk()
    app = LampController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
