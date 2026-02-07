#!/usr/bin/env python3
"""
Cloud API Key Manager for Smart Lamp Controller
Manages Tuya cloud API credentials for persistent access
"""
import json
import time
import hashlib
import hmac
import base64
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class TuyaCloudAPI:
    """Tuya Cloud API wrapper for persistent device access"""
    
    def __init__(self, client_id: str, secret: str, region: str = "us"):
        self.client_id = client_id
        self.secret = secret
        self.region = region
        self.base_url = f"https://openapi.tuya{region}.com/v2.0"
        self.access_token = None
        self.token_expires = 0
        
    def _sign_request(self, method: str, path: str, params: Dict[str, Any] = None, body: str = "") -> Dict[str, str]:
        """Generate signed headers for Tuya API request"""
        timestamp = str(int(time.time() * 1000))
        
        # Build query string
        query = ""
        if params:
            query = urlencode(sorted(params.items()))
        
        # Build string to sign
        string_to_sign = f"{method}\n{path}\n{query}\n{body}\n{timestamp}"
        
        # Generate signature
        signature = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        sign = base64.b64encode(signature).decode('utf-8')
        
        return {
            'client_id': self.client_id,
            'sign_method': 'HMAC-SHA256',
            't': timestamp,
            'sign': sign,
            'mode': 'cors',
            'Content-Type': 'application/json'
        }
    
    def get_access_token(self) -> Optional[str]:
        """Get or refresh access token"""
        # Check if current token is still valid
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
        
        # Get new token
        path = "/token"
        url = f"{self.base_url}{path}"
        
        headers = self._sign_request("GET", path)
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data.get('success'):
                self.access_token = data['result']['access_token']
                self.token_expires = time.time() + data['result']['expire_time'] - 60  # 1 minute buffer
                return self.access_token
            else:
                print(f"Token error: {data.get('msg', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Token request failed: {e}")
            return None
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information from cloud API"""
        token = self.get_access_token()
        if not token:
            return None
        
        path = f"/cloud/thing/{device_id}"
        url = f"{self.base_url}{path}"
        
        headers = self._sign_request("GET", path)
        headers['access_token'] = token
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data.get('success'):
                return data['result']
            else:
                print(f"Device info error: {data.get('msg', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Device info request failed: {e}")
            return None
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device status from cloud API"""
        token = self.get_access_token()
        if not token:
            return None
        
        path = f"/cloud/thing/{device_id}/status"
        url = f"{self.base_url}{path}"
        
        headers = self._sign_request("GET", path)
        headers['access_token'] = token
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data.get('success'):
                return data['result']
            else:
                print(f"Device status error: {data.get('msg', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Device status request failed: {e}")
            return None

def setup_cloud_credentials():
    """Setup and save Tuya cloud API credentials"""
    print("=== Tuya Cloud API Setup ===\n")
    
    print("To get your Tuya Cloud API credentials:")
    print("1. Go to https://iot.tuya.com/")
    print("2. Create an account or login")
    print("3. Create a new project")
    print("4. Get your Client ID and Secret from the project settings")
    print()
    
    client_id = input("Enter your Client ID: ").strip()
    secret = input("Enter your Secret: ").strip()
    region = input("Enter region (us, eu, cn) [default: us]: ").strip() or "us"
    
    if not client_id or not secret:
        print("❌ Client ID and Secret are required")
        return
    
    # Test the credentials
    print("\nTesting credentials...")
    api = TuyaCloudAPI(client_id, secret, region)
    
    token = api.get_access_token()
    if token:
        print("✅ Credentials are valid!")
        print(f"Access token: {token[:20]}...")
        
        # Save credentials to config
        config = {}
        try:
            with open("lamp_config.json", 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            pass
        
        # Add cloud API section
        config['cloud_api'] = {
            'client_id': client_id,
            'secret': secret,
            'region': region,
            'enabled': True
        }
        
        with open("lamp_config.json", 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Cloud API credentials saved to lamp_config.json")
        
        # Test with your device
        device_id = input("\nEnter your device ID (from lamp_config.json): ").strip()
        if device_id:
            print(f"Testing device access for {device_id}...")
            device_info = api.get_device_info(device_id)
            if device_info:
                print("✅ Device access successful!")
                print(f"Device info: {json.dumps(device_info, indent=2)}")
            else:
                print("❌ Failed to access device")
    
    else:
        print("❌ Invalid credentials")

def test_cloud_access():
    """Test cloud API access with saved credentials"""
    try:
        with open("lamp_config.json", 'r') as f:
            config = json.load(f)
        
        cloud_config = config.get('cloud_api')
        if not cloud_config or not cloud_config.get('enabled'):
            print("❌ Cloud API not configured or disabled")
            return
        
        device_config = config.get('device')
        if not device_config:
            print("❌ No device configuration found")
            return
        
        print("Testing Cloud API access...")
        api = TuyaCloudAPI(
            cloud_config['client_id'],
            cloud_config['secret'],
            cloud_config.get('region', 'us')
        )
        
        device_id = device_config['id']
        print(f"Device ID: {device_id}")
        
        # Test device info
        device_info = api.get_device_info(device_id)
        if device_info:
            print("✅ Device info retrieved:")
            print(json.dumps(device_info, indent=2))
        
        # Test device status
        device_status = api.get_device_status(device_id)
        if device_status:
            print("✅ Device status retrieved:")
            print(json.dumps(device_status, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("=== Tuya Cloud API Manager ===\n")
    
    print("Choose an option:")
    print("1. Setup Cloud API credentials")
    print("2. Test Cloud API access")
    print("3. Generate curl command for device")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        setup_cloud_credentials()
    
    elif choice == '2':
        test_cloud_access()
    
    elif choice == '3':
        try:
            with open("lamp_config.json", 'r') as f:
                config = json.load(f)
            
            cloud_config = config.get('cloud_api')
            device_config = config.get('device')
            
            if not cloud_config or not device_config:
                print("❌ Missing configuration")
                return
            
            api = TuyaCloudAPI(
                cloud_config['client_id'],
                cloud_config['secret'],
                cloud_config.get('region', 'us')
            )
            
            token = api.get_access_token()
            if token:
                device_id = device_config['id']
                path = f"/cloud/thing/{device_id}"
                url = f"{api.base_url}{path}"
                
                headers = api._sign_request("GET", path)
                headers['access_token'] = token
                
                print("\nGenerated curl command:")
                print("curl --request GET \\")
                print(f'  "{url}" \\')
                for key, value in headers.items():
                    print(f'  --header "{key}: {value}" \\')
                print("  --header \"mode: cors\"")
                print("  --header \"Content-Type: application/json\"")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
