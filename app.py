#flask related
from flask import Flask, render_template, request, jsonify, send_file
from flask_mail import Mail, Message

#inbuilt
from collections import defaultdict
import random
from datetime import datetime, timedelta
import json
import os
import requests
from typing import Dict

#model related
import pickle
import xgboost as xgb

#user defined
from data_generator import generate_unlabeled_dataset
from pdf_exporter import generate_investigation_report_with_llm
from llm_explainer import LLMFraudExplainer
from utilities_functions import *
from config import *
# At top of app.py, replace the CAMARAAPIClient class with:
from nokia_camara_client import NokiaCAMARAClient as CAMARAAPIClient
# Add at the very top of app.py, before other imports
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)


try:
    llm_explainer = LLMFraudExplainer(provider='gemini')  # Change to 'openai' or 'anthropic' with API keys
    print("✅ LLM Explainer initialized")
except Exception as e:
    print(f"⚠️  LLM Explainer initialization warning: {e}")
    llm_explainer = None


# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['ALERT_RECIPIENTS'] = ['fraud-team@example.com', 'security@example.com']

mail = Mail(app)

def send_fraud_alert_email(result, transaction_data):
    """Send comprehensive fraud alert email to security team"""
    if result['risk_level'] != 'High Risk':
        return
    
    try:
        msg = Message(
            subject=f'🚨 HIGH RISK TRANSACTION ALERT - {result["phone_number"]}',
            recipients=app.config['ALERT_RECIPIENTS']
        )
        
        triggered_rules_html = ''.join([
            f"<li><strong>{rule['condition']}</strong>: {rule['description']} (Score: +{rule['score']})</li>"
            for rule in result['triggered_rules']
        ])
        
        msg.html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 700px; margin: 0 auto; }}
                .header {{ background: #ef4444; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .alert-box {{ background: #fef2f2; padding: 20px; border-left: 4px solid #ef4444; margin: 20px 0; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .info-item {{ background: #f9fafb; padding: 15px; border-radius: 6px; }}
                .label {{ color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
                .value {{ color: #111827; font-size: 16px; font-weight: 700; margin-top: 5px; }}
                .rules-list {{ background: #fff7ed; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ HIGH RISK TRANSACTION DETECTED</h1>
                    <p>Immediate Action Required</p>
                </div>
                
                <div class="alert-box">
                    <h2 style="color: #ef4444; margin-top: 0;">Risk Assessment</h2>
                    <div style="font-size: 36px; font-weight: bold; color: #ef4444; text-align: center; margin: 15px 0;">
                        {result['final_score']}/100
                    </div>
                    <p style="text-align: center; color: #6b7280;">Final Risk Score</p>
                </div>
                
                <h3>Transaction Details</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="label">Phone Number</div>
                        <div class="value">{result['phone_number']}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Amount</div>
                        <div class="value">${result['amount']:.2f}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Timestamp</div>
                        <div class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Decision</div>
                        <div class="value" style="color: #ef4444;">{result['decision']}</div>
                    </div>
                </div>
                
                <h3>Network Intelligence (CAMARA APIs)</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="label">SIM Swap Status</div>
                        <div class="value" style="color: {'#ef4444' if result['camara_data']['sim_swap']['swapped'] else '#10b981'};">
                            {'⚠️ DETECTED' if result['camara_data']['sim_swap']['swapped'] else '✅ Clear'}
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="label">Location Verification</div>
                        <div class="value" style="color: {'#10b981' if result['camara_data']['location']['verified'] else '#ef4444'};">
                            {'✅ Verified' if result['camara_data']['location']['verified'] else '⚠️ Mismatch'}
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="label">Current Location</div>
                        <div class="value">{result['camara_data']['location']['current_country']}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">Device Status</div>
                        <div class="value">{result['camara_data']['device_status']['connection_status']}</div>
                    </div>
                </div>
                
                <div class="rules-list">
                    <h3 style="margin-top: 0; color: #ea580c;">Triggered Risk Rules</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        {triggered_rules_html}
                    </ul>
                </div>
                
                <div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <h3 style="margin-top: 0; color: #d97706;">Recommended Action</h3>
                    <p style="margin: 0; color: #78350f; line-height: 1.6;">
                        {result['recommendation']}
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from FraudGuard AI</p>
                    <p>Powered by Nokia Network-as-Code APIs</p>
                    <p>© {datetime.now().year} FraudGuard AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"✅ Fraud alert email sent to {len(app.config['ALERT_RECIPIENTS'])} recipients")
        return True
    except Exception as e:
        print(f"❌ Email alert error: {e}")
        return False
    
    
def send_daily_summary_email():

    """Send daily fraud summary report"""
    try:
        stats = get_statistics()
        logs = get_transaction_logs()
        
        # Get today's transactions
        today = datetime.now().date()
        today_logs = [
            log for log in logs 
            if datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S').date() == today
        ]
        
        high_risk_today = [log for log in today_logs if log['risk_level'] == 'High Risk']
        
        msg = Message(
            subject=f'📊 Daily Fraud Detection Summary - {today.strftime("%B %d, %Y")}',
            recipients=app.config['ALERT_RECIPIENTS']
        )
        
        msg.html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 700px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #4a9eff, #00d9ff); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .stat-box {{ background: #f9fafb; padding: 20px; border-radius: 8px; text-align: center; border: 2px solid #e5e7eb; }}
                .stat-value {{ font-size: 36px; font-weight: bold; margin-bottom: 10px; }}
                .stat-label {{ color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Fraud Detection Summary</h1>
                    <p>{today.strftime("%B %d, %Y")}</p>
                </div>
                
                <h3 style="margin-top: 30px;">Today's Overview</h3>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-value" style="color: #ef4444;">{len(high_risk_today)}</div>
                        <div class="stat-label">High Risk Alerts</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: #f59e0b;">{stats['sim_swap_detections']}</div>
                        <div class="stat-label">SIM Swaps Detected</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: #10b981;">{stats['location_mismatches']}</div>
                        <div class="stat-label">Location Mismatches</div>
                    </div>
                </div>
                
                <h3>System Performance</h3>
                <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
                    <p style="margin: 0;"><strong>Detection Rate:</strong> {(len(high_risk_today)/len(today_logs)*100 if today_logs else 0):.1f}%</p>
                    <p style="margin: 10px 0 0 0;"><strong>Total Transactions Analyzed:</strong> {stats['total_transactions']}</p>
                </div>
                
                <div style="text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px;">
                    <p>FraudGuard AI - Powered by Nokia Network-as-Code</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"✅ Daily summary email sent")
        return True
    except Exception as e:
        print(f"❌ Daily summary email error: {e}")
        return False
# Load model and encoder
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('encoder.pkl', 'rb') as f:
        encoder = pickle.load(f)
    print("✅ Model and encoder loaded successfully")
except Exception as e:
    print(f"❌ Error loading model/encoder: {e}")
    model = None
    encoder = None

# class CAMARAAPIClient:
#     """REAL Nokia CAMARA Network-as-Code APIs Client"""
#     pass
    
    # # Add diverse mock locations for MOCK mode only
    # MOCK_LOCATIONS = [
    #     {'country': 'India', 'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
    #     {'country': 'India', 'city': 'Delhi', 'lat': 28.7041, 'lon': 77.1025},
    #     {'country': 'India', 'city': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
    #     {'country': 'Pakistan', 'city': 'Karachi', 'lat': 24.8607, 'lon': 67.0011},
    #     {'country': 'Pakistan', 'city': 'Lahore', 'lat': 31.5204, 'lon': 74.3587},
    #     {'country': 'Bangladesh', 'city': 'Dhaka', 'lat': 23.8103, 'lon': 90.4125},
    #     {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
    #     {'country': 'UAE', 'city': 'Dubai', 'lat': 25.2048, 'lon': 55.2708},
    #     {'country': 'Singapore', 'city': 'Singapore', 'lat': 1.3521, 'lon': 103.8198},
    #     {'country': 'USA', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
    #     {'country': 'UK', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
    # ]
    
    # @staticmethod
    # def _make_api_call(endpoint: str, payload: dict) -> dict:
    #     """Generic API call handler with fallback to mock data"""
    #     if CAMARA_CONFIG['use_mock']:
    #         print(f"⚠️ Using MOCK data for {endpoint} (set USE_MOCK_CAMARA=false for real calls)")
    #         return None  # Return None to trigger mock fallback
        
    #     try:
    #         url = f"{CAMARA_CONFIG['base_url']}{endpoint}"
    #         headers = {
    #             'Authorization': f"Bearer {CAMARA_CONFIG['api_key']}",
    #             'Content-Type': 'application/json'
    #         }
            
    #         response = requests.post(
    #             url,
    #             json=payload,
    #             headers=headers,
    #             timeout=CAMARA_CONFIG['timeout']
    #         )
            
    #         if response.status_code == 200:
    #             return response.json()
    #         else:
    #             print(f"⚠️ API call failed: {response.status_code} - {response.text}")
    #             return None
                
    #     except requests.exceptions.Timeout:
    #         print(f"⚠️ API timeout for {endpoint}")
    #         return None
    #     except Exception as e:
    #         print(f"⚠️ API error for {endpoint}: {e}")
    #         return None
    
    # @staticmethod
    # def verify_location(phone_number: str, expected_lat: float, expected_lon: float, radius: int = 5000) -> Dict:
    #     """Verify device location using Nokia CAMARA Location API"""
    #     payload = {
    #         'phoneNumber': phone_number,
    #         'latitude': expected_lat,
    #         'longitude': expected_lon,
    #         'accuracy': radius
    #     }
        
    #     # TRY REAL API FIRST
    #     api_response = CAMARAAPIClient._make_api_call(
    #         CAMARA_CONFIG['location_endpoint'],
    #         payload
    #     )
        
    #     # IF REAL API SUCCEEDED, PARSE IT
    #     if api_response:
    #         verified = api_response.get('verificationResult') == 'VERIFIED'
    #         distance = api_response.get('distanceMeters', 0)
    #         current_lat = api_response.get('currentLatitude')
    #         current_lon = api_response.get('currentLongitude')
            
    #         # Reverse geocode to get country and city
    #         current_country = CAMARAAPIClient._reverse_geocode(current_lat, current_lon)
    #         current_city = CAMARAAPIClient._get_city_from_coords(current_lat, current_lon)
            
    #         return {
    #             'verified': verified,
    #             'distance_meters': distance,
    #             'current_lat': current_lat,
    #             'current_lon': current_lon,
    #             'current_country': current_country,
    #             'current_city': current_city,
    #             'expected_country': 'India',
    #             'risk_score': 0.0 if verified else min(distance / 10000, 1.0),
    #             'status': 'success'
    #         }
        
    #     # ELSE USE MOCK DATA (only when API returns None)
    #     else:
    #         # FIXED: Use diverse mock locations instead of always using KYC coordinates
    #         phone_hash = sum(ord(c) for c in phone_number) % len(CAMARAAPIClient.MOCK_LOCATIONS)
    #         mock_location = CAMARAAPIClient.MOCK_LOCATIONS[phone_hash]
            
    #         # Add some random variation (±0.5 degrees ~ 50km)
    #         lat_offset = random.uniform(-0.5, 0.5)
    #         lon_offset = random.uniform(-0.5, 0.5)
            
    #         current_lat = mock_location['lat'] + lat_offset
    #         current_lon = mock_location['lon'] + lon_offset
    #         current_country = mock_location['country']
    #         current_city = mock_location['city']
            
    #         # Calculate distance from expected location using Haversine formula
    #         distance = CAMARAAPIClient._haversine_distance(
    #             expected_lat, expected_lon, 
    #             current_lat, current_lon
    #         )
            
    #         verified = distance < radius
            
    #         return {
    #             'verified': verified,
    #             'distance_meters': int(distance),
    #             'current_lat': current_lat,
    #             'current_lon': current_lon,
    #             'current_country': current_country,
    #             'current_city': current_city,
    #             'expected_country': 'India',
    #             'risk_score': 0.0 if verified else min(distance / 10000, 1.0),
    #             'status': 'mock'
    #         }
    
    # @staticmethod
    # def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    #     """Calculate distance between two coordinates in meters"""
    #     from math import radians, sin, cos, sqrt, atan2
        
    #     R = 6371000  # Earth radius in meters
    #     φ1 = radians(lat1)
    #     φ2 = radians(lat2)
    #     Δφ = radians(lat2 - lat1)
    #     Δλ = radians(lon2 - lon1)
        
    #     a = sin(Δφ/2)**2 + cos(φ1) * cos(φ2) * sin(Δλ/2)**2
    #     c = 2 * atan2(sqrt(a), sqrt(1-a))
        
    #     return R * c
    
    # @staticmethod
    # def _reverse_geocode(lat: float, lon: float) -> str:
    #     """Convert coordinates to country using OpenStreetMap Nominatim API"""
    #     try:
    #         url = f"https://nominatim.openstreetmap.org/reverse"
    #         params = {
    #             'lat': lat,
    #             'lon': lon,
    #             'format': 'json',
    #             'addressdetails': 1
    #         }
    #         headers = {'User-Agent': 'FraudGuardAI/1.0'}
            
    #         response = requests.get(url, params=params, headers=headers, timeout=5)
    #         if response.status_code == 200:
    #             data = response.json()
    #             return data.get('address', {}).get('country', 'Unknown')
    #     except:
    #         pass
    #     return 'Unknown'
    
    # @staticmethod
    # def _get_city_from_coords(lat: float, lon: float) -> str:
    #     """Convert coordinates to city using OpenStreetMap Nominatim API"""
    #     try:
    #         url = f"https://nominatim.openstreetmap.org/reverse"
    #         params = {
    #             'lat': lat,
    #             'lon': lon,
    #             'format': 'json',
    #             'addressdetails': 1
    #         }
    #         headers = {'User-Agent': 'FraudGuardAI/1.0'}
            
    #         response = requests.get(url, params=params, headers=headers, timeout=5)
    #         if response.status_code == 200:
    #             data = response.json()
    #             address = data.get('address', {})
    #             # Try different city fields
    #             city = (address.get('city') or 
    #                    address.get('town') or 
    #                    address.get('village') or 
    #                    address.get('county') or 
    #                    'Unknown')
    #             return city
    #     except:
    #         pass
    #     return 'Unknown'
    
    # @staticmethod
    # def check_sim_swap(phone_number: str, max_age_hours: int = 240) -> Dict:
    #     """Check if SIM swap occurred recently using Nokia CAMARA API"""
    #     payload = {
    #         'phoneNumber': phone_number,
    #         'maxAgeHours': max_age_hours
    #     }
        
    #     # TRY REAL API
    #     api_response = CAMARAAPIClient._make_api_call(
    #         CAMARA_CONFIG['sim_swap_endpoint'], 
    #         payload
    #     )
        
    #     # IF REAL API SUCCEEDED
    #     if api_response:
    #         return {
    #             'swapped': api_response.get('swapped', False),
    #             'last_swap_date': api_response.get('lastSwapDate', 'N/A'),
    #             'risk_score': api_response.get('riskScore', 0.0),
    #             'status': 'success'
    #         }
        
    #     # ELSE USE MOCK
    #     else:
    #         swapped = random.random() < 0.15
    #         if swapped:
    #             days_ago = random.randint(1, 10)
    #             return {
    #                 'swapped': True,
    #                 'last_swap_date': f"{days_ago} days ago",
    #                 'risk_score': 0.8 if days_ago <= 3 else 0.5,
    #                 'status': 'mock'
    #             }
    #         else:
    #             return {
    #                 'swapped': False,
    #                 'last_swap_date': 'No recent swap',
    #                 'risk_score': 0.0,
    #                 'status': 'mock'
    #             }
    
    # @staticmethod
    # def check_device_roaming(phone_number: str) -> Dict:
    #     """Check if device is roaming using Nokia CAMARA API"""
    #     payload = {'phoneNumber': phone_number}
        
    #     # TRY REAL API
    #     api_response = CAMARAAPIClient._make_api_call(
    #         CAMARA_CONFIG['roaming_endpoint'],
    #         payload
    #     )
        
    #     # IF REAL API SUCCEEDED
    #     if api_response:
    #         return {
    #             'roaming': api_response.get('roaming', False),
    #             'home_network': api_response.get('homeNetwork', 'Unknown'),
    #             'current_network': api_response.get('currentNetwork', 'Unknown'),
    #             'roaming_country': api_response.get('roamingCountry'),
    #             'status': 'success'
    #         }
        
    #     # ELSE USE MOCK
    #     else:
    #         is_roaming = random.random() < 0.2
    #         if is_roaming:
    #             networks = ['Vodafone UK', 'T-Mobile DE', 'China Mobile', 'Etisalat UAE']
    #             return {
    #                 'roaming': True,
    #                 'home_network': 'Airtel IN',
    #                 'current_network': random.choice(networks),
    #                 'roaming_country': random.choice(['UK', 'Germany', 'China', 'UAE']),
    #                 'status': 'mock'
    #             }
    #         else:
    #             return {
    #                 'roaming': False,
    #                 'home_network': 'Airtel IN',
    #                 'current_network': 'Airtel IN',
    #                 'roaming_country': None,
    #                 'status': 'mock'
    #             }
    
    # @staticmethod
    # def check_device_status(phone_number: str) -> Dict:
    #     """Check device connectivity status using Nokia CAMARA API"""
    #     payload = {'phoneNumber': phone_number}
        
    #     # TRY REAL API
    #     api_response = CAMARAAPIClient._make_api_call(
    #         CAMARA_CONFIG['device_status_endpoint'],
    #         payload
    #     )
        
    #     # IF REAL API SUCCEEDED
    #     if api_response:
    #         return {
    #             'connection_status': api_response.get('connectionStatus', 'UNKNOWN'),
    #             'last_seen': api_response.get('lastSeen', 'Unknown'),
    #             'network_type': api_response.get('networkType', 'Unknown'),
    #             'signal_strength': api_response.get('signalStrength', 'Unknown'),
    #             'status': 'success'
    #         }
        
    #     # ELSE USE MOCK
    #     else:
    #         statuses = ['SMS', 'DATA', 'NOT_CONNECTED']
    #         weights = [0.15, 0.75, 0.10]
    #         device_status = random.choices(statuses, weights=weights)[0]
            
    #         if device_status == 'NOT_CONNECTED':
    #             hours_ago = random.randint(2, 48)
    #             last_seen = (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
    #         else:
    #             last_seen = 'Currently Active'
            
    #         return {
    #             'connection_status': device_status,
    #             'last_seen': last_seen,
    #             'network_type': '4G' if device_status == 'DATA' else 'GSM' if device_status == 'SMS' else 'Unknown',
    #             'signal_strength': random.choice(['Excellent', 'Good', 'Fair', 'Weak']) if device_status != 'NOT_CONNECTED' else 'No Signal',
    #             'status': 'mock'
    #         }



class HybridRiskEngine:
    """Enhanced Two-Layer Fraud Detection Engine with FATF Check"""
    
    WEIGHTS = {
        'model_probability': 0.4,
        'location_verified': 0.2,
        'sim_swap_detected': 0.2,
        'device_roaming': 0.1,
        'fatf_country': 0.1
    }
    
    CONDITION_SCORES = {
        'location_suspicious': 50,
        'sim_swap_detected': 40,
        'device_roaming': 20,
        'fatf_high_risk': 35,
        'device_offline': 25
    }
    
    THRESHOLDS = {
        'accept': 35,
        'stepup': 70
    }
    
    @classmethod
    def calculate_fraud_score(cls, model_score: float, camara_data: dict, transaction_data: dict) -> dict:
        """Calculate comprehensive fraud score with FATF check"""
        
        # Extract CAMARA flags
        location_verified = 1 if camara_data.get('location', {}).get('verified', True) else 0
        sim_swap_detected = 1 if camara_data.get('sim_swap', {}).get('swapped', False) else 0
        device_roaming = cls._check_device_roaming(camara_data, transaction_data)
        
        # NEW: FATF Country Check
        current_country = camara_data.get('location', {}).get('current_country', 'Unknown')
        fatf_check = check_fatf_country(current_country)
        is_fatf_high_risk = 1 if fatf_check['is_fatf_high_risk'] else 0
        
        # Device offline check
        device_status = camara_data.get('device_status', {}).get('connection_status', 'DATA')
        is_device_offline = 1 if device_status == 'NOT_CONNECTED' else 0
        
        # Calculate weighted score
        weighted_score_raw = (
            cls.WEIGHTS['model_probability'] * model_score +
            cls.WEIGHTS['location_verified'] * (1 - location_verified) +
            cls.WEIGHTS['sim_swap_detected'] * sim_swap_detected +
            cls.WEIGHTS['device_roaming'] * device_roaming +
            cls.WEIGHTS['fatf_country'] * is_fatf_high_risk
        )
        
        weighted_score = round(weighted_score_raw * 100, 2)
        
        # Condition-based scores
        condition_scores = []
        triggered_conditions = []
        
        if location_verified == 0:
            condition_scores.append(cls.CONDITION_SCORES['location_suspicious'])
            triggered_conditions.append({
                'condition': 'LOCATION_SUSPICIOUS',
                'score': cls.CONDITION_SCORES['location_suspicious'],
                'description': f'Device location does not match KYC address (Distance: {camara_data.get("location", {}).get("distance_meters", 0)/1000:.1f} km)'
            })
        
        if sim_swap_detected == 1:
            condition_scores.append(cls.CONDITION_SCORES['sim_swap_detected'])
            triggered_conditions.append({
                'condition': 'SIM_SWAP_DETECTED',
                'score': cls.CONDITION_SCORES['sim_swap_detected'],
                'description': f"Recent SIM swap detected ({camara_data.get('sim_swap', {}).get('last_swap_date', 'N/A')})"
            })
        
        if device_roaming == 1:
            condition_scores.append(cls.CONDITION_SCORES['device_roaming'])
            triggered_conditions.append({
                'condition': 'DEVICE_ROAMING',
                'score': cls.CONDITION_SCORES['device_roaming'],
                'description': f'Device roaming in {camara_data.get("roaming", {}).get("roaming_country", "unknown country")}'
            })
        
        if is_fatf_high_risk == 1:
            condition_scores.append(cls.CONDITION_SCORES['fatf_high_risk'])
            triggered_conditions.append({
                'condition': 'FATF_HIGH_RISK_COUNTRY',
                'score': cls.CONDITION_SCORES['fatf_high_risk'],
                'description': f'Transaction from FATF high-risk country: {current_country}'
            })
        
        if is_device_offline == 1:
            condition_scores.append(cls.CONDITION_SCORES['device_offline'])
            triggered_conditions.append({
                'condition': 'DEVICE_OFFLINE',
                'score': cls.CONDITION_SCORES['device_offline'],
                'description': f'Device not connected to network (Last seen: {camara_data.get("device_status", {}).get("last_seen", "Unknown")})'
            })
        
        condition_score = max(condition_scores) if condition_scores else 0
        final_score = max(weighted_score, condition_score)
        
        # Decision logic
        if final_score < cls.THRESHOLDS['accept']:
            decision = "ACCEPT"
            risk_level = "Low Risk"
            recommendation = "Transaction approved. Proceed with standard processing."
        elif final_score <= cls.THRESHOLDS['stepup']:
            decision = "STEP-UP"
            risk_level = "Medium Risk"
            recommendation = "Additional verification required. Implement step-up authentication."
        else:
            decision = "REJECT"
            risk_level = "High Risk"
            recommendation = "Transaction blocked. Manual review required."
        
        return {
            'model_score': round(model_score * 100, 2),
            'location_flag': 1 - location_verified,
            'sim_swap_flag': sim_swap_detected,
            'roaming_flag': device_roaming,
            'fatf_flag': is_fatf_high_risk,
            'device_offline_flag': is_device_offline,
            'weighted_score': weighted_score,
            'condition_score': condition_score,
            'triggered_conditions': triggered_conditions,
            'final_score': final_score,
            'decision': decision,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'fatf_check': fatf_check
        }
    
    @staticmethod
    def _check_device_roaming(camara_data: dict, transaction_data: dict) -> int:
        roaming_api_result = camara_data.get('roaming', {})
        if roaming_api_result.get('roaming', False):
            return 1
        
        current_country = camara_data.get('location', {}).get('current_country', 'Unknown')
        kyc_country = transaction_data.get('kyc_country', 'Unknown')
        
        if current_country != 'Unknown' and kyc_country != 'Unknown':
            if current_country != kyc_country:
                return 1
        
        return 0


def predict_fraud_hybrid(phone_number, transaction_amount,merchant_name=None, payment_method=None):
    """Enhanced prediction with real coordinates and FATF check"""
    if model is None or encoder is None:
        return None, "Model or encoder not loaded", None, None
    
    df_synthetic = generate_unlabeled_dataset()
    df_synthetic['phone_number'] = phone_number
    df_synthetic['avg_monthly_txn_value'] = transaction_amount
    
    id_columns = ['country_code', 'phone_number', 'full_phone', 'fraud_label', 'customer_id']
    X_new = df_synthetic.drop(columns=[col for col in id_columns if col in df_synthetic.columns], errors='ignore')
    
    missing_cols = set(FEATURE_COLUMNS) - set(X_new.columns)
    for col in missing_cols:
        X_new[col] = 0
    
    X_new = X_new[FEATURE_COLUMNS]
    transaction_data = X_new.iloc[0].to_dict()
    
    try:
        X_new[CATEGORICAL_COLUMNS] = encoder.transform(X_new[CATEGORICAL_COLUMNS])
    except Exception as e:
        return None, f"Encoding error: {e}", None, None
    
    try:
        dnew = xgb.DMatrix(X_new, enable_categorical=False, feature_names=FEATURE_COLUMNS)
        model_score = model.predict(dnew)[0]
        
        # Get KYC coordinates (from customer profile)
        kyc_lat = 26.4499  # Kanpur coordinates
        kyc_lon = 80.3319
        
        print(f"📡 Calling CAMARA APIs for {phone_number}...")
        camara_client = CAMARAAPIClient()
        
        sim_swap_data = camara_client.check_sim_swap(phone_number)
        location_data = camara_client.verify_location(
            phone_number,
            expected_lat=kyc_lat,
            expected_lon=kyc_lon,
            radius=50000
        )
        roaming_data = camara_client.check_device_roaming(phone_number)
        device_status_data = camara_client.check_device_status(phone_number)
        
        camara_data = {
            'sim_swap': sim_swap_data,
            'location': location_data,
            'roaming': roaming_data,
            'device_status': device_status_data
        }
        api_statuses = {
        'sim_swap': sim_swap_data.get('status', 'unknown'),
        'location': location_data.get('status', 'unknown'),
        'roaming': roaming_data.get('status', 'unknown'),
        'device_status': device_status_data.get('status', 'unknown')
        }
        all_real_api = all(status == 'real_api' for status in api_statuses.values())
        any_mock = any(status == 'mock' for status in api_statuses.values())
        # Print verification
        print("\n" + "="*60)
        print("🔍 CAMARA API STATUS VERIFICATION:")
        print("="*60)
        print(f"  SIM Swap API      : {api_statuses['sim_swap'].upper()}")
        print(f"  Location API      : {api_statuses['location'].upper()}")
        print(f"  Roaming API       : {api_statuses['roaming'].upper()}")
        print(f"  Device Status API : {api_statuses['device_status'].upper()}")
        print("="*60)
        if all_real_api:
            print("✅ ALL APIs using REAL Nokia data")
        elif any_mock:
            print("⚠️  Some APIs using MOCK data (fallback)")
        print("="*60 + "\n")
        
        camara_data = {
            'sim_swap': sim_swap_data,
            'location': location_data,
            'roaming': roaming_data,
            'device_status': device_status_data,
            'api_status_summary': {
                'all_real': all_real_api,
                'any_mock': any_mock,
                'details': api_statuses
            }
        }

        # Apply Hybrid Risk Engine with FATF check
        scoring_breakdown = HybridRiskEngine.calculate_fraud_score(
            model_score=model_score,
            camara_data=camara_data,
            transaction_data=transaction_data
        )
        
        explanation = generate_explanation_hybrid(
        transaction_data,
        scoring_breakdown,
        camara_data
        )
        
        # === NEW: Generate LLM-powered explanation ===
        llm_explanation = None
        if llm_explainer:
            try:
                # Get customer history
                all_logs = get_transaction_logs()
                customer_history = [log for log in all_logs if log['phone_number'] == phone_number]
                
                # Generate advanced explanation
                llm_explanation = llm_explainer.generate_fraud_explanation(
                    current_transaction={
                        'phone_number': phone_number,
                        'amount': transaction_amount,
                        **transaction_data
                    },
                    customer_history=customer_history,
                    camara_data=camara_data,
                    ml_scores=scoring_breakdown
                )
            except Exception as e:
                print(f"LLM explanation error: {e}")
                llm_explanation = None
        
        # Build complete result (add llm_explanation)
        result = {
            'phone_number': phone_number,
            'amount': transaction_amount,
            'merchant_name': merchant_name,  # NEW
            'payment_method': payment_method,
            # Core Scores
            'model_score': scoring_breakdown['model_score'],
            'weighted_score': scoring_breakdown['weighted_score'],
            'condition_score': scoring_breakdown['condition_score'],
            'final_score': scoring_breakdown['final_score'],
            
            # Decision
            'decision': scoring_breakdown['decision'],
            'risk_level': scoring_breakdown['risk_level'],
            'recommendation': scoring_breakdown['recommendation'],
            
            # Detailed breakdown
            'scoring_breakdown': scoring_breakdown,
            'explanation': explanation,
            'llm_explanation': llm_explanation,
            'camara_data': camara_data,
            
            # === NEW: Add API status for UI display ===
            'api_mode': 'REAL' if all_real_api else 'MIXED',
            'api_statuses': api_statuses,
            
            # For backward compatibility
            'probability': scoring_breakdown['final_score'] / 100,
            'base_probability': model_score,
            'triggered_rules': scoring_breakdown['triggered_conditions']
        }
        
        return result, None, transaction_data, camara_data
    except Exception as e:
        return None, f"Prediction error: {e}", None, None


# ROUTES

@app.route('/api/send-daily-report', methods=['POST'])
def trigger_daily_report():
    """Manually trigger daily summary email"""
    try:
        send_daily_summary_email()
        return jsonify({'status': 'success', 'message': 'Daily report sent successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/')
def index():
    stats = get_statistics()
    return render_template('index.html', stats=stats,config={'CAMARA_CONFIG': CAMARA_CONFIG})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        phone_number = request.form.get('phone_number', '').strip()
        transaction_amount = request.form.get('transaction_amount', '').strip()
        merchant_name = request.form.get('merchant_name', '').strip()  # NEW
        payment_method = request.form.get('payment_method', 'UPI').strip()
        if not phone_number or not transaction_amount:
            stats = get_statistics()
            return render_template('index.html', 
                                 error="Please enter both phone number and transaction amount", 
                                 stats=stats,
                                 config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE
        
        try:
            transaction_amount = float(transaction_amount)
            if transaction_amount <= 0:
                stats = get_statistics()
                return render_template('index.html', 
                                     error="Transaction amount must be positive", 
                                     stats=stats,
                                     config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE
        except ValueError:
            stats = get_statistics()
            return render_template('index.html', 
                                 error="Invalid transaction amount", 
                                 stats=stats,
                                 config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE
        
        result, error, transaction_data, camara_data = predict_fraud_hybrid(phone_number, transaction_amount,merchant_name=merchant_name,  # NEW
            payment_method=payment_method)
        
        if error:
            stats = get_statistics()
            return render_template('index.html', 
                                 error=error, 
                                 stats=stats,
                                 config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE
        result['merchant_name'] = merchant_name  # NEW
        result['payment_method'] = payment_method
        # === UPDATED: Pass scoring_breakdown to log_transaction ===
        log_transaction(
            phone_number,
            transaction_amount,
            result['final_score'] / 100,  # fraud_probability (for backward compatibility)
            result['risk_level'],
            result['explanation'],
            transaction_data,
            camara_data,
            scoring_breakdown=result['scoring_breakdown'],
            merchant_name=merchant_name,  # NEW
            payment_method=payment_method # NEW: Pass all scores
        )
        
        # Send email alert for high risk
        if result['risk_level'] == 'High Risk':
            send_fraud_alert_email(result, transaction_data)
        
        stats = get_statistics()
        return render_template('index.html', 
                             result=result, 
                             stats=stats,
                             config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE
    
    except Exception as e:
        stats = get_statistics()
        return render_template('index.html', 
                             error=f"Unexpected error: {str(e)}", 
                             stats=stats,
                             config={'CAMARA_CONFIG': CAMARA_CONFIG})  # ADD HERE

@app.route('/api/logs')
def api_logs():
    logs = get_transaction_logs()
    return jsonify(logs)


@app.route('/api/stats')
def api_stats():
    stats = get_statistics()
    return jsonify(stats)


@app.route('/logs')
def view_logs():
    logs = get_transaction_logs()
    stats = get_statistics()
    return render_template('logs.html', logs=logs, stats=stats)


@app.route('/investigation/<phone_number>')
def investigation_view(phone_number):
    all_logs = get_transaction_logs()
    phone_logs = [log for log in all_logs if log['phone_number'] == phone_number]
    
    if not phone_logs:
        stats = {
            'total_txns': 0,
            'high_risk_txns': 0,
            'total_amount': 0,
            'avg_risk_score': 0
        }
    else:
        stats = {
            'total_txns': len(phone_logs),
            'high_risk_txns': sum(1 for log in phone_logs if log['risk_level'] == 'High Risk'),
            'total_amount': sum(log['transaction_amount'] for log in phone_logs),
            'avg_risk_score': sum(log['fraud_probability'] for log in phone_logs) / len(phone_logs)
        }
    
    return render_template('investigation.html', phone_number=phone_number, logs=phone_logs, stats=stats)


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    phone_number = data.get('phone_number')
    feedback_type = data.get('feedback_type')
    
    feedback_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'phone_number': phone_number,
        'feedback': feedback_type
    }
    
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                feedbacks = json.load(f)
        else:
            feedbacks = []
        
        feedbacks.append(feedback_entry)
        
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(feedbacks, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Thank you for your feedback!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/dashboard')
def analytics_dashboard():
    logs = get_transaction_logs()
    stats = get_statistics()
    
    from dashboard_analytics import calculate_all_analytics
    analytics = calculate_all_analytics(logs)
    
    return render_template('dashboard.html', analytics=analytics, stats=stats)


@app.route('/analytics')
def analytics_page():
    logs = get_transaction_logs()
    
    from dashboard_analytics import calculate_roi_metrics
    roi_data = calculate_roi_metrics(logs)
    
    return render_template('analytics.html', roi_data=roi_data)


@app.route('/api/fraud-heatmap')
def fraud_heatmap():
    """Generate 24-hour fraud activity heatmap with real data"""
    logs = get_transaction_logs()
    
    hourly_fraud = defaultdict(lambda: {'high_risk': 0, 'total': 0})
    
    for log in logs:
        try:
            timestamp = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
            hour = timestamp.hour
            
            hourly_fraud[hour]['total'] += 1
            if log['risk_level'] == 'High Risk':
                hourly_fraud[hour]['high_risk'] += 1
        except:
            continue
    
    # Calculate fraud rate per hour
    hourly_data = {}
    for hour in range(24):
        total = hourly_fraud[hour]['total']
        high_risk = hourly_fraud[hour]['high_risk']
        fraud_rate = (high_risk / total * 100) if total > 0 else 0
        
        hourly_data[hour] = {
            'total': total,
            'high_risk': high_risk,
            'fraud_rate': round(fraud_rate, 1)
        }
    
    return jsonify({'hourly_fraud': hourly_data})


@app.route('/api/fraud-geographic')
def fraud_geographic():
    """Geographic fraud clusters with real coordinates - FIXED"""
    logs = get_transaction_logs()
    
    location_data = defaultdict(lambda: {
        'count': 0,
        'high_risk': 0,
        'total_amount': 0,
        'coords': []
    })
    
    for log in logs:
        camara_loc = log.get('camara_data', {}).get('location', {})
        
        # FIXED: Use city from CAMARA data, not from transaction data
        current_city = camara_loc.get('current_city')
        current_country = camara_loc.get('current_country', 'Unknown')
        
        # Fallback to transaction data only if CAMARA data missing
        if not current_city:
            current_city = log.get('city', 'Unknown')
        if current_country == 'Unknown':
            current_country = log.get('country', 'Unknown')
        
        location = f"{current_city}, {current_country}"
        
        # Get actual coordinates from CAMARA API
        lat = camara_loc.get('current_lat')
        lon = camara_loc.get('current_lon')
        
        # Only add if we have valid coordinates
        if lat and lon and lat != 0 and lon != 0:
            location_data[location]['coords'].append((lat, lon))
            location_data[location]['count'] += 1
            location_data[location]['total_amount'] += log.get('transaction_amount', 0)
            
            if log.get('risk_level') == 'High Risk':
                location_data[location]['high_risk'] += 1
    
    clusters = []
    for location, data in location_data.items():
        if data['count'] > 0 and data['coords']:
            # Average coordinates for clustering
            avg_lat = sum(c[0] for c in data['coords']) / len(data['coords'])
            avg_lon = sum(c[1] for c in data['coords']) / len(data['coords'])
            
            risk_rate = (data['high_risk'] / data['count']) * 100
            risk_level = 'High' if risk_rate > 50 else 'Medium' if risk_rate > 20 else 'Low'
            
            clusters.append({
                'location': location,
                'lat': avg_lat,
                'lon': avg_lon,
                'count': data['count'],
                'risk_level': risk_level,
                'risk_rate': round(risk_rate, 1),
                'total_amount': data['total_amount']
            })
    
    # Debug logging
    print(f"✅ Generated {len(clusters)} geographic clusters")
    for cluster in clusters[:3]:
        print(f"   📍 {cluster['location']}: {cluster['count']} txns at ({cluster['lat']:.2f}, {cluster['lon']:.2f})")
    
    return jsonify({'clusters': clusters})


@app.route('/api/velocity-checks')
def velocity_checks():
    """Enhanced velocity anomaly detection"""
    logs = get_transaction_logs()
    
    phone_transactions = defaultdict(list)
    for log in logs:
        phone_transactions[log['phone_number']].append(log)
    
    anomalies = []
    
    for phone, transactions in phone_transactions.items():
        if len(transactions) < 3:
            continue
        
        sorted_txns = sorted(transactions, key=lambda x: x['timestamp'])
        
        # Check for rapid transactions in 30-minute windows
        for i in range(len(sorted_txns) - 2):
            window_txns = sorted_txns[i:i+3]
            
            try:
                first_time = datetime.strptime(window_txns[0]['timestamp'], '%Y-%m-%d %H:%M:%S')
                last_time = datetime.strptime(window_txns[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')
                
                time_diff_minutes = (last_time - first_time).total_seconds() / 60
                
                if time_diff_minutes <= 30:
                    locations = set()
                    total_amount = 0
                    high_risk_count = 0
                    
                    for txn in window_txns:
                        locations.add(f"{txn.get('city', 'Unknown')}, {txn.get('country', 'Unknown')}")
                        total_amount += txn.get('transaction_amount', 0)
                        if txn.get('risk_level') == 'High Risk':
                            high_risk_count += 1
                    
                    anomalies.append({
                        'phone': phone,
                        'transaction_count': len(window_txns),
                        'time_window': f'{int(time_diff_minutes)} minutes',
                        'location_count': len(locations),
                        'total_amount': total_amount,
                        'high_risk_count': high_risk_count,
                        'severity': 'HIGH' if high_risk_count > 0 else 'MEDIUM'
                    })
                    break
            except:
                continue
    
    # Sort by severity
    anomalies.sort(key=lambda x: (x['severity'] == 'HIGH', x['high_risk_count']), reverse=True)
    
    return jsonify({'anomalies': anomalies[:10]})


@app.route('/api/network-behavior')
def network_behavior():
    """Enhanced network behavior timeline"""
    logs = get_transaction_logs()
    
    events = []
    
    for log in logs:
        phone = log['phone_number']
        timestamp = log['timestamp']
        camara_data = log.get('camara_data', {})
        risk_level = log.get('risk_level', 'Low Risk')
        
        # SIM Swap events
        if camara_data.get('sim_swap', {}).get('swapped'):
            events.append({
                'type': 'SIM Swap',
                'phone': phone,
                'timestamp': timestamp,
                'severity': 'HIGH',
                'details': f"SIM swap detected - {camara_data['sim_swap'].get('last_swap_date', 'Unknown date')}",
                'risk_level': risk_level
            })
        
        # Location mismatch events
        if not camara_data.get('location', {}).get('verified', True):
            distance = camara_data.get('location', {}).get('distance_meters', 0)
            current_country = camara_data.get('location', {}).get('current_country', 'Unknown')
            
            # Check if FATF country
            fatf_check = check_fatf_country(current_country)
            severity = 'CRITICAL' if fatf_check['is_fatf_high_risk'] else 'HIGH'
            
            events.append({
                'type': 'Location Change',
                'phone': phone,
                'timestamp': timestamp,
                'severity': severity,
                'details': f"Location mismatch - {distance/1000:.1f} km from KYC address in {current_country}" + 
                          (" (FATF HIGH-RISK COUNTRY)" if fatf_check['is_fatf_high_risk'] else ""),
                'risk_level': risk_level
            })
        
        # Roaming events
        if camara_data.get('roaming', {}).get('roaming'):
            network = camara_data['roaming'].get('current_network', 'Unknown')
            country = camara_data['roaming'].get('roaming_country', 'Unknown')
            events.append({
                'type': 'Roaming',
                'phone': phone,
                'timestamp': timestamp,
                'severity': 'MEDIUM',
                'details': f"Device roaming on {network} in {country}",
                'risk_level': risk_level
            })
        
        # Device offline events
        if camara_data.get('device_status', {}).get('connection_status') == 'NOT_CONNECTED':
            last_seen = camara_data['device_status'].get('last_seen', 'Unknown')
            events.append({
                'type': 'Device Offline',
                'phone': phone,
                'timestamp': timestamp,
                'severity': 'MEDIUM',
                'details': f"Device not connected - Last seen: {last_seen}",
                'risk_level': risk_level
            })
        
        # High-risk transaction events
        if risk_level == 'High Risk':
            amount = log.get('transaction_amount', 0)
            events.append({
                'type': 'High Risk Transaction',
                'phone': phone,
                'timestamp': timestamp,
                'severity': 'HIGH',
                'details': f"High-risk transaction detected - ${amount:.2f}",
                'risk_level': risk_level
            })
    
    # Sort by timestamp (newest first) and severity
    events.sort(key=lambda x: (x['timestamp'], x['severity'] == 'CRITICAL', x['severity'] == 'HIGH'), reverse=True)
    
    return jsonify({'events': events[:30]})


# In your app.py

@app.route('/export-investigation/<phone_number>')
def export_investigation_report(phone_number):
    '''Export investigation report as PDF'''
    all_logs = get_transaction_logs() # Or your function to load logs
    phone_logs = [log for log in all_logs if log['phone_number'] == phone_number]
    
    if not phone_logs:
        return jsonify({'error': 'No data found'}), 404
    
    # --- *** THIS IS THE UPDATED STATS BLOCK *** ---
    high_risk_logs = [log for log in phone_logs if log['risk_level'] == 'High Risk']
    medium_risk_logs = [log for log in phone_logs if log['risk_level'] == 'Medium Risk']
    low_risk_logs = [log for log in phone_logs if log['risk_level'] == 'Low Risk']

    stats = {
        'total_txns': len(phone_logs),
        'high_risk_txns': len(high_risk_logs),
        'medium_risk_txns': len(medium_risk_logs),  # <-- NEW
        'low_risk_txns': len(low_risk_logs),        # <-- NEW
        'total_amount': sum(log['transaction_amount'] for log in phone_logs),
        'avg_risk_score': sum(log['fraud_probability'] for log in phone_logs) / len(phone_logs)
    }
    
    # --- Find the latest LLM explanation (if any) ---
    latest_llm_explanation = None
    for log in reversed(phone_logs): # Check newest logs first
        if log.get('explanation') and log['explanation'].get('generation_method'):
            latest_llm_explanation = log['explanation']
            break # Found the latest one
    
    # Pass all data to the PDF generator
    pdf_buffer = generate_investigation_report_with_llm(
        phone_number, 
        phone_logs, 
        stats,
        latest_llm_explanation # Pass the LLM data
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'fraud_investigation_{phone_number}_{datetime.now().strftime("%Y%m%d")}.pdf'
    )
# NEW ROUTE: Get LLM explanation for existing transaction
@app.route('/api/get-llm-explanation/<phone_number>')
def get_llm_explanation(phone_number):
    """
    Generate LLM explanation for an existing transaction
    """
    if not llm_explainer:
        return jsonify({'error': 'LLM explainer not available'}), 503
    
    try:
        # Get all logs
        all_logs = get_transaction_logs()
        
        # Find transactions for this phone
        customer_history = [log for log in all_logs if log['phone_number'] == phone_number]
        
        if not customer_history:
            return jsonify({'error': 'No transactions found for this phone number'}), 404
        
        # Get most recent transaction
        latest_txn = customer_history[0]
        
        # Extract data
        camara_data = latest_txn.get('camara_data', {})
        
        # Build ML scores from logged data
        ml_scores = {
            'final_score': latest_txn.get('fraud_probability', 0) * 100,
            'model_score': latest_txn.get('fraud_probability', 0) * 100,
            'weighted_score': latest_txn.get('fraud_probability', 0) * 100,
            'condition_score': 0,
            'decision': 'REJECT' if latest_txn.get('risk_level') == 'High Risk' else 
                       'STEP-UP' if latest_txn.get('risk_level') == 'Medium Risk' else 'ACCEPT'
        }
        
        # Generate explanation
        llm_explanation = llm_explainer.generate_fraud_explanation(
            current_transaction={
                'phone_number': phone_number,
                'amount': latest_txn.get('transaction_amount', 0),
                'timestamp': latest_txn.get('timestamp'),
                'kyc_city': latest_txn.get('city', 'Unknown'),
                'kyc_country': latest_txn.get('country', 'Unknown')
            },
            customer_history=customer_history,
            camara_data=camara_data,
            ml_scores=ml_scores
        )
        
        return jsonify({
            'success': True,
            'explanation': llm_explanation
        })
    
    except Exception as e:
        print(f"Error generating LLM explanation: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/regenerate-explanation', methods=['POST'])
def regenerate_explanation():
    """
    Regenerate explanation (useful for testing different LLM providers)
    """
    data = request.json
    phone_number = data.get('phone_number')
    provider = data.get('provider', 'mock')  # 'openai', 'anthropic', or 'mock'
    
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    
    try:
        # Create new explainer with specified provider
        temp_explainer = LLMFraudExplainer(provider=provider)
        
        # Get transaction data
        all_logs = get_transaction_logs()
        customer_history = [log for log in all_logs if log['phone_number'] == phone_number]
        
        if not customer_history:
            return jsonify({'error': 'No transactions found'}), 404
        
        latest_txn = customer_history[0]
        camara_data = latest_txn.get('camara_data', {})
        
        ml_scores = {
            'final_score': latest_txn.get('fraud_probability', 0) * 100,
            'model_score': latest_txn.get('fraud_probability', 0) * 100,
            'weighted_score': latest_txn.get('fraud_probability', 0) * 100,
            'condition_score': 0,
            'decision': 'REJECT' if latest_txn.get('risk_level') == 'High Risk' else 
                       'STEP-UP' if latest_txn.get('risk_level') == 'Medium Risk' else 'ACCEPT'
        }
        
        # Generate explanation
        llm_explanation = temp_explainer.generate_fraud_explanation(
            current_transaction={
                'phone_number': phone_number,
                'amount': latest_txn.get('transaction_amount', 0),
                'timestamp': latest_txn.get('timestamp'),
                'kyc_city': latest_txn.get('city', 'Unknown'),
                'kyc_country': latest_txn.get('country', 'Unknown')
            },
            customer_history=customer_history,
            camara_data=camara_data,
            ml_scores=ml_scores
        )
        
        return jsonify({
            'success': True,
            'explanation': llm_explanation,
            'provider': provider
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Add this new route to app.py for paginated API access (optional optimization)

@app.route('/api/logs/paginated')
def api_logs_paginated():
    """Get paginated logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    all_logs = get_transaction_logs()
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_logs = all_logs[start_idx:end_idx]
    
    return jsonify({
        'logs': paginated_logs,
        'total': len(all_logs),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(all_logs) + per_page - 1) // per_page
    })
if __name__ == '__main__':
    # Add to app.py startup
    from config import verify_api_configuration
    verify_api_configuration()  # Run verification on startup
    
    print("\n" + "="*50)
    print("FraudHive Starting...")
    print(f"API Mode: {'REAL' if not CAMARA_CONFIG['use_mock'] else 'MOCK'}")
    print(f"RapidAPI Key: {'✅ Set' if CAMARA_CONFIG['api_key'] else '❌ Missing'}")
    print("="*50 + "\n")
    
   # Schedule daily report at 8 AM (optional - requires APScheduler)
    # from apscheduler.schedulers.background import BackgroundScheduler
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(func=send_daily_summary_email, trigger="cron", hour=8)
    # scheduler.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)