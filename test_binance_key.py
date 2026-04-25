#!/usr/bin/env python3
"""
Binance Key Test Script
Tests a Binance API key/secret against the Spot Test Network (demo environment).
Run this to verify if your key works before using it in Zwesta.
"""

import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode

# Replace these with your actual demo key and secret
API_KEY = '8e0swgyYlgXkoPKGFiWwZwxlihG6u5ajA3V0g7XIEYm3RH1VATsTNv7uI821EBif'
API_SECRET = 'gkhhiwuGMTdD2yv8jax45WVYKXVRF9fb5Mfnq2wIJHViR9M3WqqKRUUFmUxYgBOI'

def test_binance_key():
    base_url = 'https://testnet.binance.vision/api'
    endpoint = '/v3/account'
    url = base_url + endpoint

    # Prepare parameters
    params = {
        'recvWindow': 60000,  # Increased to 60 seconds
        'timestamp': int(time.time() * 1000)
    }

    # Create query string
    query_string = urlencode(params)

    # Sign the request
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    params['signature'] = signature

    # Make the request
    headers = {
        'X-MBX-APIKEY': API_KEY
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Key is valid! Binance accepted the request.")
        elif response.status_code == 401:
            data = response.json()
            code = data.get('code')
            msg = data.get('msg', 'Unknown error')
            print(f"❌ Key rejected: {code} - {msg}")
            if code == -2015:
                print("This means: Invalid API-key, IP, or permissions.")
                print("Check:")
                print("- API key and secret are correct")
                print("- 'Enable Reading' is checked in Binance API settings")
                print("- If IP restriction is enabled, whitelist your backend IP (148.113.5.39)")
        else:
            print(f"Unexpected response: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_binance_key()