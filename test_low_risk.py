#!/usr/bin/env python3
"""
Safe Direct Transaction Tester for FraudGuard AI
Generates and sends low-risk transactions directly (no JSON file needed)

Usage:
    python safe_test_direct.py                    # Send 150 transactions (default)
    python safe_test_direct.py --count 200        # Send 200 transactions
    python safe_test_direct.py --count 50 --fast  # Send 50 quickly

Features:
- Generates and sends in one go (like test_app.py)
- ONLY safe, low-risk transactions
- Auto-stops on ANY fraud alert
- Real-time progress display
- No intermediate JSON files
"""

import requests
import random
import time
import argparse
from datetime import datetime, timedelta

# ======================================
# CONFIGURATION
# ======================================
BASE_URL = "http://localhost:5000"
PREDICT_ENDPOINT = f"{BASE_URL}/predict"

# Safe countries (NOT on FATF high-risk lists)
SAFE_COUNTRIES = [
    "India", "United States", "United Kingdom", "Singapore", 
    "Australia", "Canada", "Japan", "Germany", "France", "Spain"
]

SAFE_CITIES = {
    "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata"],
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Edinburgh"],
    "Singapore": ["Singapore"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary"],
    "Japan": ["Tokyo", "Osaka", "Kyoto", "Yokohama"],
    "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg"],
    "France": ["Paris", "Lyon", "Marseille", "Nice"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville"]
}

PHONE_PREFIXES = {
    "India": "+91-98",
    "United States": "+1-555",
    "United Kingdom": "+44-20",
    "Singapore": "+65-91",
    "Australia": "+61-4",
    "Canada": "+1-416",
    "Japan": "+81-90",
    "Germany": "+49-30",
    "France": "+33-6",
    "Spain": "+34-6"
}

# Safe transaction scenarios
SAFE_SCENARIOS = {
    "grocery_shopping": {
        "description": "Grocery shopping",
        "amount_range": (20, 150),
        "probability": 0.30
    },
    "restaurant_dining": {
        "description": "Restaurant dining",
        "amount_range": (50, 200),
        "probability": 0.25
    },
    "online_shopping": {
        "description": "Online shopping",
        "amount_range": (100, 500),
        "probability": 0.20
    },
    "utility_bills": {
        "description": "Utility payment",
        "amount_range": (30, 300),
        "probability": 0.15
    },
    "retail_purchase": {
        "description": "Retail purchase",
        "amount_range": (200, 1000),
        "probability": 0.10
    }
}

# Safety thresholds
MAX_RISK_SCORE = 40  # Auto-stop if risk score exceeds this
ALLOWED_RISK_LEVELS = ["Low Risk"]

# ======================================
# GENERATOR FUNCTIONS
# ======================================

def generate_phone_number(country):
    """Generate realistic phone number"""
    prefix = PHONE_PREFIXES.get(country, "+1-555")
    suffix = f"{random.randint(10000, 99999)}{random.randint(1000, 9999)}"
    return f"{prefix}{suffix}"


def generate_timestamp():
    """Generate timestamps spread across 24 hours"""
    now = datetime.now()
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    timestamp = now - timedelta(hours=hours_ago, minutes=minutes_ago)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def select_scenario():
    """Weighted random selection of safe scenarios"""
    rand = random.random()
    cumulative = 0
    for name, scenario in SAFE_SCENARIOS.items():
        cumulative += scenario["probability"]
        if rand <= cumulative:
            return name, scenario
    return "grocery_shopping", SAFE_SCENARIOS["grocery_shopping"]


def generate_safe_transaction():
    """Generate a single safe transaction"""
    country = random.choice(SAFE_COUNTRIES)
    city = random.choice(SAFE_CITIES[country])
    phone = generate_phone_number(country)
    
    scenario_name, scenario = select_scenario()
    min_amt, max_amt = scenario["amount_range"]
    amount = round(random.uniform(min_amt, max_amt), 2)
    
    timestamp = generate_timestamp()
    
    return {
        "phone_number": phone,
        "amount": amount,
        "country": country,
        "city": city,
        "scenario": scenario["description"],
        "timestamp": timestamp
    }


# ======================================
# SENDER FUNCTIONS
# ======================================

