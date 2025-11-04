# ============================================================================
# CONFIGURATION SETTINGS
# ============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()



CAMARA_CONFIG = {
    'use_mock': False,
    
    #  CORRECT: Use p-eu domain for URL construction
    'base_url': 'network-as-code.p-eu.rapidapi.com',
    
    # CORRECT: Use nokia domain for headers
    'api_host': 'network-as-code.nokia.rapidapi.com',
    
    'api_key': os.environ.get('RAPIDAPI_KEY', '8d3dd95930mshd018383920dafbep1da792jsn445268c67ddc'),

    # Endpoints remain the same
    'sim_swap_check_endpoint': '/passthrough/camara/v1/sim-swap/sim-swap/v0/check',
    'location_endpoint': '/location-retrieval/v0/retrieve',
    'roaming_endpoint': '/device-status/v0/roaming',
    'device_status_endpoint': '/device-status/v0/connectivity',

    'timeout': 10,
    'test_phone_range': {
        'start': '+61400500800',
        'end': '+61400500999',
        'country': 'Australia',
        'prefix': '+61400500'
    }
}


# ===== HACKATHON PHONE NUMBER HELPERS =====
def get_random_test_number():
    """Get a random test phone number from hackathon range"""
    import random
    suffix = random.randint(800, 999)
    return f"+61400500{suffix}"

def is_valid_test_number(phone_number: str) -> bool:
    """Check if phone number is in hackathon test range"""
    phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Check if it's in the range +61400500800 to +61400500999
    if phone.startswith('+61400500'):
        try:
            suffix = int(phone.replace('+61400500', ''))
            return 800 <= suffix <= 999
        except:
            return False
    return False

def get_all_test_numbers():
    """Get list of all hackathon test phone numbers"""
    return [f"+61400500{i}" for i in range(800, 1000)]


def get_rapidapi_headers():
    """
    Generate authentication headers for RapidAPI
    """
    return {
        'x-rapidapi-key': CAMARA_CONFIG['api_key'],
        'x-rapidapi-host': CAMARA_CONFIG['api_host'],
        'Content-Type': 'application/json'
    }

# ===== PHONE NUMBER FORMAT HELPER =====
def format_phone_for_nokia(phone_number: str) -> str:
    """
    Format phone number according to Nokia CAMARA requirements
    Nokia expects E.164 format: +[country_code][number]
    """
    phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    if not phone.startswith('+'):
        phone = '+91' + phone
    
    return phone

def get_nokia_auth_headers():
    """
    Generate authentication headers for Nokia CAMARA APIs
    
    Nokia typically uses OAuth 2.0 or API Key authentication.
    Check your Nokia Developer Portal for exact requirements.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Method 1: API Key Authentication
    if CAMARA_CONFIG['api_key']:
        headers['X-API-Key'] = CAMARA_CONFIG['api_key']
    
    # Method 2: Bearer Token (OAuth 2.0)
    if CAMARA_CONFIG['oauth_token']:
        headers['Authorization'] = f"Bearer {CAMARA_CONFIG['oauth_token']}"
    
    return headers
FEATURE_COLUMNS = [
    'customer_vintage_bucket', 'customer_risk_rating', 'customer_segment',
    'occupation_type', 'avg_monthly_txn_value', 'kyc_update_freq',
    'pep_highrisk_flag', 'txn_count_1h', 'txn_frequency_day_vs_mean',
    'roundamt_repetitiveness_percent', 'sameday_creditreversal_count_7d',
    'kyc_country', 'kyc_city', 'geo_restriction_level', 'restricted_geo_location'
]

CATEGORICAL_COLUMNS = [
    'customer_vintage_bucket', 'customer_risk_rating', 'customer_segment',
    'occupation_type', 'kyc_update_freq', 'pep_highrisk_flag',
    'sameday_creditreversal_count_7d', 'kyc_country', 'kyc_city',
    'geo_restriction_level', 'restricted_geo_location'
]

LOG_FILE = 'transaction_logs.json'
FEEDBACK_FILE = 'prediction_feedback.json'
def verify_api_configuration():
    """Verify that we're using real APIs"""
    print("\n" + "="*60)
    print("🔍 API CONFIGURATION VERIFICATION")
    print("="*60)
    print(f"USE_MOCK_CAMARA     : {os.environ.get('USE_MOCK_CAMARA', 'not set')}")
    print(f"RAPIDAPI_KEY        : {'✅ SET' if CAMARA_CONFIG['api_key'] else '❌ MISSING'}")
    print(f"Base URL            : {CAMARA_CONFIG['base_url']}")
    print(f"Mock Mode Active    : {CAMARA_CONFIG['use_mock']}")
    print("="*60)
    
    if CAMARA_CONFIG['use_mock']:
        print("⚠️  WARNING: MOCK MODE IS ENABLED!")
        print("   Set USE_MOCK_CAMARA=false in .env to use real APIs")
    else:
        print("✅ REAL API MODE ENABLED")
        if not CAMARA_CONFIG['api_key']:
            print("❌ ERROR: No API key configured!")
        else:
            print("✅ Ready to make real Nokia API calls")
    print("="*60 + "\n")
# REAL CAMARA API Configuration
# CAMARA_CONFIG = {
#     'base_url': 'https://api.nokia.com/camara/v1',  # Replace with actual Nokia NaC endpoint
#     'api_key': os.environ.get('NOKIA_API_KEY', 'YOUR_NOKIA_API_KEY'),
#     'sim_swap_endpoint': '/sim-swap/check',
#     'location_endpoint': '/location-verification/verify',
#     'roaming_endpoint': '/device-roaming/check',
#     'device_status_endpoint': '/device-status/check',
#     'timeout': 10,
#     'use_mock': os.environ.get('USE_MOCK_CAMARA', 'true').lower() == 'true'  # Toggle for testing
# }

# # FATF High-Risk Countries List (Updated 2024)
# FATF_HIGH_RISK_COUNTRIES = [
#     'Myanmar', 'North Korea', 'Iran', 'Afghanistan', 'Pakistan', 'Syria',
#     'Yemen', 'Albania', 'Barbados', 'Burkina Faso', 'Cambodia', 'Cayman Islands',
#     'Democratic Republic of Congo', 'Gibraltar', 'Haiti', 'Jamaica', 'Jordan',
#     'Mali', 'Morocco', 'Mozambique', 'Nicaragua', 'Panama', 'Philippines',
#     'Senegal', 'South Sudan', 'Tanzania', 'Türkiye', 'Uganda', 'United Arab Emirates',
#     'Venezuela', 'Vietnam', 'Zimbabwe'
# ]
