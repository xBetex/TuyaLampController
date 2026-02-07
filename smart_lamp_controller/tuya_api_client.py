"""
Tuya Cloud API Client - Generate signatures and make API calls.

You need your client_id and client_secret from Tuya IoT Platform:
https://iot.tuya.com/ -> Cloud -> Your Project -> Overview
"""

import hashlib
import hmac
import time
import requests
from typing import Optional

# =============================================================================
# CONFIGURATION - Fill these in from your Tuya IoT Platform project
# =============================================================================
CLIENT_ID = "YOUR_TUYA_ACCESS_ID"
CLIENT_SECRET = "YOUR_TUYA_ACCESS_SECRET"
DEVICE_ID = "YOUR_DEVICE_ID"
BASE_URL = "https://openapi.tuyaus.com"  # US datacenter (or .tuyaeu.com / .tuyacn.com)

# =============================================================================
# API Client
# =============================================================================

class TuyaCloudAPI:
    def __init__(self, client_id: str, client_secret: str, base_url: str = BASE_URL):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = ""
        self.refresh_token = ""
        self.token_expiry = 0

    def _calc_sign(self, method: str, path: str, params: dict = None,
                   body: str = "", timestamp: int = None, use_token: bool = True) -> tuple:
        """Calculate HMAC-SHA256 signature for Tuya API."""
        t = timestamp or int(time.time() * 1000)

        # Content hash (SHA256 of body, empty string for GET)
        content_hash = hashlib.sha256(body.encode()).hexdigest()

        # Build string to sign
        # Format: method\ncontent_hash\n\npath
        headers_str = ""  # No signed headers for basic requests
        string_to_sign = f"{method}\n{content_hash}\n{headers_str}\n{path}"

        # Build sign string
        if use_token and self.access_token:
            sign_str = self.client_id + self.access_token + str(t) + string_to_sign
        else:
            sign_str = self.client_id + str(t) + string_to_sign

        # HMAC-SHA256
        sign = hmac.new(
            self.client_secret.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest().upper()

        return sign, t

    def _request(self, method: str, path: str, params: dict = None,
                 body: dict = None, use_token: bool = True) -> dict:
        """Make authenticated request to Tuya API."""
        url = self.base_url + path
        body_str = "" if body is None else str(body)

        sign, t = self._calc_sign(method, path, params, body_str, use_token=use_token)

        headers = {
            "client_id": self.client_id,
            "sign": sign,
            "t": str(t),
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }

        if use_token and self.access_token:
            headers["access_token"] = self.access_token

        response = requests.request(method, url, headers=headers, params=params, json=body)
        return response.json()

    def get_token(self) -> dict:
        """Get access token (first step)."""
        path = "/v1.0/token?grant_type=1"
        result = self._request("GET", path, use_token=False)

        if result.get("success"):
            self.access_token = result["result"]["access_token"]
            self.refresh_token = result["result"]["refresh_token"]
            self.token_expiry = time.time() + result["result"]["expire_time"]
            print(f"Token obtained. Expires in {result['result']['expire_time']}s")
        else:
            print(f"Failed to get token: {result}")

        return result

    def get_device_info(self, device_id: str = DEVICE_ID) -> dict:
        """Get device information including local_key."""
        path = f"/v2.0/cloud/thing/batch?device_ids={device_id}"
        return self._request("GET", path)

    def get_device_status(self, device_id: str = DEVICE_ID) -> dict:
        """Get device current status."""
        path = f"/v1.0/devices/{device_id}/status"
        return self._request("GET", path)

    def get_device_functions(self, device_id: str = DEVICE_ID) -> dict:
        """Get device supported functions/commands."""
        path = f"/v1.0/devices/{device_id}/functions"
        return self._request("GET", path)

    def send_commands(self, device_id: str, commands: list) -> dict:
        """Send commands to device via cloud."""
        path = f"/v1.0/devices/{device_id}/commands"
        return self._request("POST", path, body={"commands": commands})


def main():
    if not CLIENT_SECRET:
        print("=" * 60)
        print("ERROR: CLIENT_SECRET not configured!")
        print("=" * 60)
        print("\nTo get your client_secret:")
        print("1. Go to https://iot.tuya.com/")
        print("2. Click 'Cloud' in the left menu")
        print("3. Select your project")
        print("4. Go to 'Overview' tab")
        print("5. Copy the 'Access Secret/Client Secret'")
        print(f"\nYour client_id is: {CLIENT_ID}")
        print("Paste the client_secret in this file.")
        return

    api = TuyaCloudAPI(CLIENT_ID, CLIENT_SECRET)

    print("=" * 60)
    print("TUYA CLOUD API CLIENT")
    print("=" * 60)

    # Step 1: Get token
    print("\n[1] Getting access token...")
    token_result = api.get_token()
    if not token_result.get("success"):
        return

    # Step 2: Get device info (includes local_key)
    print("\n[2] Getting device info...")
    device_info = api.get_device_info()
    if device_info.get("success"):
        for device in device_info["result"]:
            print(f"\nDevice: {device['name']}")
            print(f"  ID: {device['id']}")
            print(f"  Local Key: {device['local_key']}")
            print(f"  IP: {device['ip']}")
            print(f"  Online: {device['is_online']}")

    # Step 3: Get device status
    print("\n[3] Getting device status...")
    status = api.get_device_status()
    if status.get("success"):
        print("Status:")
        for item in status["result"]:
            print(f"  {item['code']}: {item['value']}")

    # Step 4: Get device functions
    print("\n[4] Getting device functions...")
    functions = api.get_device_functions()
    if functions.get("success"):
        print("Supported functions:")
        for func in functions["result"]["functions"]:
            print(f"  {func['code']}: {func.get('desc', func.get('name', ''))}")


if __name__ == "__main__":
    main()
