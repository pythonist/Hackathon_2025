# dashboard_analytics.py
from collections import defaultdict
from datetime import datetime, timedelta


def calculate_hourly_distribution(logs):
    """Calculate transaction count per hour"""
    hourly_data = defaultdict(int)
    
    for log in logs:
        try:
            timestamp = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')
            hour = timestamp.hour
            hourly_data[hour] += 1
        except:
            continue
    
    return {hour: hourly_data.get(hour, 0) for hour in range(24)}


def calculate_risk_distribution(logs):
    """Calculate count of each risk level"""
    distribution = {'High Risk': 0, 'Medium Risk': 0, 'Low Risk': 0}
    
    for log in logs:
        risk_level = log.get('risk_level', 'Low Risk')
        if risk_level in distribution:
            distribution[risk_level] += 1
    
    return distribution


def get_top_risky_phones(logs, limit=10):
    """Get top risky phone numbers with their stats"""
    phone_stats = defaultdict(lambda: {'total_risk': 0, 'count': 0, 'amounts': []})
    
    for log in logs:
        phone = log['phone_number']
        phone_stats[phone]['total_risk'] += log['fraud_probability']
        phone_stats[phone]['count'] += 1
        phone_stats[phone]['amounts'].append(log['transaction_amount'])
    
    risky_phones = []
    for phone, stats in phone_stats.items():
        avg_risk = (stats['total_risk'] / stats['count']) * 100
        total_amount = sum(stats['amounts'])
        
        risky_phones.append({
            'number': phone,
            'risk_score': round(avg_risk, 1),
            'transaction_count': stats['count'],
            'total_amount': round(total_amount, 2)
        })
    
    risky_phones.sort(key=lambda x: x['risk_score'], reverse=True)
    return risky_phones[:limit]


def calculate_fraud_trend(logs):
    """Calculate fraud trend over last 7 days"""
    daily_fraud = defaultdict(lambda: {'high_risk': 0, 'total': 0})
    
    today = datetime.now()
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    for log in logs:
        try:
            log_date = log['timestamp'][:10]
            if log_date in last_7_days:
                daily_fraud[log_date]['total'] += 1
                if log['risk_level'] == 'High Risk':
                    daily_fraud[log_date]['high_risk'] += 1
        except:
            continue
    
    trend_data = {}
    for date in last_7_days:
        total = daily_fraud[date]['total']
        high_risk = daily_fraud[date]['high_risk']
        fraud_rate = (high_risk / total * 100) if total > 0 else 0
        trend_data[date] = {
            'fraud_rate': round(fraud_rate, 1),
            'total_txns': total,
            'high_risk_txns': high_risk
        }
    
    return trend_data


def calculate_geo_distribution(logs):
    """Calculate transaction distribution by country"""
    geo_data = defaultdict(lambda: {'count': 0, 'high_risk': 0})
    
    for log in logs:
        country = log.get('country', 'Unknown')
        geo_data[country]['count'] += 1
        if log['risk_level'] == 'High Risk':
            geo_data[country]['high_risk'] += 1
    
    geo_list = []
    for country, stats in geo_data.items():
        risk_rate = (stats['high_risk'] / stats['count'] * 100) if stats['count'] > 0 else 0
        geo_list.append({
            'country': country,
            'transaction_count': stats['count'],
            'high_risk_count': stats['high_risk'],
            'risk_rate': round(risk_rate, 1)
        })
    
    geo_list.sort(key=lambda x: x['transaction_count'], reverse=True)
    return geo_list[:10]

def calculate_roi_metrics(logs):
    """Calculate ROI metrics for fraud prevention"""
    if not logs:
        return {
            'total_saved': '0.00',
            'fraud_blocked': 0,
            'accuracy': 0,
            'avg_fraud_amount': '0.00'
        }
    
    high_risk_transactions = [log for log in logs if log['risk_level'] == 'High Risk']
    
    # Calculate total amount that would have been lost
    total_saved = sum(log.get('transaction_amount', 0) for log in high_risk_transactions)
    
    # Calculate average fraud amount
    avg_fraud_amount = total_saved / len(high_risk_transactions) if high_risk_transactions else 0
    
    # Calculate accuracy (this is simplified - in production, use actual feedback data)
    accuracy = 85.5 if len(logs) > 0 else 0
    
    return {
        'total_saved': f'{total_saved:,.2f}',
        'fraud_blocked': len(high_risk_transactions),
        'accuracy': f'{accuracy:.1f}',
        'avg_fraud_amount': f'{avg_fraud_amount:,.2f}'
    }

def calculate_all_analytics(logs):
    """Calculate all dashboard analytics"""
    return {
        'hourly_transactions': calculate_hourly_distribution(logs),
        'risk_distribution': calculate_risk_distribution(logs),
        'top_risky_numbers': get_top_risky_phones(logs, limit=10),
        'fraud_trend': calculate_fraud_trend(logs),
        'geographic_distribution': calculate_geo_distribution(logs)
    }