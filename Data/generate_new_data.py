# ============================================================================
# GENERATE SAMPLE NEW TRANSACTIONS CSV
# ============================================================================
import pandas as pd
import numpy as np
def generate_sample_new_transactions(n_samples=10, output_file='new_transactions.csv'):
    """
    Generate sample new transactions CSV for testing predictions
    
    Parameters:
    -----------
    n_samples : int
        Number of sample transactions to generate
    output_file : str
        Output CSV filename
    """
    np.random.seed(42)
    
    # Generate sample data matching the schema
    data = {
        'country_code': np.random.choice(['US', 'UK', 'IN', 'SG', 'AE'], n_samples),
        'phone_number': [f'{np.random.randint(1000000, 9999999)}' for _ in range(n_samples)],
        'full_phone': [f'+1-{np.random.randint(1000000, 9999999)}' for _ in range(n_samples)],
        
        # Categorical features
        'customer_vintage_bucket': np.random.choice(['0-3 months', '3-6 months', '6-12 months', '1-2 years', '2+ years'], n_samples),
        'customer_risk_rating': np.random.choice(['Low', 'Medium', 'High'], n_samples),
        'customer_segment': np.random.choice(['Retail', 'Premium', 'Corporate', 'SME'], n_samples),
        'occupation_type': np.random.choice(['Salaried', 'Self-Employed', 'Business', 'Professional', 'Student'], n_samples),
        'kyc_country': np.random.choice(['US', 'UK', 'IN', 'SG', 'AE'], n_samples),
        'kyc_city': np.random.choice(['New York', 'London', 'Mumbai', 'Singapore', 'Dubai'], n_samples),
        'geo_restriction_level': np.random.choice(['None', 'Low', 'Medium', 'High'], n_samples),
        'restricted_geo_location': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        
        # Numerical features
        'avg_monthly_txn_value': np.random.uniform(1000, 100000, n_samples),
        'kyc_update_freq': np.random.randint(0, 10, n_samples),
        'pep_highrisk_flag': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'txn_count_1h': np.random.randint(0, 20, n_samples),
        'txn_frequency_day_vs_mean': np.random.uniform(0.1, 5.0, n_samples),
        'roundamt_repetitiveness_percent': np.random.uniform(0, 100, n_samples),
        'sameday_creditreversal_count_7d': np.random.randint(0, 5, n_samples),
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"\n{'='*70}")
    print(f"Generated {n_samples} sample transactions")
    print(f"Saved to: {output_file}")
    print(f"{'='*70}")
    print("\nSample data preview:")
    print(df.head())
    print("\nColumns:", df.columns.tolist())
    
    return df
import pandas as pd
import numpy as np
import random

# -----------------------------------------
# Configuration
# -----------------------------------------
N_SAMPLES = 500  # Change to desired sample size
np.random.seed(42)
random.seed(42)

# -----------------------------------------
# Helper functions
# -----------------------------------------
def generate_customer_id(n):
    return [f"CUST{str(i).zfill(8)}" for i in range(1, n + 1)]