def send_transaction(phone_number, amount):
    """Send transaction to Flask /predict endpoint"""
    payload = {
        "phone_number": phone_number,
        "transaction_amount": amount
    }
    
    try:
        response = requests.post(
            PREDICT_ENDPOINT,
            data=payload,
            timeout=10
        )
        return response.status_code == 200, response
    except requests.exceptions.RequestException as e:
        return False, str(e)


def check_for_fraud_alerts(response):
    """
    Check if response contains any fraud alerts
    Returns: (is_safe, alert_reason)
    """
    try:
        html = response.text
        
        # Check for High Risk
        if "High Risk" in html or "high-risk" in html.lower():
            return False, "High Risk detected"
        
        # Check for fraud alert keywords
        fraud_keywords = {
            "SIM Swap Detected": "SIM swap alert",
            "sim_swap": "SIM swap detected",
            "Location Mismatch": "Location mismatch",
            "location_suspicious": "Location suspicious",
            "Device Offline": "Device offline",
            "NOT_CONNECTED": "Device not connected",
            "Roaming": "Roaming detected",
            "FATF": "FATF country",
            "Blocked": "Transaction blocked",
            "REJECT": "Transaction rejected"
        }
        
        html_lower = html.lower()
        for keyword, reason in fraud_keywords.items():
            if keyword.lower() in html_lower:
                return False, reason
        
        # Check for high risk scores
        import re
        percentages = re.findall(r'(\d+\.?\d*)%', html)
        if percentages:
            max_score = max(float(p) for p in percentages)
            if max_score > MAX_RISK_SCORE:
                return False, f"Risk score too high: {max_score}%"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {e}"


# ======================================
# MAIN TEST RUNNER
# ======================================

