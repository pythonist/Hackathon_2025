# nokia_camara_client.py - Complete Fixed Version

import requests
import random
from datetime import datetime, timedelta
from typing import Dict
from config import CAMARA_CONFIG, get_rapidapi_headers, format_phone_for_nokia  # ✅ Import get_rapidapi_headers


class NokiaCAMARAClient:
    """
    Enhanced Nokia CAMARA Network-as-Code APIs Client
    Supports both real API calls and mock fallback
    """
    
    # Mock locations for fallback (when real API fails)
    MOCK_LOCATIONS = [
        {'country': 'India', 'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
        {'country': 'India', 'city': 'Delhi', 'lat': 28.7041, 'lon': 77.1025},
        {'country': 'India', 'city': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
        {'country': 'Pakistan', 'city': 'Karachi', 'lat': 24.8607, 'lon': 67.0011},
        {'country': 'Bangladesh', 'city': 'Dhaka', 'lat': 23.8103, 'lon': 90.4125},
        {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        {'country': 'UAE', 'city': 'Dubai', 'lat': 25.2048, 'lon': 55.2708},
        {'country': 'Singapore', 'city': 'Singapore', 'lat': 1.3521, 'lon': 103.8198},
        {'country': 'USA', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
        {'country': 'UK', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
    ]
    
    @staticmethod
    @staticmethod
    def _make_api_call(endpoint: str, payload: dict, method: str = 'POST') -> dict:
        """Generic API call handler with proper error handling"""
        
        if CAMARA_CONFIG['use_mock']:
            print(f"⚠️  MOCK MODE: Simulating API call to {endpoint}")
            return None
        
        if not CAMARA_CONFIG['api_key']:
            print("❌ No API credentials configured. Set RAPIDAPI_KEY in .env")
            return None
        
        try:
            # ✅ CORRECT: URL uses base_url (p-eu domain)
            url = f"https://{CAMARA_CONFIG['base_url']}{endpoint}"
            
            # ✅ CORRECT: Headers use api_host (nokia domain)
            headers = get_rapidapi_headers()
            
            print(f"📡 Making REAL API call to: {url}")
            print(f"   Headers: x-rapidapi-host={headers.get('x-rapidapi-host')}")
            print(f"   Payload: {payload}")
            
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=CAMARA_CONFIG['timeout'])
            else:
                response = requests.get(url, params=payload, headers=headers, timeout=CAMARA_CONFIG['timeout'])
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Real API call successful")
                return response.json()
            elif response.status_code == 401:
                print("❌ Authentication failed. Check your RAPIDAPI_KEY")
                print(f"   Response: {response.text[:200]}")
                return None
            elif response.status_code == 404:
                print("❌ API endpoint not found")
                print(f"   URL: {url}")
                print(f"   Response: {response.text[:200]}")
                return None
            else:
                print(f"⚠️  API returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"⚠️  API error: {e}")
            return None
    
    @classmethod
    def verify_location(cls, phone_number: str, expected_lat: float, expected_lon: float, radius: int = 5000) -> Dict:
        """Verify device location using Nokia CAMARA Location Retrieval API"""
        formatted_phone = format_phone_for_nokia(phone_number)
        
        # ✅ FIXED: Use correct payload structure for Nokia API
        payload = {
            'device': {
                'phoneNumber': formatted_phone
            },
            'maxAge': 60  # Nokia expects maxAge, not area verification
        }
        
        # Try real API
        api_response = cls._make_api_call(
            CAMARA_CONFIG['location_endpoint'],
            payload
        )
        
        # Parse real API response
        if api_response:
            # Nokia returns latitude/longitude/accuracy
            current_lat = api_response.get('latitude', expected_lat)
            current_lon = api_response.get('longitude', expected_lon)
            accuracy = api_response.get('accuracy', radius)
            
            # Calculate distance from expected location
            distance = cls._haversine_distance(expected_lat, expected_lon, current_lat, current_lon)
            verified = distance < radius
            
            current_country = cls._reverse_geocode(current_lat, current_lon)
            current_city = cls._get_city_from_coords(current_lat, current_lon)
            
            return {
                'verified': verified,
                'distance_meters': int(distance),
                'current_lat': current_lat,
                'current_lon': current_lon,
                'current_country': current_country,
                'current_city': current_city,
                'expected_country': 'India',
                'risk_score': 0.0 if verified else min(distance / 10000, 1.0),
                'status': 'real_api',
                'accuracy': accuracy
            }
        
        return cls._mock_location_verification(phone_number, expected_lat, expected_lon, radius)
    
    @classmethod
    def check_sim_swap(cls, phone_number: str, max_age_hours: int = 240) -> dict:
        """Check if SIM swap occurred recently using Nokia CAMARA SIM Swap Check API"""
        formatted_phone = format_phone_for_nokia(phone_number)
        
        payload = {
            "phoneNumber": formatted_phone,
            "maxAge": max_age_hours
        }

        # Correct endpoint (check API)
        api_response = cls._make_api_call(
            CAMARA_CONFIG["sim_swap_check_endpoint"],  # /passthrough/camara/v1/sim-swap/sim-swap/v0/check
            payload,
            method="POST"
        )

        if api_response:
            swapped = api_response.get("swapped", False)
            return {
                "swapped": swapped,
                "message": "SIM swap detected" if swapped else "No SIM swap detected",
                "status": "real_api"
            }

        # fallback mock
        return cls._mock_sim_swap()

    
    @classmethod
    def check_device_roaming(cls, phone_number: str) -> dict:
        """Check if device is roaming using Nokia CAMARA Device Roaming Status API"""
        formatted_phone = format_phone_for_nokia(phone_number)
        payload = {
            "device": {
                "phoneNumber": formatted_phone
            }
        }

        # Correct endpoint and HTTP method
        api_response = cls._make_api_call(
            CAMARA_CONFIG["roaming_endpoint"],  # should be /device-roaming-status/v0/roaming
            payload,
            method="POST"
        )

        if api_response:
            roaming = api_response.get("roaming", False)
            country_list = api_response.get("countryName", [])
            roaming_country = (
                country_list[0] if isinstance(country_list, list) and country_list else "Unknown"
            )

            return {
                "roaming": roaming,
                "home_network": "Airtel IN",
                "current_network": f"Network in {roaming_country}" if roaming else "Airtel IN",
                "roaming_country": roaming_country if roaming else None,
                "status": "real_api",
            }

        # fallback mock if API fails
        return cls._mock_roaming()

    
    @classmethod
    def check_device_status(cls, phone_number: str) -> dict:
        """Check device connectivity status using Nokia CAMARA Connectivity API"""
        formatted_phone = format_phone_for_nokia(phone_number)
        payload = {
            "device": {
                "phoneNumber": formatted_phone
            }
        }

        # Correct endpoint and HTTP method
        api_response = cls._make_api_call(
            CAMARA_CONFIG["device_status_endpoint"],  # /passthrough/camara/v1/device-status/device-status/v0/connectivity
            payload,
            method="POST"
        )

        if api_response:
            status = api_response.get("connectivityStatus", "UNKNOWN")
            last_time = api_response.get("lastStatusTime", "Unknown")

            status_map = {
                "CONNECTED_DATA": "DATA",
                "CONNECTED_SMS": "SMS",
                "NOT_CONNECTED": "NOT_CONNECTED",
                "UNKNOWN": "NOT_CONNECTED",
            }

            mapped_status = status_map.get(status, "NOT_CONNECTED")

            return {
                "connection_status": mapped_status,
                "last_seen": last_time if mapped_status == "NOT_CONNECTED" else "Currently Active",
                "network_type": (
                    "4G" if mapped_status == "DATA" else "GSM" if mapped_status == "SMS" else "Unknown"
                ),
                "signal_strength": "Good" if mapped_status != "NOT_CONNECTED" else "No Signal",
                "status": "real_api",
            }

        # fallback mock if API fails
        return cls._mock_device_status()

    
    # ===== MOCK FALLBACK METHODS =====
    
    @classmethod
    def _mock_location_verification(cls, phone_number: str, expected_lat: float, expected_lon: float, radius: int) -> Dict:
        """Mock location data when real API unavailable"""
        phone_hash = sum(ord(c) for c in phone_number) % len(cls.MOCK_LOCATIONS)
        mock_location = cls.MOCK_LOCATIONS[phone_hash]
        
        lat_offset = random.uniform(-0.5, 0.5)
        lon_offset = random.uniform(-0.5, 0.5)
        
        current_lat = mock_location['lat'] + lat_offset
        current_lon = mock_location['lon'] + lon_offset
        
        distance = cls._haversine_distance(expected_lat, expected_lon, current_lat, current_lon)
        verified = distance < radius
        
        return {
            'verified': verified,
            'distance_meters': int(distance),
            'current_lat': current_lat,
            'current_lon': current_lon,
            'current_country': mock_location['country'],
            'current_city': mock_location['city'],
            'expected_country': 'India',
            'risk_score': 0.0 if verified else min(distance / 10000, 1.0),
            'status': 'mock'
        }
    
    @staticmethod
    def _mock_sim_swap() -> Dict:
        """Mock SIM swap data"""
        swapped = random.random() < 0.15
        if swapped:
            days_ago = random.randint(1, 10)
            return {
                'swapped': True,
                'last_swap_date': f"{days_ago} days ago",
                'risk_score': 0.8 if days_ago <= 3 else 0.5,
                'status': 'mock'
            }
        return {
            'swapped': False,
            'last_swap_date': 'No recent swap',
            'risk_score': 0.0,
            'status': 'mock'
        }
    
    @staticmethod
    def _mock_roaming() -> Dict:
        """Mock roaming data"""
        is_roaming = random.random() < 0.2
        if is_roaming:
            networks = ['Vodafone UK', 'T-Mobile DE', 'China Mobile', 'Etisalat UAE']
            countries = ['UK', 'Germany', 'China', 'UAE']
            idx = random.randint(0, len(networks) - 1)
            return {
                'roaming': True,
                'home_network': 'Airtel IN',
                'current_network': networks[idx],
                'roaming_country': countries[idx],
                'status': 'mock'
            }
        return {
            'roaming': False,
            'home_network': 'Airtel IN',
            'current_network': 'Airtel IN',
            'roaming_country': None,
            'status': 'mock'
        }
    
    @staticmethod
    def _mock_device_status() -> Dict:
        """Mock device status data"""
        statuses = ['SMS', 'DATA', 'NOT_CONNECTED']
        weights = [0.15, 0.75, 0.10]
        device_status = random.choices(statuses, weights=weights)[0]
        
        if device_status == 'NOT_CONNECTED':
            hours_ago = random.randint(2, 48)
            last_seen = (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_seen = 'Currently Active'
        
        return {
            'connection_status': device_status,
            'last_seen': last_seen,
            'network_type': '4G' if device_status == 'DATA' else 'GSM' if device_status == 'SMS' else 'Unknown',
            'signal_strength': random.choice(['Excellent', 'Good', 'Fair']) if device_status != 'NOT_CONNECTED' else 'No Signal',
            'status': 'mock'
        }
    
    # ===== HELPER METHODS =====
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000
        φ1 = radians(lat1)
        φ2 = radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lon2 - lon1)
        
        a = sin(Δφ/2)**2 + cos(φ1) * cos(φ2) * sin(Δλ/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def _reverse_geocode(lat: float, lon: float) -> str:
        """Convert coordinates to country"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {'lat': lat, 'lon': lon, 'format': 'json'}
            headers = {'User-Agent': 'FraudGuardAI/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json().get('address', {}).get('country', 'Unknown')
        except:
            pass
        return 'Unknown'
    
    @staticmethod
    def _get_city_from_coords(lat: float, lon: float) -> str:
        """Convert coordinates to city"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {'lat': lat, 'lon': lon, 'format': 'json'}
            headers = {'User-Agent': 'FraudGuardAI/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                address = response.json().get('address', {})
                return (address.get('city') or address.get('town') or 
                       address.get('village') or 'Unknown')
        except:
            pass
        return 'Unknown'