def generate_local_number_for_country(country, existing_locals):
    lengths = {"India": 10, "UAE": 9, "USA": 10, "Singapore": 8, "Pakistan": 10, "Iran": 10, "Myanmar": 9, "UK": 10, "Germany": 11}
    length = lengths.get(country, 9)
    while True:
        if country == "India":
            first = str(np.random.randint(6, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest
        else:
            first = str(np.random.randint(2, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest
        if local not in existing_locals:
            existing_locals.add(local)
            return local

# -----------------------------------------
# Generate unlabeled dataset (for prediction)
# -----------------------------------------
def generate_unlabeled_dataset(n=N_SAMPLES):
    data = pd.DataFrame()
    data["customer_id"] = generate_customer_id(n)

    # Random but realistic distributions (no Fraud_Label)
    data["Customer_Vintage_Bucket"] = np.random.choice(["New", "Mid", "Mature"], size=n, p=[0.2, 0.4, 0.4])
    data["customer_risk_rating"] = np.random.choice([1, 2, 3], size=n, p=[0.6, 0.3, 0.1])
    data["Avg_Monthly_Txn_Value"] = np.random.lognormal(12.3, 0.9, size=n)
    data["KYC_Update_Freq"] = np.random.choice(range(0, 10), size=n, p=[0.4,0.2,0.1,0.1,0.05,0.05,0.03,0.03,0.02,0.02])
    data["PEP_HighRisk_Flag"] = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
    data["Customer_Segment"] = np.random.choice(["Retail", "Corporate"], size=n, p=[0.9, 0.1])
    data["Occupation_Type"] = np.random.choice(["Salaried", "Self-Employed", "Student", "Retired", "Unemployed"], size=n, p=[0.5,0.3,0.1,0.07,0.03])
    data["Txn_Count_1H"] = np.random.poisson(2, size=n)
    data["Txn_Frequency_Day_vs_Mean"] = np.random.gamma(1.5, 1.0, size=n)
    data["RoundAmt_Repetitiveness_Percent"] = np.random.beta(2,3,size=n)*100
    data["SameDay_CreditReversal_Count_7D"] = np.random.poisson(0.5, size=n)

    countries = ["India","UAE","USA","Singapore","Pakistan","Iran","Myanmar","UK","Germany"]
    cities = {
        "India":["Mumbai","Delhi","Bangalore"], "UAE":["Dubai","Abu Dhabi"], "USA":["New York","San Francisco"],
        "Singapore":["Singapore"], "Pakistan":["Karachi","Lahore"], "Iran":["Tehran","Isfahan"],
        "Myanmar":["Yangon","Mandalay"], "UK":["London","Manchester"], "Germany":["Berlin","Munich"]
    }
    fatf_high_risk = ["Iran","Myanmar"]
    fatf_watchlist = ["Pakistan"]

    kyc_country, kyc_city, geo_level, restricted_flag = [], [], [], []
    for _ in range(n):
        country = np.random.choice(countries)
        city = np.random.choice(cities[country])
        if country in fatf_high_risk:
            level = "High-Risk"
        elif country in fatf_watchlist:
            level = "Watchlist"
        else:
            level = "Normal"
        restricted = 1 if level != "Normal" else 0
        kyc_country.append(country)
        kyc_city.append(city)
        geo_level.append(level)
        restricted_flag.append(restricted)

    data["KYC_Country"] = kyc_country
    data["KYC_City"] = kyc_city
    data["Geo_Restriction_Level"] = geo_level
    data["Restricted_Geo_Location"] = restricted_flag

    country_phone_codes = {"India":"+91","UAE":"+971","USA":"+1","Singapore":"+65","Pakistan":"+92","Iran":"+98","Myanmar":"+95","UK":"+44","Germany":"+49"}
    existing_local_per_country = {c:set() for c in country_phone_codes.keys()}
    country_codes, phone_local_numbers, full_phone_numbers = [], [], []

    for c in data["KYC_Country"]:
        cc = country_phone_codes[c]
        local = generate_local_number_for_country(c, existing_local_per_country[c])
        full = f"{cc}{local}"
        country_codes.append(cc)
        phone_local_numbers.append(local)
        full_phone_numbers.append(full)

    data["Country_Code"] = country_codes
    data["Phone_Number"] = phone_local_numbers
    data["Full_Phone"] = full_phone_numbers

    return data

# -----------------------------------------
# Run generator
# -----------------------------------------
df_new = generate_unlabeled_dataset()
df_new.to_csv(r"E:\VS code stuff\Dataset Generation\Data\banking_cust_dataset_unlabeled.csv", index=False)
print("✓ Unlabeled dataset saved successfully!")

# generate_sample_new_transactions(1,r"E:\VS code stuff\Dataset Generation\Data\new_transactions.csv")
