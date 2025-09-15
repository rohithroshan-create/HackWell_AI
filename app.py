import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import json
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="AI Wellness Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional medical CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #34495E;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .risk-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid;
        transition: transform 0.2s;
    }
    .risk-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .high-risk {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left-color: #f44336;
    }
    .moderate-risk {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left-color: #ff9800;
    }
    .low-risk {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left-color: #4caf50;
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .user-message {
        background: #007bff;
        color: white;
        padding: 0.75rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        text-align: right;
    }
    .bot-message {
        background: #28a745;
        color: white;
        padding: 0.75rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #f39c12;
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
    .recommendation-item {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

class WellnessAssistant:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = {}
        self.performance_metrics = {}
        self.load_models()
        self.setup_chatbot()
    
    def load_models(self):
        """Load trained models and components"""
        try:
            model_files = {
                'heart_disease': 'models/heart_disease_model.pkl',
                'diabetes': 'models/diabetes_model.pkl',
                'hypertension': 'models/hypertension_model.pkl'
            }
            
            scaler_files = {
                'heart_disease': 'models/heart_disease_scaler.pkl',
                'diabetes': 'models/diabetes_scaler.pkl',
                'hypertension': 'models/hypertension_scaler.pkl'
            }
            
            # Load models
            for condition, file_path in model_files.items():
                if os.path.exists(file_path):
                    self.models[condition] = joblib.load(file_path)
                    st.success(f"✅ Loaded {condition} model")
            
            # Load scalers
            for condition, file_path in scaler_files.items():
                if os.path.exists(file_path):
                    self.scalers[condition] = joblib.load(file_path)
            
            # Load feature names and performance metrics
            if os.path.exists('models/feature_names.pkl'):
                self.feature_names = joblib.load('models/feature_names.pkl')
            
            if os.path.exists('models/performance_metrics.pkl'):
                self.performance_metrics = joblib.load('models/performance_metrics.pkl')
            
            if not self.models:
                st.warning("⚠️ No models found. Using demo mode.")
                self.create_demo_models()
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            self.create_demo_models()
    
    def create_demo_models(self):
        """Create demo models for testing"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        
        # Demo performance metrics
        self.performance_metrics = {
            'heart_disease': {'accuracy': 0.87, 'auc': 0.92, 'model_name': 'XGBoost'},
            'diabetes': {'accuracy': 0.85, 'auc': 0.89, 'model_name': 'Random Forest'},
            'hypertension': {'accuracy': 0.83, 'auc': 0.88, 'model_name': 'Logistic Regression'}
        }
        
        # Create demo models
        for condition in ['heart_disease', 'diabetes', 'hypertension']:
            n_features = {'heart_disease': 14, 'diabetes': 10, 'hypertension': 13}[condition]
            
            X_demo = np.random.rand(100, n_features)
            y_demo = np.random.randint(0, 2, 100)
            
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X_demo, y_demo)
            self.models[condition] = model
            
            scaler = StandardScaler()
            scaler.fit(X_demo)
            self.scalers[condition] = scaler
    
    def setup_chatbot(self):
        """Setup AI chatbot knowledge base"""
        self.medical_knowledge = {
            'heart_disease': {
                'risk_factors': [
                    'Age over 55', 'High blood pressure', 'High cholesterol',
                    'Smoking', 'Diabetes', 'Family history', 'Obesity', 'Physical inactivity'
                ],
                'prevention': [
                    'Regular exercise (150 min/week moderate activity)',
                    'Heart-healthy diet (Mediterranean, DASH)',
                    'Maintain healthy weight (BMI 18.5-24.9)',
                    'Don\'t smoke or quit smoking',
                    'Manage stress through relaxation techniques',
                    'Get adequate sleep (7-9 hours)',
                    'Regular health checkups'
                ],
                'symptoms': [
                    'Chest pain or discomfort', 'Shortness of breath',
                    'Pain in arms, back, neck, jaw', 'Nausea', 'Cold sweat'
                ]
            },
            'diabetes': {
                'risk_factors': [
                    'Age over 45', 'Overweight (BMI > 25)', 'Family history',
                    'Physical inactivity', 'High blood pressure', 'Abnormal cholesterol'
                ],
                'prevention': [
                    'Maintain healthy weight',
                    'Be physically active (30 min most days)',
                    'Eat healthy foods (whole grains, vegetables)',
                    'Limit refined carbs and sugary drinks',
                    'Regular health screenings'
                ],
                'symptoms': [
                    'Increased thirst and urination', 'Unexplained weight loss',
                    'Fatigue', 'Blurred vision', 'Slow-healing wounds'
                ]
            },
            'hypertension': {
                'risk_factors': [
                    'Age', 'Family history', 'Obesity', 'Physical inactivity',
                    'High salt diet', 'Alcohol consumption', 'Stress', 'Smoking'
                ],
                'prevention': [
                    'Maintain healthy weight',
                    'Regular physical activity',
                    'Limit sodium intake (<2,300mg/day)',
                    'Eat potassium-rich foods',
                    'Limit alcohol consumption',
                    'Manage stress',
                    'Don\'t smoke'
                ],
                'symptoms': [
                    'Often no symptoms (silent killer)',
                    'Severe headache', 'Chest pain', 'Difficulty breathing',
                    'Vision problems', 'Blood in urine'
                ]
            }
        }
    
    def collect_patient_data(self):
        """Comprehensive patient data collection"""
        st.sidebar.header("📋 Patient Health Assessment")
        
        # Basic Information
        with st.sidebar.expander("👤 Personal Information", expanded=True):
            name = st.text_input("Full Name", placeholder="Enter your full name")
            age = st.slider("Age", 18, 100, 45)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
        # Biometric Data
        with st.sidebar.expander("🩺 Biometric Measurements", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                height = st.slider("Height (cm)", 140, 220, 170)
                systolic_bp = st.slider("Systolic BP", 90, 200, 120)
                heart_rate = st.slider("Heart Rate", 50, 120, 72)
            
            with col2:
                weight = st.slider("Weight (kg)", 40, 200, 70)
                diastolic_bp = st.slider("Diastolic BP", 60, 120, 80)
                glucose = st.slider("Glucose (mg/dL)", 70, 300, 100)
            
            bmi = weight / ((height/100) ** 2)
            st.metric("BMI", f"{bmi:.1f}")
            
            cholesterol = st.slider("Cholesterol (mg/dL)", 100, 400, 200)
        
        # Medical History
        with st.sidebar.expander("🏥 Medical History"):
            family_history = st.multiselect("Family History", 
                                          ["Heart Disease", "Diabetes", "Hypertension", "Stroke"])
            current_conditions = st.multiselect("Current Conditions",
                                              ["High BP", "High Cholesterol", "Diabetes", "Heart Disease"])
            medications = st.text_area("Current Medications")
        
        # Lifestyle Factors
        with st.sidebar.expander("🏃‍♂️ Lifestyle"):
            exercise_freq = st.selectbox("Exercise Frequency", 
                                       ["Never", "1-2 times/week", "3-4 times/week", "Daily"])
            smoking = st.selectbox("Smoking Status", ["Never", "Former", "Current"])
            alcohol = st.selectbox("Alcohol Consumption", ["Never", "Occasional", "Moderate", "Heavy"])
            sleep_hours = st.slider("Sleep Hours/Night", 4, 12, 8)
            stress_level = st.slider("Stress Level (1-10)", 1, 10, 5)
        
        return {
            'name': name, 'age': age, 'gender': gender,
            'height': height, 'weight': weight, 'bmi': bmi,
            'systolic_bp': systolic_bp, 'diastolic_bp': diastolic_bp,
            'heart_rate': heart_rate, 'glucose': glucose, 'cholesterol': cholesterol,
            'family_history': family_history, 'current_conditions': current_conditions,
            'medications': medications, 'exercise_freq': exercise_freq,
            'smoking': smoking, 'alcohol': alcohol, 'sleep_hours': sleep_hours,
            'stress_level': stress_level
        }
    
    def prepare_features(self, patient_data: Dict, condition: str) -> np.ndarray:
        """Prepare features for each condition"""
        try:
            if condition == 'heart_disease':
                # Map to heart disease features
                features = [
                    patient_data['age'],
                    1 if patient_data['gender'] == 'Male' else 0,
                    1,  # chest pain type (default)
                    patient_data['systolic_bp'],
                    patient_data['cholesterol'],
                    1 if patient_data['glucose'] > 120 else 0,
                    0,  # rest ECG
                    patient_data['heart_rate'],
                    0,  # exercise induced angina
                    0,  # oldpeak
                    1,  # slope
                    0,  # ca
                    2,  # thal
                    # Age group feature
                    0 if patient_data['age'] < 40 else 1 if patient_data['age'] < 55 else 2 if patient_data['age'] < 70 else 3
                ]
                
            elif condition == 'diabetes':
                # Map to diabetes features
                features = [
                    0 if patient_data['gender'] == 'Male' else min(5, max(0, (patient_data['age'] - 20) // 5)),  # pregnancies
                    patient_data['glucose'],
                    patient_data['diastolic_bp'],
                    20,  # skin thickness (default)
                    85,  # insulin (default)
                    patient_data['bmi'],
                    0.5,  # diabetes pedigree function
                    patient_data['age'],
                    # BMI category
                    0 if patient_data['bmi'] < 18.5 else 1 if patient_data['bmi'] < 25 else 2 if patient_data['bmi'] < 30 else 3,
                    # Glucose category
                    0 if patient_data['glucose'] < 100 else 1 if patient_data['glucose'] < 126 else 2
                ]
                
            elif condition == 'hypertension':
                # Map to hypertension features
                features = [
                    patient_data['age'],
                    1 if patient_data['gender'] == 'Male' else 0,
                    1 if patient_data['smoking'] == 'Current' else 0,
                    1 if patient_data['alcohol'] in ['Moderate', 'Heavy'] else 0,
                    2 if patient_data['exercise_freq'] == 'Daily' else 1 if '3-4' in patient_data['exercise_freq'] else 0,
                    1 if 'Hypertension' in patient_data['family_history'] else 0,
                    1 if 'Diabetes' in patient_data['current_conditions'] else 0,
                    1 if patient_data['bmi'] > 30 else 0,
                    2 if patient_data['stress_level'] > 7 else 1 if patient_data['stress_level'] > 4 else 0,
                    2,  # salt intake (default high)
                    patient_data['sleep_hours'],
                    8,  # work hours (default)
                    # Age risk category
                    0 if patient_data['age'] < 35 else 1 if patient_data['age'] < 50 else 2 if patient_data['age'] < 65 else 3
                ]
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            st.error(f"Error preparing features for {condition}: {str(e)}")
            return None
    
    def predict_risk(self, patient_data: Dict, condition: str) -> Dict:
        """Predict disease risk"""
        if condition not in self.models:
            return None
        
        features = self.prepare_features(patient_data, condition)
        if features is None:
            return None
        
        try:
            # Scale features
            if condition in self.scalers:
                features = self.scalers[condition].transform(features)
            
            # Get prediction
            model = self.models[condition]
            probability = model.predict_proba(features)[0][1]
            
            # Risk categorization
            if probability < 0.3:
                risk_level = "Low"
                color = "#4CAF50"
            elif probability < 0.6:
                risk_level = "Moderate"
                color = "#FF9800"
            else:
                risk_level = "High"
                color = "#F44336"
            
            return {
                'probability': probability,
                'risk_level': risk_level,
                'color': color,
                'confidence': max(probability, 1 - probability)
            }
            
        except Exception as e:
            st.error(f"Prediction error for {condition}: {str(e)}")
            return None
    
    def create_risk_gauge(self, probability: float, condition: str, color: str) -> go.Figure:
        """Create risk visualization gauge"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = probability * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{condition.replace('_', ' ').title()} Risk"},
            delta = {'reference': 30},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 60], 'color': "yellow"},
                    {'range': [60, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    
    def get_recommendations(self, condition: str, risk_level: str, patient_data: Dict) -> List[str]:
        """Get personalized recommendations"""
        base_recommendations = {
            'heart_disease': {
                'High': [
                    "🚨 Consult a cardiologist immediately for comprehensive evaluation",
                    "🥗 Adopt Mediterranean diet: fish 2x/week, olive oil, nuts, vegetables",
                    "💊 Take prescribed medications exactly as directed",
                    "🚶‍♂️ Start with 10-15 min daily walks, gradually increase",
                    "🚭 Stop smoking completely - use nicotine replacement if needed",
                    "📊 Monitor blood pressure daily at same time",
                    "😴 Maintain 7-9 hours sleep with consistent schedule"
                ],
                'Moderate': [
                    "👨‍⚕️ Schedule regular checkups with your doctor every 3-6 months",
                    "🥗 Increase fruits and vegetables to 5-9 servings daily",
                    "🏃‍♂️ Aim for 150 minutes moderate exercise weekly",
                    "⚖️ Maintain healthy weight (BMI 18.5-24.9)",
                    "🧘‍♀️ Practice stress management: meditation, yoga, deep breathing"
                ],
                'Low': [
                    "✅ Continue healthy lifestyle habits",
                    "🔄 Annual health screenings and checkups",
                    "💪 Maintain regular physical activity",
                    "🥗 Keep eating balanced, nutritious diet"
                ]
            },
            'diabetes': {
                'High': [
                    "🚨 Consult endocrinologist for diabetes management plan",
                    "🍽️ Follow plate method: 1/2 vegetables, 1/4 protein, 1/4 whole grains",
                    "📊 Monitor blood glucose levels as recommended by doctor",
                    "🚶‍♂️ Walk 10-15 minutes after each meal to lower glucose",
                    "⚖️ Work on gradual weight loss (5-10% of body weight)",
                    "👀 Schedule annual eye exams for diabetic retinopathy screening",
                    "🦶 Inspect feet daily for cuts, sores, or changes"
                ],
                'Moderate': [
                    "👨‍⚕️ Regular glucose screening every 3 months",
                    "🥗 Choose low glycemic index foods (oats, beans, apples)",
                    "💪 Include resistance training 2x per week",
                    "💧 Stay hydrated with water, avoid sugary drinks",
                    "😴 Prioritize 7-8 hours quality sleep nightly"
                ],
                'Low': [
                    "✅ Maintain current healthy habits",
                    "🔄 Annual diabetes screening",
                    "🏃‍♂️ Continue regular physical activity",
                    "🥗 Keep eating balanced meals"
                ]
            },
            'hypertension': {
                'High': [
                    "🚨 See doctor immediately for blood pressure management",
                    "🧂 Reduce sodium to <1,500mg daily (read food labels)",
                    "🍌 Eat potassium-rich foods: bananas, spinach, sweet potatoes",
                    "🩺 Monitor blood pressure at home twice daily",
                    "💊 Take prescribed medications at same time daily",
                    "⚖️ Lose weight gradually (1-2 pounds per week)",
                    "🚭 Stop smoking - each cigarette raises BP temporarily"
                ],
                'Moderate': [
                    "👨‍⚕️ Regular BP monitoring and doctor visits",
                    "🥗 Follow DASH diet: fruits, vegetables, low-fat dairy",
                    "🏃‍♂️ 30 minutes aerobic exercise most days",
                    "🍷 Limit alcohol: 1 drink/day women, 2 drinks/day men",
                    "😌 Practice relaxation techniques daily"
                ],
                'Low': [
                    "✅ Maintain current healthy lifestyle",
                    "🔄 Regular blood pressure checks",
                    "💪 Continue regular exercise routine",
                    "🧂 Keep sodium intake moderate"
                ]
            }
        }
        
        return base_recommendations.get(condition, {}).get(risk_level, [])
    
    def ai_chatbot_response(self, question: str, patient_data: Dict, predictions: Dict) -> str:
        """Generate AI chatbot response"""
        question_lower = question.lower()
        
        # Risk-related questions
        if any(word in question_lower for word in ['risk', 'probability', 'chance']):
            response = "Based on your health assessment:\n\n"
            for condition, pred in predictions.items():
                if pred:
                    response += f"🎯 **{condition.replace('_', ' ').title()}**: {pred['probability']:.1%} ({pred['risk_level']} risk)\n"
            
            highest_risk = max(predictions.items(), key=lambda x: x[1]['probability'] if x[1] else 0)
            if highest_risk[1]:
                response += f"\n⚠️ Your highest concern is **{highest_risk[0].replace('_', ' ')}** at {highest_risk[1]['probability']:.1%} risk."
            
            return response
        
        # Prevention questions
        elif any(word in question_lower for word in ['prevent', 'reduce', 'lower', 'improve']):
            # Find highest risk condition
            highest_risk = max(predictions.items(), key=lambda x: x[1]['probability'] if x[1] else 0)
            condition = highest_risk[0]
            
            if condition in self.medical_knowledge:
                prevention_tips = self.medical_knowledge[condition]['prevention']
                response = f"To reduce your **{condition.replace('_', ' ')}** risk:\n\n"
                for i, tip in enumerate(prevention_tips[:5], 1):
                    response += f"{i}. {tip}\n"
                response += "\n⚠️ **Important**: These are general guidelines. Consult your doctor for personalized medical advice."
            
            return response
        
        # Symptom questions
        elif any(word in question_lower for word in ['symptom', 'sign', 'warning']):
            response = "🚨 **Warning Signs to Watch For:**\n\n"
            
            for condition, knowledge in self.medical_knowledge.items():
                if condition in predictions and predictions[condition]['risk_level'] in ['Moderate', 'High']:
                    response += f"**{condition.replace('_', ' ').title()}** symptoms:\n"
                    for symptom in knowledge['symptoms']:
                        response += f"• {symptom}\n"
                    response += "\n"
            
            response += "🚨 **EMERGENCY**: Call 911 if you experience chest pain, difficulty breathing, or severe symptoms!"
            return response
        
        # Lifestyle questions
        elif any(word in question_lower for word in ['diet', 'food', 'exercise', 'lifestyle']):
            response = "🏃‍♂️ **Lifestyle Recommendations Based on Your Risk:**\n\n"
            
            # Get highest risk condition
            highest_risk = max(predictions.items(), key=lambda x: x[1]['probability'] if x[1] else 0)
            condition, pred_data = highest_risk
            
            if pred_data and pred_data['risk_level'] in ['Moderate', 'High']:
                recommendations = self.get_recommendations(condition, pred_data['risk_level'], patient_data)
                for rec in recommendations[:6]:
                    response += f"• {rec}\n"
            
            response += "\n💡 **Remember**: Start gradually and consult healthcare providers before major changes."
            return response
        
        # Default response
        else:
            return """🤖 **I'm your AI Health Assistant!** I can help you understand:

• 📊 Your health risk assessments and what they mean
• 💡 Lifestyle changes to improve your health
• ⚠️ Warning signs and symptoms to watch for
• 🥗 Diet and exercise recommendations
• 🏥 When to seek medical care

**Important**: I provide educational information only. I cannot prescribe medications or replace professional medical advice. Always consult healthcare providers for medical decisions.

Try asking: "What can I do to reduce my risk?" or "What symptoms should I watch for?" """

def main():
    """Main application"""
    # Header
    st.markdown('<h1 class="main-header">🏥 AI Wellness Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Personalized Health Risk Assessment & Wellness Guidance</p>', unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="warning-box">
        <strong>⚕️ Medical Disclaimer:</strong> This AI tool provides educational information only and does not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical decisions.
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize assistant
    assistant = WellnessAssistant()
    
    # Display model performance if available
    if assistant.performance_metrics:
        st.subheader("📊 AI Model Performance")
        cols = st.columns(3)
        
        conditions = ['heart_disease', 'diabetes', 'hypertension']
        condition_names = ['Heart Disease', 'Diabetes', 'Hypertension']
        
        for i, (condition, name) in enumerate(zip(conditions, condition_names)):
            if condition in assistant.performance_metrics:
                metrics = assistant.performance_metrics[condition]
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <h4>{name}</h4>
                        <p><strong>Model:</strong> {metrics['model_name']}</p>
                        <p><strong>Accuracy:</strong> {metrics['accuracy']:.1%}</p>
                        <p><strong>AUC:</strong> {metrics['auc']:.3f}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Collect patient data
    patient_data = assistant.collect_patient_data()
    
    # Analysis button
    if st.sidebar.button("🔍 Analyze Health Risks", type="primary", use_container_width=True):
        if not patient_data['name']:
            st.sidebar.error("⚠️ Please enter your name to continue")
        else:
            with st.spinner("🔄 Analyzing your health data..."):
                # Predict risks
                conditions = ['heart_disease', 'diabetes', 'hypertension']
                predictions = {}
                
                for condition in conditions:
                    pred = assistant.predict_risk(patient_data, condition)
                    if pred:
                        predictions[condition] = pred
                
                # Store in session state
                st.session_state.predictions = predictions
                st.session_state.patient_data = patient_data
                
                # Display results
                display_results(assistant, predictions, patient_data)
    
    # Show previous results
    elif 'predictions' in st.session_state:
        display_results(assistant, st.session_state.predictions, st.session_state.patient_data)
    
    else:
        # Welcome screen
        display_welcome()

def display_results(assistant: WellnessAssistant, predictions: Dict, patient_data: Dict):
    """Display comprehensive results"""
    
    if not predictions:
        st.error("Unable to generate predictions. Please check your input.")
        return
    
    # Overall health summary
    st.subheader("🎯 Health Risk Summary")
    
    cols = st.columns(len(predictions))
    for i, (condition, pred_data) in enumerate(predictions.items()):
        with cols[i]:
            # Risk card
            risk_class = pred_data['risk_level'].lower().replace(' ', '-') + '-risk'
            
            st.markdown(f"""
            <div class="risk-card {risk_class}">
                <h3>{condition.replace('_', ' ').title()}</h3>
                <h1 style="color: {pred_data['color']}">{pred_data['probability']:.1%}</h1>
                <h4><strong>{pred_data['risk_level']} Risk</strong></h4>
                <p>Confidence: {pred_data['confidence']:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Risk gauge
            fig = assistant.create_risk_gauge(pred_data['probability'], condition, pred_data['color'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Personalized recommendations
    st.subheader("💡 Personalized Recommendations")
    
    for condition, pred_data in predictions.items():
        with st.expander(f"📋 {condition.replace('_', ' ').title()} Action Plan", expanded=True):
            recommendations = assistant.get_recommendations(condition, pred_data['risk_level'], patient_data)
            
            for rec in recommendations:
                st.markdown(f"""
                <div class="recommendation-item">
                    {rec}
                </div>
                """, unsafe_allow_html=True)
    
    # AI Chatbot
    st.subheader("🤖 AI Health Assistant")
    st.markdown("Ask me anything about your health assessment!")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Quick questions
    st.markdown("**Quick Questions:**")
    col1, col2, col3 = st.columns(3)
    
    quick_questions = [
        "What's my biggest health risk?",
        "How can I improve my health?",
        "What symptoms should I watch for?"
    ]
    
    for i, question in enumerate(quick_questions):
        col = [col1, col2, col3][i]
        if col.button(question, key=f"quick_{i}"):
            response = assistant.ai_chatbot_response(question, patient_data, predictions)
            st.session_state.chat_history.append({
                'question': question,
                'response': response,
                'timestamp': datetime.now().strftime("%H:%M")
            })
    
    # Chat input
    user_input = st.text_input("💬 Ask your question:", placeholder="e.g., What foods should I avoid?")
    
    if user_input:
        response = assistant.ai_chatbot_response(user_input, patient_data, predictions)
        st.session_state.chat_history.append({
            'question': user_input,
            'response': response,
            'timestamp': datetime.now().strftime("%H:%M")
        })
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Chat History")
        
        for chat in reversed(st.session_state.chat_history[-10:]):  # Show last 10 chats
            st.markdown(f"""
            <div class="user-message">
                <strong>You ({chat['timestamp']}):</strong> {chat['question']}
            </div>
            <div class="bot-message">
                <strong>🤖 AI Assistant:</strong> {chat['response']}
            </div>
            """, unsafe_allow_html=True)

def display_welcome():
    """Welcome screen"""
    st.markdown("""
    ## 👋 Welcome to Your AI Wellness Assistant!
    
    ### 🎯 What We Do
    - **🫀 Heart Disease** risk assessment using UCI clinical dataset
    - **🩸 Type 2 Diabetes** prediction with Pima Indians database  
    - **🩺 Hypertension** evaluation using comprehensive patient data
    - **🤖 AI Health Chatbot** for personalized guidance
    
    ### 🚀 How to Get Started
    1. **📋 Complete Assessment** - Fill your health information in the sidebar
    2. **🔍 Analyze Risks** - Click "Analyze Health Risks" 
    3. **📊 Review Results** - Understand your personalized risk profile
    4. **💡 Follow Recommendations** - Get evidence-based wellness guidance
    5. **🤖 Ask Questions** - Chat with your AI health assistant
    
    ### 🔒 Privacy & Safety
    - ✅ All data processing happens locally
    - ✅ No personal information is stored
    - ✅ Evidence-based recommendations only
    - ✅ No medication prescriptions - always consult doctors
    
    **Ready to start?** Fill out your information in the sidebar!
    """)

if __name__ == "__main__":
    main()
