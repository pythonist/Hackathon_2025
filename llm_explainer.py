# llm_explainer.py
"""
Advanced LLM-Powered Fraud Explanation Engine
Using Google Gemini
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")


class LLMFraudExplainer:
    """
    Advanced fraud explanation system using Google Gemini
    """
    
    def __init__(self, provider='gemini'):
        """
        Initialize LLM explainer
        
        Args:
            provider: 'gemini' or 'mock' (for testing)
        """
        self.provider = provider
        
        if provider == 'gemini' and GEMINI_AVAILABLE:
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    # Try multiple model names in order of preference
                    model_options = [
                        'gemini-2.0-flash-exp',           # Stable model
                    ]
                    
                    model_initialized = False
                    for model_name in model_options:
                        try:
                            self.client = genai.GenerativeModel(model_name)
                            # Test the model with a simple prompt
                            test_response = self.client.generate_content("Hello", generation_config={'max_output_tokens': 10})
                            print(f"✅ Gemini AI initialized successfully with model: {model_name}")
                            model_initialized = True
                            break
                        except Exception as model_error:
                            print(f"⚠️  Model {model_name} failed: {str(model_error)[:100]}")
                            continue
                    
                    if not model_initialized:
                        raise Exception("All Gemini models failed to initialize")
                except Exception as e:
                    print(f"❌ Gemini initialization failed: {e}")
                    print("⚠️  Falling back to mock explanations")
                    self.provider = 'mock'
            else:
                print("⚠️  GEMINI_API_KEY not found in environment variables")
                print("💡 Set it with: export GEMINI_API_KEY='your_key_here'")
                print("⚠️  Using mock explanations")
                self.provider = 'mock'
        else:
            if not GEMINI_AVAILABLE:
                print("⚠️  Google Generative AI library not available")
            self.provider = 'mock'
            print("ℹ️  Using mock LLM explanations")
    
    
    def generate_fraud_explanation(self, current_transaction, customer_history, camara_data, ml_scores):
        """
        Generate comprehensive fraud explanation using LLM
        
        Args:
            current_transaction: Current transaction details
            customer_history: Past transaction history
            camara_data: CAMARA API results
            ml_scores: ML model scores and breakdown
            
        Returns:
            Dictionary with detailed explanation
        """
        
        # Build context for LLM
        context = self._build_context(current_transaction, customer_history, camara_data, ml_scores)
        
        # Generate explanation based on provider
        if self.provider == 'gemini':
            return self._generate_gemini_explanation(context)
        else:
            return self._generate_mock_explanation(context)
    
    
    def _build_context(self, current_txn, history, camara, scores):
        """Build comprehensive context for LLM"""
        
        # Analyze customer behavior patterns
        behavior_analysis = self._analyze_customer_behavior(history)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(current_txn, history, camara)
        
        # Build structured context
        context = {
            'current_transaction': {
                'phone_number': current_txn.get('phone_number'),
                'amount': current_txn.get('amount'),
                'timestamp': current_txn.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'location': f"{current_txn.get('kyc_city', 'Unknown')}, {current_txn.get('kyc_country', 'Unknown')}"
            },
            
            'ml_scores': {
                'final_risk_score': scores.get('final_score', 0),
                'model_probability': scores.get('model_score', 0),
                'weighted_score': scores.get('weighted_score', 0),
                'condition_score': scores.get('condition_score', 0),
                'decision': scores.get('decision', 'UNKNOWN')
            },
            
            'camara_intelligence': {
                'sim_swap': {
                    'detected': camara.get('sim_swap', {}).get('swapped', False),
                    'details': camara.get('sim_swap', {}).get('last_swap_date', 'N/A')
                },
                'location': {
                    'verified': camara.get('location', {}).get('verified', True),
                    'distance_km': camara.get('location', {}).get('distance_meters', 0) / 1000,
                    'current_country': camara.get('location', {}).get('current_country', 'Unknown')
                },
                'roaming': {
                    'active': camara.get('roaming', {}).get('roaming', False),
                    'network': camara.get('roaming', {}).get('current_network', 'N/A'),
                    'country': camara.get('roaming', {}).get('roaming_country', 'N/A')
                },
                'device_status': {
                    'status': camara.get('device_status', {}).get('connection_status', 'UNKNOWN'),
                    'last_seen': camara.get('device_status', {}).get('last_seen', 'N/A')
                }
            },
            
            'customer_profile': {
                'total_transactions': behavior_analysis['total_transactions'],
                'average_amount': behavior_analysis.get('avg_amount', 0),
                'transaction_frequency': behavior_analysis['frequency'],
                'typical_amount_range': behavior_analysis['typical_range'],
                'high_risk_history': behavior_analysis['high_risk_count'],
                'days_as_customer': behavior_analysis.get('customer_days', 0),
                'velocity_pattern': behavior_analysis['velocity_pattern']
            },
            
            'detected_anomalies': anomalies,
            
            'historical_context': {
                'recent_transactions': behavior_analysis.get('recent_txns', []),
                'location_changes': behavior_analysis['location_changes'],
                'amount_trends': behavior_analysis['amount_trend']
            }
        }
        
        return context
    
    
    def _analyze_customer_behavior(self, history):
        """Analyze customer's historical behavior patterns"""
        
        if not history or len(history) == 0:
            return {
                'total_transactions': 0,
                'avg_amount': 0.0,
                'frequency': 'New Customer',
                'typical_range': '$0 - $0',
                'high_risk_count': 0,
                'customer_days': 0,
                'days_as_customer': 0,
                'velocity_pattern': 'Unknown',
                'recent_txns': [],
                'recent_transactions': [],
                'location_changes': 0,
                'amount_trend': 'No history'
            }
        
        # Calculate statistics
        amounts = [txn.get('transaction_amount', 0) for txn in history]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        # Sort by timestamp
        sorted_history = sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate time span
        if len(sorted_history) > 1:
            try:
                first_date = datetime.strptime(sorted_history[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')
                last_date = datetime.strptime(sorted_history[0]['timestamp'], '%Y-%m-%d %H:%M:%S')
                days_span = (last_date - first_date).days or 1
                frequency = f"{len(history)} txns / {days_span} days"
            except:
                frequency = f"{len(history)} transactions"
                days_span = 1
        else:
            frequency = "First transaction"
            days_span = 0
        
        # Typical amount range
        if amounts:
            min_amt = min(amounts)
            max_amt = max(amounts)
            typical_range = f"${min_amt:.2f} - ${max_amt:.2f}"
        else:
            typical_range = "$0 - $0"
        
        # High risk count
        high_risk_count = sum(1 for txn in history if txn.get('risk_level') == 'High Risk')
        
        # Velocity pattern
        recent_7d = [txn for txn in sorted_history if self._is_recent(txn.get('timestamp', ''), days=7)]
        if len(recent_7d) > 10:
            velocity_pattern = "Very High Activity"
        elif len(recent_7d) > 5:
            velocity_pattern = "High Activity"
        elif len(recent_7d) > 2:
            velocity_pattern = "Moderate Activity"
        else:
            velocity_pattern = "Low Activity"
        
        # Location changes
        locations = set()
        for txn in sorted_history[:10]:
            loc = f"{txn.get('country', 'Unknown')}"
            locations.add(loc)
        location_changes = len(locations) - 1 if len(locations) > 1 else 0
        
        # Amount trend
        if len(amounts) >= 3:
            recent_avg = sum(amounts[:3]) / 3
            older_avg = sum(amounts[-3:]) / 3
            if recent_avg > older_avg * 1.5:
                amount_trend = "Increasing significantly"
            elif recent_avg > older_avg * 1.1:
                amount_trend = "Gradually increasing"
            elif recent_avg < older_avg * 0.7:
                amount_trend = "Decreasing"
            else:
                amount_trend = "Stable"
        else:
            amount_trend = "Insufficient history"
        
        # Recent transactions summary
        recent_txns = []
        for txn in sorted_history[:5]:
            recent_txns.append({
                'amount': txn.get('transaction_amount', 0),
                'risk': txn.get('risk_level', 'Unknown'),
                'time': txn.get('timestamp', 'Unknown')[:16]
            })
        
        return {
            'total_transactions': len(history),
            'avg_amount': avg_amount,
            'average_amount': avg_amount,
            'frequency': frequency,
            'typical_range': typical_range,
            'high_risk_count': high_risk_count,
            'customer_days': days_span,
            'days_as_customer': days_span,
            'velocity_pattern': velocity_pattern,
            'recent_txns': recent_txns,
            'recent_transactions': recent_txns,
            'location_changes': location_changes,
            'amount_trend': amount_trend,
            'amount_trends': amount_trend
        }
    
    
    def _detect_anomalies(self, current_txn, history, camara):
        """Detect specific anomalies in current transaction"""
        
        anomalies = []
        
        # Amount anomaly
        if history and len(history) > 0:
            amounts = [txn.get('transaction_amount', 0) for txn in history]
            avg_amount = sum(amounts) / len(amounts)
            current_amount = current_txn.get('amount', 0)
            
            if current_amount > avg_amount * 3:
                anomalies.append({
                    'type': 'AMOUNT_SPIKE',
                    'severity': 'HIGH',
                    'description': f'Transaction amount (${current_amount:.2f}) is {(current_amount/avg_amount):.1f}x higher than average (${avg_amount:.2f})'
                })
        
        # SIM swap anomaly
        if camara.get('sim_swap', {}).get('swapped'):
            anomalies.append({
                'type': 'SIM_SWAP',
                'severity': 'CRITICAL',
                'description': f"SIM card was recently changed ({camara['sim_swap'].get('last_swap_date', 'recently')}). This is a strong indicator of account takeover."
            })
        
        # Location anomaly
        if not camara.get('location', {}).get('verified', True):
            distance = camara.get('location', {}).get('distance_meters', 0) / 1000
            anomalies.append({
                'type': 'LOCATION_MISMATCH',
                'severity': 'HIGH',
                'description': f'Device location is {distance:.1f} km away from registered address. Possible use of VPN or unauthorized access.'
            })
        
        # Roaming anomaly
        if camara.get('roaming', {}).get('roaming'):
            network = camara['roaming'].get('current_network', 'unknown network')
            country = camara['roaming'].get('roaming_country', 'unknown country')
            anomalies.append({
                'type': 'ROAMING',
                'severity': 'MEDIUM',
                'description': f'Device is roaming on {network} in {country}. Verify if customer is traveling.'
            })
        
        # Device offline anomaly
        if camara.get('device_status', {}).get('connection_status') == 'NOT_CONNECTED':
            anomalies.append({
                'type': 'DEVICE_OFFLINE',
                'severity': 'MEDIUM',
                'description': 'Device is currently offline. Transaction may be from compromised credentials on different device.'
            })
        
        # Velocity anomaly
        if history:
            recent_1h = [txn for txn in history if self._is_recent(txn.get('timestamp', ''), hours=1)]
            if len(recent_1h) >= 3:
                anomalies.append({
                    'type': 'HIGH_VELOCITY',
                    'severity': 'HIGH',
                    'description': f'Detected {len(recent_1h)} transactions within 1 hour. Possible automated attack or account compromise.'
                })
        
        return anomalies
    
    
    def _is_recent(self, timestamp_str, days=None, hours=None):
        """Check if timestamp is within recent timeframe"""
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            
            if days:
                return (now - timestamp).days <= days
            if hours:
                return (now - timestamp).total_seconds() / 3600 <= hours
            
            return False
        except:
            return False
    
    
    def _generate_gemini_explanation(self, context):
        """Generate explanation using Google Gemini"""
        
        try:
            prompt = self._build_llm_prompt(context)
            
            print("🔄 Calling Gemini API...")
            
            # Generate content with Gemini
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 2000,
                }
            )
            
            explanation = response.text
            print("✅ Gemini API call successful")
            
            return self._parse_llm_response(explanation, context)
        
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            print("⚠️  Falling back to mock explanations")
            return self._generate_mock_explanation(context)
    
    
    def _build_llm_prompt(self, context):
        """Build comprehensive prompt for LLM"""
        
        prompt = f"""Analyze this transaction and provide a detailed fraud investigation report.

**CURRENT TRANSACTION:**
- Phone: {context['current_transaction']['phone_number']}
- Amount: ${context['current_transaction']['amount']:.2f}
- Time: {context['current_transaction']['timestamp']}
- Location: {context['current_transaction']['location']}

**FRAUD DETECTION SCORES:**
- Final Risk Score: {context['ml_scores']['final_risk_score']}/100
- ML Model Score: {context['ml_scores']['model_probability']}/100
- Decision: {context['ml_scores']['decision']}

**NETWORK INTELLIGENCE (CAMARA APIs):**
- SIM Swap: {'DETECTED - ' + context['camara_intelligence']['sim_swap']['details'] if context['camara_intelligence']['sim_swap']['detected'] else 'Clear'}
- Location: {'MISMATCH - ' + str(context['camara_intelligence']['location']['distance_km']) + ' km from KYC' if not context['camara_intelligence']['location']['verified'] else 'Verified'}
- Roaming: {'ACTIVE - ' + context['camara_intelligence']['roaming']['network'] + ' in ' + context['camara_intelligence']['roaming']['country'] if context['camara_intelligence']['roaming']['active'] else 'Not roaming'}
- Device Status: {context['camara_intelligence']['device_status']['status']}

**CUSTOMER PROFILE & HISTORY:**
- Total Transactions: {context['customer_profile']['total_transactions']}
- Average Amount: ${context['customer_profile']['average_amount']:.2f}
- Typical Range: {context['customer_profile']['typical_amount_range']}
- High Risk History: {context['customer_profile']['high_risk_history']} transactions
- Customer Duration: {context['customer_profile']['days_as_customer']} days
- Activity Level: {context['customer_profile']['velocity_pattern']}
- Amount Trend: {context['customer_profile'].get('amount_trends', 'N/A')}

**DETECTED ANOMALIES:**
{self._format_anomalies_for_prompt(context['detected_anomalies'])}

**RECENT TRANSACTION HISTORY:**
{self._format_recent_txns_for_prompt(context['historical_context']['recent_transactions'])}

Please provide a structured analysis with these sections:

 **EXECUTIVE SUMMARY** (2-3 sentences): High-level assessment

 **DETAILED ANALYSIS**: What makes this suspicious/legitimate? How does it compare to normal behavior?

 **BEHAVIORAL INSIGHTS**: Past patterns, changes, velocity analysis

 **RISK FACTORS** (list specific red flags with severity)

 **RECOMMENDATION**: APPROVE/BLOCK/ADDITIONAL VERIFICATION with specific next steps

Write clearly for fraud investigators to act upon immediately."""

        return prompt
    
    
    def _format_anomalies_for_prompt(self, anomalies):
        """Format anomalies for LLM prompt"""
        if not anomalies:
            return "- No significant anomalies detected"
        
        formatted = []
        for anomaly in anomalies:
            formatted.append(f"- [{anomaly['severity']}] {anomaly['description']}")
        
        return "\n".join(formatted)
    
    
    def _format_recent_txns_for_prompt(self, recent_txns):
        """Format recent transactions for LLM prompt"""
        if not recent_txns:
            return "- No transaction history available (new customer)"
        
        formatted = []
        for i, txn in enumerate(recent_txns, 1):
            formatted.append(f"{i}. ${txn['amount']:.2f} at {txn['time']} - Risk: {txn['risk']}")
        
        return "\n".join(formatted)
    
    
    def _parse_llm_response(self, llm_text, context):
        """Parse LLM response into structured format"""
        
        sections = {
            'executive_summary': '',
            'detailed_analysis': '',
            'behavioral_insights': '',
            'risk_factors': [],
            'recommendation': {},
            'anomalies': context['detected_anomalies'],
            'customer_profile': context['customer_profile'],
            'generation_method': 'gemini'
        }
        
        # Simple parsing logic
        lines = llm_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if 'EXECUTIVE SUMMARY' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'executive_summary'
                current_content = []
            elif 'DETAILED ANALYSIS' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'detailed_analysis'
                current_content = []
            elif 'BEHAVIORAL INSIGHTS' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'behavioral_insights'
                current_content = []
            elif 'RISK FACTORS' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = 'risk_factors'
                current_content = []
            elif 'RECOMMENDATION' in line.upper():
                if current_section:
                    if current_section == 'risk_factors':
                        sections[current_section] = self._parse_risk_factors(current_content)
                    else:
                        sections[current_section] = '\n'.join(current_content)
                current_section = 'recommendation'
                current_content = []
            elif line and current_section:
                if not line.startswith('#') and not line.startswith('**'):
                    current_content.append(line)
        
        # Handle last section
        if current_section:
            if current_section == 'risk_factors':
                sections[current_section] = self._parse_risk_factors(current_content)
            elif current_section == 'recommendation':
                sections[current_section] = self._parse_recommendation(current_content)
            else:
                sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    
    def _parse_risk_factors(self, content):
        """Parse risk factors from LLM output"""
        risk_factors = []
        for line in content:
            if line.strip() and not line.startswith('-'):
                risk_factors.append({
                    'factor': 'Risk Factor',
                    'severity': 'MEDIUM',
                    'explanation': line.strip()
                })
        return risk_factors
    
    
    def _parse_recommendation(self, content):
        """Parse recommendation from LLM output"""
        text = ' '.join(content)
        
        if 'BLOCK' in text.upper() or 'REJECT' in text.upper():
            action = 'BLOCK TRANSACTION'
        elif 'VERIFY' in text.upper() or 'STEP' in text.upper():
            action = 'REQUIRE ADDITIONAL VERIFICATION'
        else:
            action = 'APPROVE TRANSACTION'
        
        return {
            'action': action,
            'next_steps': [line.strip() for line in content if line.strip()],
            'urgency': 'IMMEDIATE' if 'BLOCK' in action else 'STANDARD'
        }
    
    
    def _generate_mock_explanation(self, context):
        """Generate detailed mock explanation (fallback)"""
        
        decision = context['ml_scores']['decision']
        risk_score = context['ml_scores']['final_risk_score']
        amount = context['current_transaction']['amount']
        
        executive_summary = self._build_mock_summary(context, decision, risk_score)
        detailed_analysis = self._build_mock_detailed_analysis(context)
        behavioral_insights = self._build_mock_behavioral_insights(context)
        risk_factors = self._build_mock_risk_factors(context)
        recommendation = self._build_mock_recommendation(context, decision)
        
        return {
            'executive_summary': executive_summary,
            'detailed_analysis': detailed_analysis,
            'behavioral_insights': behavioral_insights,
            'risk_factors': risk_factors,
            'recommendation': recommendation,
            'anomalies': context['detected_anomalies'],
            'customer_profile': context['customer_profile'],
            'generation_method': 'mock'
        }
    
    
    def _build_mock_summary(self, context, decision, risk_score):
        """Build executive summary"""
        amount = context['current_transaction']['amount']
        phone = context['current_transaction']['phone_number']
        
        if decision == "REJECT":
            return f"This ${amount:.2f} transaction from {phone} has been flagged as HIGH RISK (score: {risk_score}/100) and should be blocked immediately. Multiple critical fraud indicators detected."
        elif decision == "STEP-UP":
            return f"This ${amount:.2f} transaction shows moderate risk signals (score: {risk_score}/100) and requires additional verification."
        else:
            return f"This ${amount:.2f} transaction appears legitimate (score: {risk_score}/100) with all fraud checks passing."
    
    
    def _build_mock_detailed_analysis(self, context):
        """Build detailed analysis"""
        analysis_parts = []
        
        camara = context['camara_intelligence']
        
        if camara['sim_swap']['detected']:
            analysis_parts.append(f"⚠️ CRITICAL - SIM Swap Detected: {camara['sim_swap']['details']}")
        
        if not camara['location']['verified']:
            analysis_parts.append(f"Location Mismatch: Device is {camara['location']['distance_km']:.1f} km from registered address")
        
        if not analysis_parts:
            return "All transaction parameters are within normal ranges."
        
        return "\n\n".join(analysis_parts)
    
    
    def _build_mock_behavioral_insights(self, context):
        """Build behavioral insights"""
        profile = context['customer_profile']
        return f"Customer has {profile['total_transactions']} transactions with average amount ${profile['average_amount']:.2f}. Activity level: {profile['velocity_pattern']}."
    
    
    def _build_mock_risk_factors(self, context):
        """Build risk factors list"""
        risk_factors = []
        for anomaly in context['detected_anomalies']:
            risk_factors.append({
                'factor': anomaly['type'].replace('_', ' ').title(),
                'severity': anomaly['severity'],
                'explanation': anomaly['description']
            })
        return risk_factors
    
    
    def _build_mock_recommendation(self, context, decision):
        """Build recommendation"""
        if decision == "REJECT":
            return {
                'action': 'BLOCK TRANSACTION',
                'next_steps': [
                    'Block transaction and freeze account',
                    'Contact customer through verified channel',
                    'Escalate to fraud investigation team'
                ],
                'urgency': 'IMMEDIATE ACTION REQUIRED'
            }
        elif decision == "STEP-UP":
            return {
                'action': 'REQUIRE ADDITIONAL VERIFICATION',
                'next_steps': [
                    'Hold transaction pending verification',
                    'Send OTP to registered email',
                    'Request biometric authentication'
                ],
                'urgency': 'VERIFY WITHIN 24 HOURS'
            }
        else:
            return {
                'action': 'APPROVE TRANSACTION',
                'next_steps': ['Process normally', 'Continue monitoring'],
                'urgency': 'STANDARD PROCESSING'
            }