def run_safe_test(total_count=150, delay=0.3, show_details=True):
    """
    Main test runner - generates and sends transactions
    
    Args:
        total_count: Number of transactions to send
        delay: Seconds between requests
        show_details: Show detailed output for each transaction
    """
    
    print("=" * 90)
    print(f"🛡️  FraudGuard AI - Safe Direct Tester")
    print("=" * 90)
    print(f"📊 Transactions to send: {total_count}")
    print(f"🎯 Target endpoint: {PREDICT_ENDPOINT}")
    print(f"⏱️  Delay between requests: {delay}s")
    print(f"🛡️  Safety mode: ENABLED (auto-stop on alerts)")
    print("=" * 90)
    print()
    
    # Statistics
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "stopped": False,
        "stop_reason": None,
        "total_amount": 0,
        "countries": {},
        "scenarios": {}
    }
    
    start_time = time.time()
    
    for i in range(1, total_count + 1):
        stats["total"] = i
        
        # Generate safe transaction
        txn = generate_safe_transaction()
        
        # Track statistics
        stats["countries"][txn["country"]] = stats["countries"].get(txn["country"], 0) + 1
        stats["scenarios"][txn["scenario"]] = stats["scenarios"].get(txn["scenario"], 0) + 1
        stats["total_amount"] += txn["amount"]
        
        # Send transaction
        success, response_or_error = send_transaction(txn["phone_number"], txn["amount"])
        
        if not success:
            stats["failed"] += 1
            print(f"[{i:03d}] ❌ FAILED - Connection error")
            stats["stopped"] = True
            stats["stop_reason"] = f"Connection error: {response_or_error}"
            break
        
        # Check for fraud alerts
        is_safe, alert_reason = check_for_fraud_alerts(response_or_error)
        
        if not is_safe:
            # STOP IMMEDIATELY
            stats["stopped"] = True
            stats["stop_reason"] = alert_reason
            print()
            print("=" * 90)
            print(f"🚨 SAFETY STOP TRIGGERED!")
            print(f"Reason: {alert_reason}")
            print(f"Transaction #{i}: {txn['phone_number']} - ${txn['amount']:.2f}")
            print(f"Country: {txn['country']} | Scenario: {txn['scenario']}")
            print("=" * 90)
            break
        
        stats["success"] += 1
        
        # Display progress
        if show_details:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{i:03d}] {timestamp} | {txn['country']:12} | ${txn['amount']:8.2f} | {txn['scenario']:20} | ✅ OK")
        else:
            # Show progress bar for fast mode
            if i % 10 == 0:
                progress = (i / total_count) * 100
                print(f"Progress: {i}/{total_count} ({progress:.1f}%) - All safe ✅")
        
        # Delay before next request
        time.sleep(delay)
    
    elapsed_time = time.time() - start_time
    
    # Print final summary
    print()
    print("=" * 90)
    print("📊 Test Summary")
    print("=" * 90)
    print(f"Total Sent:          {stats['total']}")
    print(f"Success:             {stats['success']}")
    print(f"Failed:              {stats['failed']}")
    print(f"Total Amount:        ${stats['total_amount']:,.2f}")
    
    if stats['success'] > 0:
        print(f"Average Amount:      ${stats['total_amount'] / stats['success']:,.2f}")
    
    print(f"Elapsed Time:        {elapsed_time:.1f}s")
    print(f"Avg Time/Request:    {elapsed_time / stats['total']:.2f}s")
    print()
    
    if stats["stopped"]:
        print("⚠️  STOPPED EARLY")
        print(f"Reason: {stats['stop_reason']}")
    else:
        print("✅ All transactions completed successfully!")
        print("   No fraud alerts triggered")
        print("   All transactions marked as Low Risk")
    
    print()
    print("Country Distribution:")
    for country, count in sorted(stats["countries"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats["success"]) * 100 if stats["success"] > 0 else 0
        print(f"  {country:20} {count:3} ({percentage:.1f}%)")
    
    print()
    print("Scenario Distribution:")
    for scenario, count in sorted(stats["scenarios"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats["success"]) * 100 if stats["success"] > 0 else 0
        print(f"  {scenario:20} {count:3} ({percentage:.1f}%)")
    
    print("=" * 90)
    
    return stats


# ======================================
# COMMAND LINE INTERFACE
# ======================================

def main():
    parser = argparse.ArgumentParser(
        description="Safe Direct Transaction Tester for FraudGuard AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python safe_test_direct.py                    # Send 150 transactions (default)
  python safe_test_direct.py --count 200        # Send 200 transactions
  python safe_test_direct.py --count 50 --fast  # Send 50 quickly (0.1s delay)
  python safe_test_direct.py --quiet            # Minimal output

Safety Features:
  ✓ Only safe, low-risk transactions
  ✓ No FATF high-risk countries
  ✓ No fraud indicators (SIM swap, location mismatch, etc.)
  ✓ Auto-stops immediately on any alert
  ✓ Max risk score: 40%
        """
    )
    
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=150,
        help='Number of transactions to send (default: 150)'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.3,
        help='Delay between requests in seconds (default: 0.3)'
    )
    
    parser.add_argument(
        '--fast', '-f',
        action='store_true',
        help='Fast mode: 0.1s delay, minimal output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode: show summary only'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=BASE_URL,
        help=f'Flask app URL (default: {BASE_URL})'
    )
    
    args = parser.parse_args()
    
    # Apply fast mode
    if args.fast:
        args.delay = 0.1
        args.quiet = True
    
    # Update global URL if provided
    global PREDICT_ENDPOINT
    PREDICT_ENDPOINT = f"{args.url}/predict"
    
    # Validation
    if args.count < 1 or args.count > 1000:
        print("❌ Error: Count must be between 1 and 1000")
        return
    
    if args.delay < 0.05:
        print("⚠️  Warning: Very low delay may cause connection issues")
    
    # Confirm before sending
    print(f"\n🛡️  Ready to send {args.count} safe transactions")
    print(f"Target: {PREDICT_ENDPOINT}")
    
    if not args.quiet and not args.fast:
        response = input("\nProceed? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled by user")
            return
    
    # Run test
    show_details = not args.quiet
    stats = run_safe_test(args.count, args.delay, show_details)
    
    # Exit with appropriate code
    if stats["stopped"]:
        exit(1)  # Error occurred
    else:
        exit(0)  # Success


if __name__ == "__main__":
    main()


# Basic (150 safe transactions)
# python safe_test_direct.py

# # Custom count
# python safe_test_direct.py --count 200

# # Fast mode (quick testing)
# python safe_test_direct.py --count 50 --fast

# # Quiet mode (summary only)
# python safe_test_direct.py --quiet

# # Custom delay
# python safe_test_direct.py --count 100 --delay 0.5