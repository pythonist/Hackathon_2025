# utilities_functions.py - UPDATED to save all score types
import json
import os
import numpy as np
from datetime import datetime
from collections import defaultdict

LOGS_FILE = 'transaction_logs.json'
FEEDBACK_FILE = 'feedback_logs.json'


def convert_to_serializable(obj):
    """Convert NumPy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj


def log_transaction(phone_number, transaction_amount, fraud_probability, risk_level, explanation, transaction_data, camara_data, scoring_breakdown=None,merchant_name=None, payment_method=None):
    """
    Log transaction with FULL customer profile data + ALL SCORE TYPES
    
    NEW: Now saves ml_score, weighted_score, condition_score, and final_score separately
    """
    
    # Convert all NumPy types to native Python types
    transaction_data = convert_to_serializable(transaction_data)
    camara_data = convert_to_serializable(camara_data)
    
    # Extract location from CAMARA data
    camara_location = camara_data.get('location', {})
    current_city = camara_location.get('current_city', transaction_data.get('kyc_city', 'N/A'))
    current_country = camara_location.get('current_country', transaction_data.get('kyc_country', 'N/A'))
    
    # NEW: Extract individual scores from scoring_breakdown
    if scoring_breakdown:
        model_score = scoring_breakdown.get('model_score', fraud_probability * 100)
        weighted_score = scoring_breakdown.get('weighted_score', fraud_probability * 100)
        condition_score = scoring_breakdown.get('condition_score', 0)
        final_score = scoring_breakdown.get('final_score', fraud_probability * 100)
    else:
        # Fallback for backward compatibility
        model_score = fraud_probability * 100
        weighted_score = fraud_probability * 100
        condition_score = 0
        final_score = fraud_probability * 100
    
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'phone_number': str(phone_number),
        'transaction_amount': float(transaction_amount),
        'merchant_name': merchant_name,  # NEW
        'payment_method': payment_method,  # NEW
        # === NEW: MULTIPLE SCORE TYPES ===
        'model_score': float(model_score),           # Base ML score
        'weighted_score': float(weighted_score),      # Weighted with CAMARA
        'condition_score': float(condition_score),    # Rule engine score
        'final_score': float(final_score),           # Final decision score
        
        # Keep fraud_probability for backward compatibility
        'fraud_probability': float(fraud_probability),
        
        'risk_level': str(risk_level),
        'explanation': explanation,
        'camara_data': camara_data,
        
        # === CUSTOMER PROFILE DATA ===
        'customer_vintage': str(transaction_data.get('customer_vintage_bucket', 'N/A')),
        'risk_rating': int(transaction_data.get('customer_risk_rating', 0)) if transaction_data.get('customer_risk_rating') else 'N/A',
        'segment': str(transaction_data.get('customer_segment', 'N/A')),
        'occupation': str(transaction_data.get('occupation_type', 'N/A')),
        
        # Store both KYC and current location
        'kyc_country': str(transaction_data.get('kyc_country', 'N/A')),
        'kyc_city': str(transaction_data.get('kyc_city', 'N/A')),
        'current_country': str(current_country),  # From CAMARA
        'current_city': str(current_city),        # From CAMARA
        
        # For backward compatibility
        'country': str(current_country),
        'city': str(current_city),
        
        'geo_restriction': str(transaction_data.get('geo_restriction_level', 'N/A')),
        'pep_flag': 'Yes' if int(transaction_data.get('pep_highrisk_flag', 0)) == 1 else 'No',
        
        # === TRANSACTION PATTERNS ===
        'txn_count_1h': int(transaction_data.get('txn_count_1h', 0)),
        'credit_reversals_7d': int(transaction_data.get('sameday_creditreversal_count_7d', 0)),
        'avg_monthly_txn': float(transaction_data.get('avg_monthly_txn_value', 0)),
        'txn_frequency': float(transaction_data.get('txn_frequency_day_vs_mean', 0)),
        
        # === FULL TRANSACTION DATA ===
        'full_transaction_data': transaction_data,
        
        # === SCORING BREAKDOWN (for debugging) ===
        'scoring_breakdown': scoring_breakdown if scoring_breakdown else {}
    }
    
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️ Corrupted logs file detected. Creating new logs file.")
                    logs = []
        else:
            logs = []
        
        logs.insert(0, log_entry)
        
        with open(LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
        
        print(f"✅ Transaction logged: {phone_number} from {current_city}, {current_country}")
        print(f"   📊 Scores: ML={model_score:.1f}% | Weighted={weighted_score:.1f}% | Rules={condition_score:.1f}% | Final={final_score:.1f}%")
    except Exception as e:
        print(f"❌ Error logging transaction: {e}")
        import traceback
        traceback.print_exc()


def get_transaction_logs():
    """Get all transaction logs with error handling"""
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                return json.load(f)
        return []
    except json.JSONDecodeError as e:
        print(f"Error loading logs: {e}")
        print("⚠️ Logs file is corrupted. Backing up and creating new file.")
        
        # Backup corrupted file
        if os.path.exists(LOGS_FILE):
            backup_name = f'transaction_logs_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            try:
                os.rename(LOGS_FILE, backup_name)
                print(f"✅ Corrupted file backed up as: {backup_name}")
            except:
                pass
        
        return []
    except Exception as e:
        print(f"Error loading logs: {e}")
        return []


def get_statistics():
    """Calculate statistics from logs"""
    logs = get_transaction_logs()
    
    if not logs:
        return {
            'total_transactions': 0,
            'high_risk_count': 0,
            'sim_swap_detections': 0,
            'location_mismatches': 0,
            'roaming_detections': 0,
            'device_not_connected': 0
        }
    
    stats = {
        'total_transactions': len(logs),
        'high_risk_count': sum(1 for log in logs if log.get('risk_level') == 'High Risk'),
        'medium_risk_count': sum(1 for log in logs if log.get('risk_level') == 'Medium Risk'),
        'low_risk_count': sum(1 for log in logs if log.get('risk_level') == 'Low Risk'),
        'sim_swap_detections': sum(1 for log in logs if log.get('camara_data', {}).get('sim_swap', {}).get('swapped', False)),
        'location_mismatches': sum(1 for log in logs if not log.get('camara_data', {}).get('location', {}).get('verified', True)),
        'roaming_detections': sum(1 for log in logs if log.get('camara_data', {}).get('roaming', {}).get('roaming', False)),
        'device_not_connected': sum(1 for log in logs if log.get('camara_data', {}).get('device_status', {}).get('connection_status') == 'NOT_CONNECTED')
    }
    
    return stats


def check_fatf_country(country):
    """
    Check if country is in FATF high-risk or watch list
    Updated as of 2024
    """
    FATF_HIGH_RISK = [
        'Iran', 'North Korea', 'Myanmar', 'Democratic People\'s Republic of Korea'
    ]
    
    FATF_WATCHLIST = [
        'Pakistan', 'Afghanistan', 'Albania', 'Barbados', 'Burkina Faso',
        'Cameroon', 'Croatia', 'Democratic Republic of the Congo', 'Gibraltar',
        'Haiti', 'Jamaica', 'Jordan', 'Mali', 'Mozambique', 'Nigeria',
        'Panama', 'Philippines', 'Senegal', 'South Africa', 'South Sudan',
        'Syria', 'Tanzania', 'Turkey', 'Uganda', 'United Arab Emirates',
        'Vietnam', 'Yemen'
    ]
    
    is_high_risk = country in FATF_HIGH_RISK
    is_watchlist = country in FATF_WATCHLIST
    
    return {
        'country': country,
        'is_fatf_high_risk': is_high_risk,
        'is_fatf_watchlist': is_watchlist,
        'risk_level': 'High Risk' if is_high_risk else 'Watchlist' if is_watchlist else 'Normal',
        'description': f"{country} is on FATF High-Risk list" if is_high_risk else 
                      f"{country} is on FATF Watchlist" if is_watchlist else 
                      f"{country} is not on FATF lists"
    }


def generate_explanation_hybrid(transaction_data, scoring_breakdown, camara_data):
    """
    Generate human-readable explanation for the hybrid scoring decision
    """
    explanation = {
        'summary': '',
        'factors': [],
        'triggered_rules': []
    }
    
    # Build summary
    decision = scoring_breakdown['decision']
    final_score = scoring_breakdown['final_score']
    
    if decision == "REJECT":
        explanation['summary'] = f"This transaction has been flagged as HIGH RISK (score: {final_score}/100) and should be blocked immediately due to multiple fraud indicators."
    elif decision == "STEP-UP":
        explanation['summary'] = f"This transaction shows MEDIUM RISK signals (score: {final_score}/100) and requires additional verification before processing."
    else:
        explanation['summary'] = f"This transaction appears LEGITIMATE (score: {final_score}/100) with all fraud checks passing normally."
    
    # Add factors
    if scoring_breakdown.get('sim_swap_flag'):
        explanation['factors'].append("Recent SIM swap detected - critical fraud indicator")
    
    if scoring_breakdown.get('location_flag'):
        explanation['factors'].append("Device location does not match registered address")
    
    if scoring_breakdown.get('roaming_flag'):
        explanation['factors'].append("Device is currently roaming in foreign country")
    
    if scoring_breakdown.get('fatf_flag'):
        explanation['factors'].append("Transaction from FATF high-risk country")
    
    if scoring_breakdown.get('device_offline_flag'):
        explanation['factors'].append("Registered device is currently offline")
    
    # Add triggered conditions as rules
    for condition in scoring_breakdown.get('triggered_conditions', []):
        rule_entry = {
            'rule': condition['condition'].replace('_', ' ').title(),
            'severity': 'HIGH' if condition['score'] >= 35 else 'MEDIUM',
            'impact': f"+{condition['score']} risk score",
            'description': condition['description']
        }
        explanation['triggered_rules'].append(rule_entry)
    
    return explanation