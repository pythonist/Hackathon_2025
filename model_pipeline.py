import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import shap
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. DATA LOADING AND PREPROCESSING
# ============================================================================

def load_and_prepare_data(df):
    """
    Load data and separate features from target
    """
    # Remove identifier columns that shouldn't be used for training
    id_columns = ['country_code', 'phone_number', 'full_phone']
    df.columns = df.columns.str.lower()
    # Separate target and features
    X = df.drop(columns=['fraud_label'] + [col for col in id_columns if col in df.columns])
    y = df['fraud_label']
    
    return X, y

# ============================================================================
# 2. INTELLIGENT COLUMN DETECTION AND ENCODING
# ============================================================================

def detect_column_types(X):
    """
    Automatically detect categorical vs numerical columns
    """
    categorical_cols = []
    numerical_cols = []
    
    for col in X.columns:
        # Check if column is object/string type or has few unique values
        if X[col].dtype == 'object' or X[col].dtype.name == 'category':
            categorical_cols.append(col)
        elif X[col].nunique() < 20 and X[col].dtype in ['int64', 'int32']:
            # Likely categorical (e.g., flags, small integer codes)
            categorical_cols.append(col)
        else:
            numerical_cols.append(col)
    
    return categorical_cols, numerical_cols

def encode_features(X_train, X_test, categorical_cols):
    """
    Encode categorical features using OrdinalEncoder
    Handles unknown categories gracefully
    """
    if not categorical_cols:
        return X_train.copy(), X_test.copy(), None
    
    # Initialize encoder with unknown value handling
    encoder = OrdinalEncoder(
        handle_unknown='use_encoded_value',
        unknown_value=-1,
        encoded_missing_value=-1
    )
    
    # Fit on training data
    X_train_encoded = X_train.copy()
    X_test_encoded = X_test.copy()
    
    # Encode categorical columns
    X_train_encoded[categorical_cols] = encoder.fit_transform(X_train[categorical_cols])
    X_test_encoded[categorical_cols] = encoder.transform(X_test[categorical_cols])
    
    return X_train_encoded, X_test_encoded, encoder

# ============================================================================
# 3. MODEL TRAINING WITH XGBOOST 3.1.1
# ============================================================================

def train_xgboost_model(X_train, y_train, X_val, y_val):
    """
    Train XGBoost model with optimized hyperparameters for fraud detection
    """
    # Calculate scale_pos_weight for imbalanced data
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    # XGBoost parameters optimized for fraud detection
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
        'tree_method': 'hist',  # Fast histogram-based algorithm
        'device': 'cpu'  # Compatible with XGBoost 3.1.1
    }
    
    # Create DMatrix for XGBoost with feature names
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=False, feature_names=X_train.columns.tolist())
    dval = xgb.DMatrix(X_val, label=y_val, enable_categorical=False, feature_names=X_val.columns.tolist())
    
    # Training with early stopping
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
# 4. FEATURE IMPORTANCE ANALYSIS
# ============================================================================

def plot_feature_importance(model, feature_names, top_n=15):
    """
    Plot top N most important features
    """
    # Get feature importance
    importance_dict = model.get_score(importance_type='gain')
    
    # Map feature indices/names to actual feature names
    importance_df = pd.DataFrame([
        {
            'feature': feature_names[int(k.replace('f', ''))] if k.startswith('f') and k[1:].isdigit() else k,
            'importance': v
        }
        for k, v in importance_dict.items()
    ])
    
    # Sort and get top N
    importance_df = importance_df.sort_values('importance', ascending=False).head(top_n)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(importance_df)), importance_df['importance'].values)
    plt.yticks(range(len(importance_df)), importance_df['feature'].values)
    plt.xlabel('Feature Importance (Gain)')
    plt.title(f'Top {top_n} Most Important Features')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()
    
    return importance_df

# ============================================================================
# 5. SHAP EXPLAINABILITY
# ============================================================================

