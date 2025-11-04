# =============================================================
# Banking–Telecom Fraud Detection Dataset Generator
# Synthetic Dataset for Hackathon (10K Records)
# Enhanced with Telecom Features
# =============================================================

import pandas as pd
import numpy as np
import random

# -----------------------------------------
# Configuration
# -----------------------------------------
N_SAMPLES = 10000
FRAUD_RATE = 0.09  # 9% fraud cases
np.random.seed(42)
random.seed(42)

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def generate_customer_id(n):
    """Generate unique customer IDs"""
    return [f"CUST{str(i).zfill(8)}" for i in range(1, n + 1)]

def generate_local_number_for_country(country, existing_locals):
    """
    Generate a plausible local phone number (string of digits) for a given country.
    existing_locals is a set to enforce uniqueness per country code+local combination.
    This is synthetic and not guaranteed to match exact national numbering plans, but realistic enough.
    """
    # lengths chosen for plausibility
    lengths = {
        "India": 10,
        "UAE": 9,
        "USA": 10,
        "Singapore": 8,
        "Pakistan": 10,
        "Iran": 10,
        "Myanmar": 9,
        "UK": 10,
        "Germany": 11
    }
    length = lengths.get(country, 9)
    # try until unique local number for this country
    while True:
        if country == "India":
            # start with 6-9 for Indian mobiles
            first = str(np.random.randint(6, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest
        else:
            # other countries: random digits, avoid leading zero
            first = str(np.random.randint(2, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest

        if local not in existing_locals:
            existing_locals.add(local)
            return local

# -----------------------------------------
# Telecom Feature Generation Functions
# -----------------------------------------
def generate_sim_swap_freq(is_fraud):
    """Generate SIM swap frequency - fraudsters often swap SIMs"""
    if is_fraud:
        # Fraud cases: higher SIM swap activity
        return np.random.choice(
            range(0, 8),
            p=[0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.03, 0.02]
        )
    else:
        # Normal cases: rarely swap SIMs
        return np.random.choice(
            range(0, 5),
            p=[0.85, 0.10, 0.03, 0.015, 0.005]
        )

def generate_days_since_sim_swap(sim_swap_freq):
    """Generate days since last SIM swap"""
    if sim_swap_freq == 0:
        # Never swapped - return high value or null indicator
        return np.random.randint(180, 730)
    elif sim_swap_freq >= 3:
        # Frequent swappers - recent swap
        return np.random.randint(1, 15)
    else:
        # Occasional swappers
        return np.random.randint(15, 120)

def generate_device_online_pct(is_fraud, occupation):
    """Generate device online percentage"""
    if is_fraud:
        # Fraudsters: irregular patterns, sometimes offline to avoid detection
        if np.random.rand() < 0.3:
            return round(np.random.uniform(20, 50), 2)  # Suspicious low activity
        else:
            return round(np.random.uniform(60, 95), 2)
    else:
        # Normal users: consistent online presence
        if occupation in ['Salaried', 'Self-Employed']:
            return round(np.random.uniform(75, 98), 2)
        elif occupation == 'Student':
            return round(np.random.uniform(80, 99), 2)
        else:
            return round(np.random.uniform(60, 90), 2)

def generate_roaming_days(is_fraud, geo_restriction):
    """Generate roaming days"""
    if is_fraud and geo_restriction == 1:
        # Cross-border fraud operations
        probs = np.array([0.10] + [0.05]*5 + [0.08]*10 + [0.025]*9)
        probs = probs / probs.sum()  # Normalize to sum to 1
        return np.random.choice(range(0, 25), p=probs)
    elif is_fraud:
        return np.random.randint(0, 10)
    else:
        # Normal users: occasional travel
        probs = np.array([0.60, 0.15, 0.10, 0.05, 0.03, 0.02, 0.015, 0.01] + [0.005]*7)
        probs = probs / probs.sum()  # Normalize to sum to 1
        return np.random.choice(range(0, 15), p=probs)

def generate_unique_locations(is_fraud, roaming_days):
    """Generate unique location count"""
    if is_fraud:
        # Fraudsters: either very mobile or stationary
        if roaming_days > 10:
            return np.random.randint(8, 30)  # High mobility
        else:
            return np.random.randint(1, 8)   # Hiding in one location
    else:
        # Normal users: moderate mobility
        base = min(3 + roaming_days, 15)
        return max(1, np.random.randint(base - 2, base + 3))

def generate_daily_distance(unique_locations, roaming_days, is_fraud):
    """Generate average daily distance traveled"""
    if is_fraud and roaming_days > 10:
        # Fraudsters traveling cross-border
        return round(np.random.uniform(50, 300), 2)
    elif unique_locations > 10:
        # High mobility users
        return round(np.random.uniform(20, 100), 2)
    else:
        # Normal commute patterns
        return round(np.random.uniform(5, 40), 2)

def generate_number_change_freq(sim_swap_freq_30d, is_fraud):
    """Generate number change frequency in 90 days"""
    if is_fraud:
        # Fraud: multiple number changes to evade detection
        base = sim_swap_freq_30d * 2
        return min(base + np.random.randint(0, 4), 15)
    else:
        # Normal: rarely change numbers
        return np.random.choice(
            range(0, 5),
            p=[0.90, 0.06, 0.02, 0.015, 0.005]
        )

def generate_sms_connectivity(device_online_pct, is_fraud):
    """Generate SMS connectivity ratio"""
    if is_fraud and np.random.rand() < 0.25:
        # Some fraudsters avoid SMS to prevent OTP verification
        return round(np.random.uniform(0.3, 0.7), 3)
    else:
        # Normal: high SMS connectivity
        base = device_online_pct / 100
        noise = np.random.uniform(-0.1, 0.05)
        return round(min(1.0, max(0.0, base + noise)), 3)

def generate_offline_streak(device_online_pct, is_fraud):
    """Generate maximum offline streak"""
    if is_fraud and np.random.rand() < 0.35:
        # Fraudsters sometimes go dark
        return np.random.randint(5, 20)
    elif device_online_pct < 50:
        return np.random.randint(3, 15)
    elif device_online_pct > 90:
        return np.random.randint(0, 3)
    else:
        return np.random.randint(1, 7)

def generate_high_risk_location_flag(kyc_country, geo_restriction, roaming_days, is_fraud):
    """Generate high-risk location flag"""
    high_risk_countries = ['Iran', 'Myanmar', 'Pakistan']
    
    if kyc_country in high_risk_countries:
        return 1
    elif geo_restriction == 1:
        return 1
    elif is_fraud and roaming_days > 15:
        # Fraudster moving through risky areas
        return 1 if np.random.rand() < 0.4 else 0
    elif roaming_days > 20:
        return 1 if np.random.rand() < 0.15 else 0
    else:
        return 0

# -----------------------------------------
# Core Dataset Generation
# -----------------------------------------
def generate_dataset():
    n = N_SAMPLES
    data = pd.DataFrame()

    # === Identifiers ===
    data['customer_id'] = generate_customer_id(n)

    # === Fraud Label ===
    n_fraud = int(n * FRAUD_RATE)
    labels = np.array([1] * n_fraud + [0] * (n - n_fraud))
    np.random.shuffle(labels)
    data['Fraud_Label'] = labels

    # === Customer Vintage Bucket ===
    data['Customer_Vintage_Bucket'] = [
        np.random.choice(['New', 'Mid', 'Mature'],
                         p=[0.35, 0.40, 0.25] if f == 1 else [0.18, 0.28, 0.54])
        for f in labels
    ]

    # === Customer Risk Rating ===
    data['customer_risk_rating'] = np.random.choice([1, 2, 3], size=n, p=[0.60, 0.30, 0.10])

    # === Avg Monthly Transaction Value ===
    avg_txn_values = []
    for f in labels:
        if f == 1:
            if np.random.rand() < 0.4:
                value = np.random.uniform(5e6, 1e7)
            else:
                value = np.random.lognormal(13, 1.5)
        else:
            value = np.random.lognormal(12.2, 0.8)
        avg_txn_values.append(min(value, 1e7))
    data['Avg_Monthly_Txn_Value'] = avg_txn_values

    # === KYC Update Frequency ===
    kyc_freq = []
    for f in labels:
        if f == 1:
            freq = np.random.choice([0,1,2,3,4,5,6,7,8,9,10,15,20,25],
                                    p=[0.15,0.10,0.10,0.12,0.10,0.08,0.07,0.06,0.05,0.04,0.04,0.04,0.03,0.02])
        else:
            p = np.array([0.88,0.05,0.03,0.015,0.01,0.005,0.003,0.002,0.001,0.001,0.002])
            p /= p.sum()
            freq = np.random.choice([0,1,2,3,4,5,6,7,8,9,10], p=p)
        kyc_freq.append(freq)
    data['KYC_Update_Freq'] = kyc_freq

    # === PEP / High-Risk Flag ===
    data['PEP_HighRisk_Flag'] = [
        np.random.choice([0, 1], p=[0.70, 0.30]) if f == 1 else np.random.choice([0, 1], p=[0.97, 0.03])
        for f in labels
    ]

    # === Customer Segment ===
    data['Customer_Segment'] = np.random.choice(['Retail', 'Corporate'], size=n, p=[0.90, 0.10])

    # === Occupation Type ===
    data['Occupation_Type'] = np.random.choice(
        ['Salaried', 'Self-Employed', 'Student', 'Retired', 'Unemployed'],
        size=n, p=[0.50, 0.30, 0.10, 0.07, 0.03]
    )

    # === Txn Count (1 Hour Window) ===
    txn_counts = []
    for f in labels:
        if f == 1:
            probs = np.array([0.10] + [0.015]*10 + [0.025]*10 + [0.035]*20 + [0.020]*9)
            probs /= probs.sum()
            txn_counts.append(np.random.choice(range(0,50), p=probs))
        else:
            probs = np.array([0.50,0.20,0.12,0.08,0.05] + [0.01]*10 + [0.002]*15)
            probs /= probs.sum()
            txn_counts.append(np.random.choice(range(0,30), p=probs))
    data['Txn_Count_1H'] = txn_counts

    # === Txn Frequency vs Mean ===
    data['Txn_Frequency_Day_vs_Mean'] = [
        min(np.random.gamma(2,1.5),10) if f == 1 else min(np.random.gamma(1.2,0.5),10)
        for f in labels
    ]

    # === Round Amount Repetitiveness ===
    data['RoundAmt_Repetitiveness_Percent'] = [
        np.random.beta(3,2)*100 if f == 1 else np.random.beta(1.5,4)*100
        for f in labels
    ]

    # === Same Day Credit Reversal (7D) ===
    data['SameDay_CreditReversal_Count_7D'] = [
        np.random.choice(range(0,8),
                         p=[0.30,0.20,0.15,0.12,0.10,0.08,0.03,0.02]) if f == 1
        else np.random.choice(range(0,8),
                              p=[0.92,0.04,0.02,0.01,0.005,0.003,0.001,0.001])
        for f in labels
    ]

    # === Geography / FATF-based Risk ===
    countries = ['India','UAE','USA','Singapore','Pakistan','Iran','Myanmar','UK','Germany']
    cities = {
        'India':['Mumbai','Delhi','Bangalore','Chennai','Kolkata','Hyderabad'],
        'UAE':['Dubai','Abu Dhabi','Sharjah'],
        'USA':['New York','San Francisco','Chicago','Los Angeles'],
        'Singapore':['Singapore'],
        'Pakistan':['Karachi','Lahore','Islamabad'],
        'Iran':['Tehran','Mashhad','Isfahan'],
        'Myanmar':['Yangon','Mandalay','Naypyidaw'],
        'UK':['London','Manchester','Birmingham'],
        'Germany':['Berlin','Munich','Frankfurt']
    }
    fatf_high_risk = ['Iran','North Korea','Myanmar']
    fatf_watchlist = ['Pakistan','Syria','Yemen','Turkey']

    kyc_country, kyc_city, geo_level, restricted_flag = [], [], [], []
    for f in labels:
        if f == 1:
            country = np.random.choice(['India','Pakistan','Iran','Myanmar','UAE'],
                                       p=[0.45,0.20,0.15,0.10,0.10])
        else:
            country = np.random.choice(['India','UAE','USA','UK','Germany','Singapore'],
                                       p=[0.55,0.15,0.10,0.10,0.05,0.05])
        city = np.random.choice(cities[country])
        if country in fatf_high_risk:
            level = 'High-Risk'
        elif country in fatf_watchlist:
            level = 'Watchlist'
        else:
            level = 'Watchlist' if np.random.rand() < 0.01 else 'Normal'
        restricted = 1 if level != 'Normal' else 0

        kyc_country.append(country)
        kyc_city.append(city)
        geo_level.append(level)
        restricted_flag.append(restricted)

    data['KYC_Country'] = kyc_country
    data['KYC_City'] = kyc_city
    data['Geo_Restriction_Level'] = geo_level
    data['Restricted_Geo_Location'] = restricted_flag

    # === Country Code and Local Phone Number ===
    country_phone_codes = {
        "India": "+91",
        "UAE": "+971",
        "USA": "+1",
        "Singapore": "+65",
        "Pakistan": "+92",
        "Iran": "+98",
        "Myanmar": "+95",
        "UK": "+44",
        "Germany": "+49"
    }

    existing_local_per_country = {c: set() for c in country_phone_codes.keys()}

    country_codes = []
    phone_local_numbers = []
    full_phone_numbers = []

    for c in data['KYC_Country']:
        cc = country_phone_codes.get(c, "+91")
        local = generate_local_number_for_country(c, existing_local_per_country.setdefault(c, set()))
        full = f"{cc}{local}"
        country_codes.append(cc)
        phone_local_numbers.append(local)
        full_phone_numbers.append(full)

    data['Country_Code'] = country_codes
    data['Phone_Number'] = phone_local_numbers
    data['Full_Phone'] = full_phone_numbers

    # ==============================================
    # === TELECOM FEATURES (NEW) ===
    # ==============================================
    
    # 1. SIM Swap Frequency (30 days)
    data['sim_swap_freq_30d'] = [generate_sim_swap_freq(f) for f in labels]
    
    # 2. Days Since Last SIM Swap
    data['days_since_last_sim_swap'] = [
        generate_days_since_sim_swap(freq) for freq in data['sim_swap_freq_30d']
    ]
    
    # 3. Average Device Online Percentage
    data['avg_device_online_pct'] = [
        generate_device_online_pct(f, occ) 
        for f, occ in zip(labels, data['Occupation_Type'])
    ]
    
    # 4. Roaming Days (30 days)
    data['roaming_days_30d'] = [
        generate_roaming_days(f, geo) 
        for f, geo in zip(labels, data['Restricted_Geo_Location'])
    ]
    
    # 5. Unique Location Count (30 days)
    data['unique_location_count_30d'] = [
        generate_unique_locations(f, rd) 
        for f, rd in zip(labels, data['roaming_days_30d'])
    ]
    
    # 6. Average Daily Distance (km)
    data['avg_daily_distance_km'] = [
        generate_daily_distance(ul, rd, f)
        for ul, rd, f in zip(data['unique_location_count_30d'], data['roaming_days_30d'], labels)
    ]
    
    # 7. Number Change Frequency (90 days)
    data['number_change_freq_90d'] = [
        generate_number_change_freq(ss, f)
        for ss, f in zip(data['sim_swap_freq_30d'], labels)
    ]
    
    # 8. SMS Connectivity Ratio
    data['sms_connectivity_ratio'] = [
        generate_sms_connectivity(do, f)
        for do, f in zip(data['avg_device_online_pct'], labels)
    ]
    
    # 9. Device Offline Streak (max consecutive days)
    data['device_offline_streak_max'] = [
        generate_offline_streak(do, f)
        for do, f in zip(data['avg_device_online_pct'], labels)
    ]
    
    # 10. High Risk Location Flag
    data['high_risk_location_flag'] = [
        generate_high_risk_location_flag(kyc, geo, rd, f)
        for kyc, geo, rd, f in zip(
            data['KYC_Country'], 
            data['Restricted_Geo_Location'], 
            data['roaming_days_30d'], 
            labels
        )
    ]

    # === Rounding Numeric Features ===
    data['Avg_Monthly_Txn_Value'] = [round(v, 2) for v in data['Avg_Monthly_Txn_Value']]
    data['Txn_Frequency_Day_vs_Mean'] = [round(v, 2) for v in data['Txn_Frequency_Day_vs_Mean']]
    data['RoundAmt_Repetitiveness_Percent'] = [round(v, 1) for v in data['RoundAmt_Repetitiveness_Percent']]
    data['Txn_Count_1H'] = [int(v) for v in data['Txn_Count_1H']]
    data['SameDay_CreditReversal_Count_7D'] = [int(v) for v in data['SameDay_CreditReversal_Count_7D']]
    data['KYC_Update_Freq'] = [int(v) for v in data['KYC_Update_Freq']]

    # === Final Column Order ===
    column_order = [
        'customer_id', 'Country_Code', 'Phone_Number', 'Full_Phone', 'Fraud_Label',
        'Customer_Vintage_Bucket', 'customer_risk_rating', 'Customer_Segment', 'Occupation_Type',
        'Avg_Monthly_Txn_Value', 'KYC_Update_Freq', 'PEP_HighRisk_Flag',
        'Txn_Count_1H', 'Txn_Frequency_Day_vs_Mean', 'RoundAmt_Repetitiveness_Percent',
        'SameDay_CreditReversal_Count_7D',
        'KYC_Country', 'KYC_City', 'Geo_Restriction_Level', 'Restricted_Geo_Location',
        # Telecom features
        'sim_swap_freq_30d', 'days_since_last_sim_swap', 'avg_device_online_pct',
        'roaming_days_30d', 'unique_location_count_30d', 'avg_daily_distance_km',
        'number_change_freq_90d', 'sms_connectivity_ratio', 'device_offline_streak_max',
        'high_risk_location_flag'
    ]

    return data[column_order]

# -----------------------------------------
# Generate Dataset
# -----------------------------------------
print("Generating enhanced banking-telecom fraud dataset...")
df = generate_dataset()
print("✓ Dataset generated successfully!")

# Save to CSV
df.to_csv(r"E:\VS code stuff\Dataset Generation\banking_cust_dataset.csv", index=False)
print(f"✓ Saved to: E:\\VS code stuff\\Dataset Generation\\banking_cust_dataset.csv")

# Quick checks
print(f"\nTotal Records: {len(df)}")
print(f"Fraud Cases: {df['Fraud_Label'].sum()} ({df['Fraud_Label'].mean()*100:.2f}%)")
print("\n=== Telecom Features Summary ===")
print(f"Avg SIM Swaps (Fraud): {df[df['Fraud_Label']==1]['sim_swap_freq_30d'].mean():.2f}")
print(f"Avg SIM Swaps (Normal): {df[df['Fraud_Label']==0]['sim_swap_freq_30d'].mean():.2f}")
print(f"Avg Roaming Days (Fraud): {df[df['Fraud_Label']==1]['roaming_days_30d'].mean():.2f}")
print(f"Avg Roaming Days (Normal): {df[df['Fraud_Label']==0]['roaming_days_30d'].mean():.2f}")
print(f"High Risk Location (Fraud): {df[df['Fraud_Label']==1]['high_risk_location_flag'].mean()*100:.1f}%")
print(f"High Risk Location (Normal): {df[df['Fraud_Label']==0]['high_risk_location_flag'].mean()*100:.1f}%")

print("\nSample rows:")
print(df.head(3).to_string(index=False))