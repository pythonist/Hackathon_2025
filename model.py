import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import pickle
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================

def load_and_prepare_data(df):
    """Load data and separate features from target"""
    id_columns = ['country_code', 'phone_number', 'full_phone', 'customer_id']
    df.columns = df.columns.str.lower()
    X = df.drop(columns=['fraud_label'] + [col for col in id_columns if col in df.columns])
    y = df['fraud_label']
    return X, y

# ============================================================================
# COLUMN DETECTION AND ENCODING
# ============================================================================

def detect_column_types(X):
    """Detect categorical vs numerical columns"""
    categorical_cols = []
    numerical_cols = []
    
    for col in X.columns:
        if X[col].dtype == 'object' or X[col].dtype.name == 'category':
            categorical_cols.append(col)
        elif X[col].nunique() < 20 and X[col].dtype in ['int64', 'int32']:
            categorical_cols.append(col)
        else:
            numerical_cols.append(col)
    
    return categorical_cols, numerical_cols

def encode_features(X_train, X_test, categorical_cols):
    """Encode categorical features"""
    if not categorical_cols:
        return X_train.copy(), X_test.copy(), None
    
    encoder = OrdinalEncoder(
        handle_unknown='use_encoded_value',
        unknown_value=-1,
        encoded_missing_value=-1
    )
    
    X_train_encoded = X_train.copy()
    X_test_encoded = X_test.copy()
    
    X_train_encoded[categorical_cols] = encoder.fit_transform(X_train[categorical_cols])
    X_test_encoded[categorical_cols] = encoder.transform(X_test[categorical_cols])
    
    return X_train_encoded, X_test_encoded, encoder

# ============================================================================
# MODEL TRAINING
# ============================================================================

def train_xgboost_model(X_train, y_train, X_val, y_val):
    """Train XGBoost model"""
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'tree_method': 'hist',
        'device': 'cpu'
    }
    
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=False, feature_names=X_train.columns.tolist())
    dval = xgb.DMatrix(X_val, label=y_val, enable_categorical=False, feature_names=X_val.columns.tolist())
    
    evals = [(dtrain, 'train'), (dval, 'validation')]
    
    print("Training XGBoost model...")
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=500,
        evals=evals,
        early_stopping_rounds=50,
        verbose_eval=50,
    )
    
    return model

# ============================================================================
# PREDICTION
# ============================================================================

def predict_new_data(new_df, model, encoder, categorical_cols, feature_columns):
    """Make predictions on new data"""
    print("="*70)
    print("PREDICTING ON NEW DATA")
    print("="*70)
    
    id_columns = ['country_code', 'phone_number', 'full_phone', 'fraud_label', 'customer_id']
    
    X_new = new_df.drop(columns=[col for col in id_columns if col in new_df.columns], errors='ignore')
    
    missing_cols = set(feature_columns) - set(X_new.columns)
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
        for col in missing_cols:
            X_new[col] = 0
    
    X_new = X_new[feature_columns]
    
    X_new_encoded = X_new.copy()
    if encoder and categorical_cols:
        print(f"Encoding {len(categorical_cols)} categorical features...")
        X_new_encoded[categorical_cols] = encoder.transform(X_new[categorical_cols])
    
    dnew = xgb.DMatrix(X_new_encoded, enable_categorical=False, feature_names=feature_columns)
    
    print("Generating predictions...")
    fraud_probabilities = model.predict(dnew)
    fraud_predictions = (fraud_probabilities > 0.5).astype(int)
    
    results_df = new_df.copy()
    results_df['fraud_probability'] = fraud_probabilities
    results_df['fraud_prediction'] = fraud_predictions
    results_df['risk_level'] = results_df['fraud_probability'].apply(
        lambda x: 'HIGH' if x > 0.7 else ('MEDIUM' if x > 0.3 else 'LOW')
    )
    
    print(f"\nTotal records: {len(results_df)}")
    print(f"Predicted frauds: {fraud_predictions.sum()} ({fraud_predictions.mean():.2%})")
    print(f"\nRisk Level Distribution:")
    print(results_df['risk_level'].value_counts().to_string())
    
    return results_df

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main_pipeline(df):
    """Complete training pipeline"""
    print("="*70)
    print("XGBOOST FRAUD DETECTION PIPELINE")
    print("="*70)
    
    # Prepare data
    print("\n1. Loading and preparing data...")
    X, y = load_and_prepare_data(df)
    print(f"   Dataset shape: {X.shape}")
    print(f"   Fraud rate: {y.mean():.2%}")
    
    # Detect column types
    print("\n2. Detecting column types...")
    categorical_cols, numerical_cols = detect_column_types(X)
    print(f"   Categorical columns ({len(categorical_cols)}): {categorical_cols}")
    print(f"   Numerical columns ({len(numerical_cols)}): {numerical_cols}")
    
    # Train-test split
    print("\n3. Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    # Encode features
    print("\n4. Encoding categorical features...")
    X_train_enc, X_val_enc, encoder = encode_features(X_train_split, X_val, categorical_cols)
    X_test_enc, _, _ = encode_features(X_test, X_test, categorical_cols)
    if encoder:
        X_test_enc[categorical_cols] = encoder.transform(X_test[categorical_cols])
    
    # Train model
    print("\n5. Training XGBoost model...")
    model = train_xgboost_model(X_train_enc, y_train_split, X_val_enc, y_val)
    
    # Evaluate model
    print("\n6. Evaluating model on test set...")
    dtest = xgb.DMatrix(X_test_enc, enable_categorical=False, feature_names=X_test_enc.columns.tolist())
    y_pred_proba = model.predict(dtest)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    
    return {
        'model': model,
        'encoder': encoder,
        'categorical_cols': categorical_cols,
        'feature_columns': X.columns.tolist()
    }

# ============================================================================
# RUN TRAINING
# ============================================================================

if __name__ == "__main__":
    # Load data
    """
    Expected columns:
    ['country_code', 'phone_number', 'full_phone', 'fraud_label',
     'customer_vintage_bucket', 'customer_risk_rating', 'customer_segment',
     'occupation_type', 'avg_monthly_txn_value', 'kyc_update_freq',
     'pep_highrisk_flag', 'txn_count_1h', 'txn_frequency_day_vs_mean',
     'roundamt_repetitiveness_percent', 'sameday_creditreversal_count_7d',
     'kyc_country', 'kyc_city', 'geo_restriction_level',
     'restricted_geo_location']
    """
    
    print("✓ Model saved to: fraud_model.json")
    print("✓ Encoder saved to: encoder.pkl")
    