def explain_with_shap(model, X_sample, feature_names, sample_size=100):
    """
    Generate SHAP explanations for model predictions
    Compatible with XGBoost 3.x
    """
    # Sample data for SHAP (SHAP can be slow on large datasets)
    if len(X_sample) > sample_size:
        X_shap = X_sample.sample(n=sample_size, random_state=42)
    else:
        X_shap = X_sample
    
    # Create SHAP explainer using data instead of model directly (XGBoost 3.x compatibility)
    print("\nGenerating SHAP explanations...")
    try:
        # Try direct method first
        explainer = shap.TreeExplainer(model, X_shap)
        shap_values = explainer(X_shap)
        shap_values_array = shap_values.values
    except (ValueError, AttributeError) as e:
        print(f"Note: Using alternative SHAP method due to XGBoost 3.x compatibility")
        # Fallback: Use model predictions to estimate SHAP values
        explainer = shap.Explainer(
            lambda x: model.predict(xgb.DMatrix(x, enable_categorical=False, feature_names=feature_names)),
            X_shap
        )
        shap_values = explainer(X_shap)
        shap_values_array = shap_values.values
    
    # Summary plot - shows feature importance across all samples
    print("\nSHAP Summary Plot (Global Feature Importance):")
    shap.summary_plot(shap_values_array, X_shap, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.show()
    
    return explainer, shap_values

def explain_single_prediction(model, explainer, X_sample, feature_names, customer_idx=0):
    """
    Explain why a specific customer has high/low fraud risk
    Compatible with XGBoost 3.x
    """
    # Get single customer data
    customer_data = X_sample.iloc[[customer_idx]]
    dmatrix = xgb.DMatrix(customer_data, enable_categorical=False, feature_names=feature_names)
    
    # Get prediction
    fraud_prob = model.predict(dmatrix)[0]
    
    # Get SHAP values for this customer
    try:
        shap_values_single = explainer(customer_data)
        shap_vals = shap_values_single.values[0]
        base_value = shap_values_single.base_values[0] if hasattr(shap_values_single.base_values, '__iter__') else shap_values_single.base_values
    except:
        # Fallback if explainer format is different
        shap_vals = explainer.shap_values(customer_data)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        base_value = explainer.expected_value if hasattr(explainer, 'expected_value') else 0.5
    
    print(f"\n{'='*70}")
    print(f"CUSTOMER RISK EXPLANATION (Customer Index: {customer_idx})")
    print(f"{'='*70}")
    print(f"Fraud Probability: {fraud_prob:.2%}")
    print(f"Risk Level: {'HIGH RISK' if fraud_prob > 0.5 else 'LOW RISK'}")
    print(f"\n{'='*70}")
    
    # Create feature contribution summary
    contribution_df = pd.DataFrame({
        'Feature': feature_names,
        'Value': customer_data.values[0],
        'SHAP_Value': shap_vals
    })
    contribution_df = contribution_df.reindex(
        contribution_df['SHAP_Value'].abs().sort_values(ascending=False).index
    )
    
    print("\nTop 10 Features Contributing to Risk Score:")
    print(contribution_df.head(10).to_string(index=False))
    
    # Waterfall plot - shows how each feature contributes to this prediction
    try:
        print("\nSHAP Waterfall Plot (Individual Prediction Explanation):")
        shap.plots.waterfall(
            shap.Explanation(
                values=shap_vals,
                base_values=base_value,
                data=customer_data.values[0],
                feature_names=feature_names
            ),
            show=False
        )
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Waterfall plot not available: {e}")
    
    # Force plot - alternative visualization
    try:
        print("\nSHAP Force Plot:")
        shap.force_plot(
            base_value,
            shap_vals,
            customer_data.values[0],
            feature_names=feature_names,
            matplotlib=True,
            show=False
        )
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Force plot not available: {e}")
    
    return fraud_prob

# ============================================================================
# 6. PREDICTION ON NEW DATA
# ============================================================================

def predict_single_transaction(transaction_dict, model, encoder, categorical_cols, feature_columns):
    """
    Predict fraud probability for a SINGLE transaction
    
    Parameters:
    -----------
    transaction_dict : dict
        Single transaction as dictionary with feature names as keys
        Example: {
            'customer_vintage_bucket': '6-12 months',
            'txn_count_1h': 5,
            'avg_monthly_txn_value': 25000,
            ...
        }
    model : xgboost.Booster
        Trained XGBoost model
    encoder : OrdinalEncoder
        Fitted encoder from training
    categorical_cols : list
        List of categorical column names
    feature_columns : list
        List of feature column names
    
    Returns:
    --------
    result : dict
        Prediction results with probability, prediction, and risk level
    """
    print("="*70)
    print("PREDICTING SINGLE TRANSACTION")
    print("="*70)
    
    # Convert to DataFrame
    transaction_df = pd.DataFrame([transaction_dict])
    
    # Use the main prediction function
    results_df = predict_new_data(transaction_df, model, encoder, categorical_cols, feature_columns)
    
    # Extract single result
    result = {
        'fraud_probability': results_df['fraud_probability'].iloc[0],
        'fraud_prediction': results_df['fraud_prediction'].iloc[0],
        'risk_level': results_df['risk_level'].iloc[0],
        'transaction_data': transaction_dict
    }
    
    print(f"\n{'='*70}")
    print("SINGLE TRANSACTION RESULT")
    print(f"{'='*70}")
    print(f"Fraud Probability: {result['fraud_probability']:.2%}")
    print(f"Prediction: {'FRAUD' if result['fraud_prediction'] == 1 else 'LEGITIMATE'}")
    print(f"Risk Level: {result['risk_level']}")
    
    return result

def predict_new_data(new_df, model, encoder, categorical_cols, feature_columns):
    """
    Make predictions on new data
    
    Parameters:
    -----------
    new_df : DataFrame
        New data to predict (should have same columns as training data)
    model : xgboost.Booster
        Trained XGBoost model
    encoder : OrdinalEncoder
        Fitted encoder from training
    categorical_cols : list
        List of categorical column names
    feature_columns : list
        List of feature column names (same order as training)
    
    Returns:
    --------
    predictions_df : DataFrame
        Original data with predictions added
    """
    print("="*70)
    print("PREDICTING ON NEW DATA")
    print("="*70)
    
    # Remove identifier columns if present
    id_columns = ['country_code', 'phone_number', 'full_phone', 'fraud_label']
    
    # Keep identifiers for output
    identifiers = {}
    for col in id_columns:
        if col in new_df.columns:
            identifiers[col] = new_df[col].copy()
    
    # Prepare features
    X_new = new_df.drop(columns=[col for col in id_columns if col in new_df.columns], errors='ignore')
    
    # Ensure columns match training data
    missing_cols = set(feature_columns) - set(X_new.columns)
    if missing_cols:
        print(f"Warning: Missing columns in new data: {missing_cols}")
        for col in missing_cols:
            X_new[col] = 0  # Add missing columns with default value
    
    # Reorder columns to match training
    X_new = X_new[feature_columns]
    
    # Encode categorical features
    X_new_encoded = X_new.copy()
    if encoder and categorical_cols:
        print(f"Encoding {len(categorical_cols)} categorical features...")
        X_new_encoded[categorical_cols] = encoder.transform(X_new[categorical_cols])
    
    # Create DMatrix
    dnew = xgb.DMatrix(X_new_encoded, enable_categorical=False, feature_names=feature_columns)
    
    # Make predictions
    print("Generating predictions...")
    fraud_probabilities = model.predict(dnew)
    fraud_predictions = (fraud_probabilities > 0.5).astype(int)
    
    # Create results dataframe
    results_df = new_df.copy()
    results_df['fraud_probability'] = fraud_probabilities
    results_df['fraud_prediction'] = fraud_predictions
    results_df['risk_level'] = results_df['fraud_probability'].apply(
        lambda x: 'HIGH' if x > 0.7 else ('MEDIUM' if x > 0.3 else 'LOW')
    )
    
    # Summary statistics
    print(f"\n{'='*70}")
    print("PREDICTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total records: {len(results_df)}")
    print(f"Predicted frauds: {fraud_predictions.sum()} ({fraud_predictions.mean():.2%})")
    print(f"\nRisk Level Distribution:")
    print(results_df['risk_level'].value_counts().to_string())
    print(f"\nAverage fraud probability: {fraud_probabilities.mean():.4f}")
    print(f"Max fraud probability: {fraud_probabilities.max():.4f}")
    print(f"Min fraud probability: {fraud_probabilities.min():.4f}")
    
    return results_df

def predict_and_explain(new_df, model, encoder, explainer, categorical_cols, feature_columns, top_n=5):
    """
    Predict on new data and explain high-risk cases
    
    Parameters:
    -----------
    new_df : DataFrame
        New data to predict
    model : xgboost.Booster
        Trained model
    encoder : OrdinalEncoder
        Fitted encoder
    explainer : shap.Explainer
        Fitted SHAP explainer
    categorical_cols : list
        Categorical columns
    feature_columns : list
        Feature columns
    top_n : int
        Number of highest-risk cases to explain
    
    Returns:
    --------
    results_df : DataFrame
        Predictions with explanations
    """
    # Get predictions
    results_df = predict_new_data(new_df, model, encoder, categorical_cols, feature_columns)
    
    # Prepare encoded data for SHAP
    id_columns = ['country_code', 'phone_number', 'full_phone', 'fraud_label']
    X_new = new_df.drop(columns=[col for col in id_columns if col in new_df.columns], errors='ignore')
    
    # Ensure columns match
    missing_cols = set(feature_columns) - set(X_new.columns)
    if missing_cols:
        for col in missing_cols:
            X_new[col] = 0
    X_new = X_new[feature_columns]
    
    # Encode
    X_new_encoded = X_new.copy()
    if encoder and categorical_cols:
        X_new_encoded[categorical_cols] = encoder.transform(X_new[categorical_cols])
    
    # Get top N highest risk cases
    top_risk_indices = results_df.nlargest(top_n, 'fraud_probability').index
    
    print(f"\n{'='*70}")
    print(f"EXPLAINING TOP {top_n} HIGHEST RISK CASES")
    print(f"{'='*70}")
    
    # Explain each high-risk case
    for idx in top_risk_indices:
        explain_single_prediction(
            model, 
            explainer, 
            X_new_encoded, 
            feature_columns, 
            customer_idx=idx
        )
    
    return results_df

# ============================================================================
# 7. MAIN PIPELINE
# ============================================================================

def main_pipeline(df):
    """
    Complete end-to-end pipeline
    """
    print("="*70)
    print("XGBOOST FRAUD DETECTION PIPELINE")
    print("="*70)
    
    # Step 1: Prepare data
    print("\n1. Loading and preparing data...")
    X, y = load_and_prepare_data(df)
    print(f"   Dataset shape: {X.shape}")
    print(f"   Fraud rate: {y.mean():.2%}")
    
    # Step 2: Detect column types
    print("\n2. Detecting column types...")
    categorical_cols, numerical_cols = detect_column_types(X)
    print(f"   Categorical columns ({len(categorical_cols)}): {categorical_cols}")
    print(f"   Numerical columns ({len(numerical_cols)}): {numerical_cols}")
    
    # Step 3: Train-test split
    print("\n3. Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    # Step 4: Encode features
    print("\n4. Encoding categorical features...")
    X_train_enc, X_val_enc, encoder = encode_features(X_train_split, X_val, categorical_cols)
    X_test_enc, _, _ = encode_features(X_test, X_test, categorical_cols)
    if encoder:
        X_test_enc[categorical_cols] = encoder.transform(X_test[categorical_cols])
    
    # Step 5: Train model
    print("\n5. Training XGBoost model...")
    model = train_xgboost_model(X_train_enc, y_train_split, X_val_enc, y_val)
    
    # Step 6: Evaluate model
    print("\n6. Evaluating model on test set...")
    dtest = xgb.DMatrix(X_test_enc, enable_categorical=False, feature_names=X_test_enc.columns.tolist())
    y_pred_proba = model.predict(dtest)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Step 7: Feature importance
    print("\n7. Analyzing feature importance...")
    importance_df = plot_feature_importance(model, X.columns.tolist(), top_n=15)
    print("\nTop 10 Most Important Features:")
    print(importance_df.head(10).to_string(index=False))
    
    # Step 8: SHAP explanations
    print("\n8. Generating SHAP explanations...")
    explainer, shap_values = explain_with_shap(model, X_test_enc, X.columns.tolist())
    
    # Step 9: Explain a high-risk customer
    print("\n9. Explaining individual predictions...")
    # Find a high-risk customer
    high_risk_idx = y_pred_proba.argmax()
    explain_single_prediction(model, explainer, X_test_enc, X.columns.tolist(), high_risk_idx)
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print("\nModel artifacts returned:")
    print("  - model: Trained XGBoost model")
    print("  - encoder: Fitted OrdinalEncoder")
    print("  - explainer: SHAP explainer")
    print("  - importance_df: Feature importance rankings")
    print("  - categorical_cols: List of categorical columns")
    print("  - feature_columns: List of feature columns")
    print("\nTo predict on new data, use:")
    print("  results = predict_new_data(new_df, model, encoder, categorical_cols, feature_columns)")
    print("  OR")
    print("  results = predict_and_explain(new_df, model, encoder, explainer, categorical_cols, feature_columns)")
    
    return {
        'model': model,
        'encoder': encoder,
        'explainer': explainer,
        'importance_df': importance_df,
        'categorical_cols': categorical_cols,
        'feature_columns': X.columns.tolist()
    }

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Load your data
    # df = pd.read_csv('your_fraud_data.csv')
    
    # For demonstration, create sample data structure
    # Replace this with your actual data loading
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
    
    print("="*70)
    print("XGBOOST FRAUD DETECTION - USAGE GUIDE")
    print("="*70)
    print("\n1. TRAINING:")
    print("   pipeline_artifacts = main_pipeline(df)")
    print("\n2. PREDICTION ON NEW DATA (BATCH):")
    print("   new_data = pd.read_csv('new_transactions.csv')")
    print("   results = predict_new_data(")
    print("       new_data,")
    print("       pipeline_artifacts['model'],")
    print("       pipeline_artifacts['encoder'],")
    print("       pipeline_artifacts['categorical_cols'],")
    print("       pipeline_artifacts['feature_columns']")
    print("   )")
    print("\n3. PREDICTION FOR SINGLE TRANSACTION:")
    print("   single_txn = {")
    print("       'customer_vintage_bucket': '6-12 months',")
    print("       'customer_risk_rating': 'High',")
    print("       'txn_count_1h': 5,")
    print("       'avg_monthly_txn_value': 25000,")
    print("       # ... other features")
    print("   }")
    print("   result = predict_single_transaction(")
    print("       single_txn,")
    print("       pipeline_artifacts['model'],")
    print("       pipeline_artifacts['encoder'],")
    print("       pipeline_artifacts['categorical_cols'],")
    print("       pipeline_artifacts['feature_columns']")
    print("   )")
    print("\n4. PREDICTION WITH EXPLANATIONS:")
    print("   results = predict_and_explain(")
    print("       new_data,")
    print("       pipeline_artifacts['model'],")
    print("       pipeline_artifacts['encoder'],")
    print("       pipeline_artifacts['explainer'],")
    print("       pipeline_artifacts['categorical_cols'],")
    print("       pipeline_artifacts['feature_columns'],")
    print("       top_n=5")
    print("   )")
    print("\n5. SAVE MODEL:")
    print("   pipeline_artifacts['model'].save_model('fraud_model.json')")
    print("   import pickle")
    print("   with open('encoder.pkl', 'wb') as f:")
    print("       pickle.dump(pipeline_artifacts['encoder'], f)")
    print("\n6. LOAD MODEL:")
    print("   loaded_model = xgb.Booster()")
    print("   loaded_model.load_model('fraud_model.json')")
    print("   with open('encoder.pkl', 'rb') as f:")
    print("       loaded_encoder = pickle.load(f)")
    print("="*70)



df = pd.read_csv(r'E:\VS code stuff\Dataset Generation\Data\banking_cust_dataset.csv')  # Replace with actual data loading
pipeline_artifacts = main_pipeline(df)
print("\n5. SAVE MODEL:")
pipeline_artifacts['model'].save_model(r'E:\VS code stuff\Dataset Generation\model\fraud_model.json')
import pickle
with open(r'E:\VS code stuff\Dataset Generation\encoder\encoder.pkl', 'wb') as f:
    pickle.dump(pipeline_artifacts['encoder'], f)