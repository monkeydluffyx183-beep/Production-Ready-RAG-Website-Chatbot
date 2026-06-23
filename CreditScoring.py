import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (roc_auc_score, roc_curve, confusion_matrix, 
                            classification_report, precision_recall_curve, 
                            average_precision_score, f1_score, accuracy_score)
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')

# ============================================
# 1. LOAD AND EXPLORE GERMAN CREDIT DATA
# ============================================
# German Credit Dataset from UCI ML Repository
url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"

# Column names based on dataset documentation
columns = [
    'status', 'duration', 'credit_history', 'purpose', 'credit_amount',
    'savings', 'employment', 'installment_rate', 'personal_status', 'other_debtors',
    'residence', 'property', 'age', 'other_installments', 'housing',
    'existing_credits', 'job', 'dependents', 'telephone', 'foreign_worker', 'class'
]

print("=" * 60)
print("CREDIT SCORING MODEL - GERMAN CREDIT DATA")
print("=" * 60)

# Load data
df = pd.read_csv(url, sep=' ', header=None, names=columns)
print(f"\nDataset loaded: {df.shape[0]} samples, {df.shape[1]} features")

# Target variable: 1 = Good credit, 2 = Bad credit
# Convert to binary: 0 = Good, 1 = Bad (for risk modeling convention)
df['default'] = (df['class'] == 2).astype(int)
df.drop('class', axis=1, inplace=True)

print(f"\nTarget Distribution:")
print(df['default'].value_counts())
print(f"Default Rate: {df['default'].mean():.2%}")

# ============================================
# 2. FEATURE ENGINEERING & PREPROCESSING
# ============================================
print("\n" + "=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)

# Categorical features mapping (based on German Credit documentation)
categorical_mappings = {
    'status': {
        1: 'no_checking', 2: '<0_DM', 3: '0-200_DM', 4: '>200_DM'
    },
    'credit_history': {
        0: 'delay', 1: 'critical', 2: 'existing_paid', 
        3: 'paid_duly', 4: 'no_credits'
    },
    'purpose': {
        0: 'other', 1: 'new_car', 2: 'used_car', 3: 'furniture', 
        4: 'radio_tv', 5: 'appliances', 6: 'repairs', 7: 'education', 
        8: 'vacation', 9: 'retraining', 10: 'business'
    },
    'savings': {
        1: '<100_DM', 2: '100-500_DM', 3: '500-1000_DM', 
        4: '>1000_DM', 5: 'unknown'
    },
    'employment': {
        1: 'unemployed', 2: '<1_year', 3: '1-4_years', 
        4: '4-7_years', 5: '>7_years'
    },
    'personal_status': {
        1: 'male_divorced', 2: 'female_divorced', 3: 'male_single',
        4: 'male_married', 5: 'female_single'
    },
    'other_debtors': {
        1: 'none', 2: 'co-applicant', 3: 'guarantor'
    },
    'property': {
        1: 'real_estate', 2: 'building_society', 3: 'car_other', 4: 'none'
    },
    'other_installments': {
        1: 'bank', 2: 'stores', 3: 'none'
    },
    'housing': {
        1: 'rent', 2: 'own', 3: 'for_free'
    },
    'job': {
        1: 'unemployed', 2: 'unskilled', 3: 'skilled', 4: 'management'
    },
    'telephone': {
        1: 'none', 2: 'yes'
    },
    'foreign_worker': {
        1: 'yes', 2: 'no'
    }
}

# Apply mappings
for col, mapping in categorical_mappings.items():
    df[col + '_cat'] = df[col].map(mapping)

# Create new features
df['credit_to_income_ratio'] = df['credit_amount'] / (df['duration'] + 1)
df['age_group'] = pd.cut(df['age'], bins=[0, 25, 35, 50, 100], labels=['young', 'adult', 'middle', 'senior'])
df['credit_amount_log'] = np.log1p(df['credit_amount'])
df['duration_years'] = df['duration'] / 12

# Risk indicators
df['is_young'] = (df['age'] < 25).astype(int)
df['high_credit'] = (df['credit_amount'] > df['credit_amount'].quantile(0.75)).astype(int)
df['long_duration'] = (df['duration'] > 36).astype(int)

print("Created engineered features:")
print("- credit_to_income_ratio")
print("- age_group")
print("- credit_amount_log")
print("- duration_years")
print("- is_young, high_credit, long_duration (risk indicators)")

# ============================================
# 3. PREPARE DATA FOR MODELING
# ============================================
# Select features for modeling
feature_cols = [
    'duration', 'credit_amount', 'installment_rate', 'residence', 
    'age', 'existing_credits', 'dependents',
    'credit_to_income_ratio', 'credit_amount_log', 'duration_years',
    'is_young', 'high_credit', 'long_duration'
]

# One-hot encode categorical features
categorical_cols = ['status', 'credit_history', 'purpose', 'savings', 
                   'employment', 'personal_status', 'other_debtors',
                   'property', 'other_installments', 'housing', 'job']

df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# Get all feature columns (excluding target and original categorical)
feature_cols = [col for col in df_encoded.columns 
                if col not in ['default', 'age_group'] + list(categorical_mappings.keys())]

X = df_encoded[feature_cols]
y = df_encoded['default']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"\nTraining set: {X_train.shape[0]} samples")
print(f"Test set: {X_test.shape[0]} samples")
print(f"Number of features: {X_train.shape[1]}")

# ============================================
# 4. TRAIN MULTIPLE MODELS
# ============================================
print("\n" + "=" * 60)
print("MODEL TRAINING & COMPARISON")
print("=" * 60)

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced'),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    if name == 'Logistic Regression':
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    auc = roc_auc_score(y_test, y_prob)
    avg_precision = average_precision_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    
    results[name] = {
        'model': model,
        'auc': auc,
        'avg_precision': avg_precision,
        'f1': f1,
        'accuracy': accuracy,
        'y_prob': y_prob,
        'y_pred': y_pred
    }
    
    print(f"  AUC-ROC: {auc:.4f}")
    print(f"  Average Precision: {avg_precision:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    print(f"  Accuracy: {accuracy:.4f}")

# ============================================
# 5. VISUALIZATION 1: MODEL COMPARISON
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# ROC Curves
ax1 = axes[0, 0]
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['y_prob'])
    ax1.plot(fpr, tpr, label=f"{name} (AUC={res['auc']:.3f})", linewidth=2)
ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5)
ax1.set_xlabel('False Positive Rate')
ax1.set_ylabel('True Positive Rate')
ax1.set_title('ROC Curves Comparison', fontsize=12, fontweight='bold')
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.3)

# Precision-Recall Curves
ax2 = axes[0, 1]
for name, res in results.items():
    precision, recall, _ = precision_recall_curve(y_test, res['y_prob'])
    ax2.plot(recall, precision, label=f"{name} (AP={res['avg_precision']:.3f})", linewidth=2)
ax2.set_xlabel('Recall')
ax2.set_ylabel('Precision')
ax2.set_title('Precision-Recall Curves', fontsize=12, fontweight='bold')
ax2.legend(loc='lower left')
ax2.grid(True, alpha=0.3)

# Model Metrics Comparison
ax3 = axes[1, 0]
metrics = ['auc', 'avg_precision', 'f1', 'accuracy']
x = np.arange(len(metrics))
width = 0.25

for i, (name, res) in enumerate(results.items()):
    values = [res[m] for m in metrics]
    ax3.bar(x + i*width, values, width, label=name, alpha=0.8)

ax3.set_ylabel('Score')
ax3.set_title('Model Performance Metrics', fontsize=12, fontweight='bold')
ax3.set_xticks(x + width)
ax3.set_xticklabels(['AUC-ROC', 'Avg Precision', 'F1-Score', 'Accuracy'])
ax3.legend()
ax3.set_ylim(0, 1)
ax3.grid(True, alpha=0.3, axis='y')

# Confusion Matrix for Best Model (Random Forest typically)
best_model_name = max(results, key=lambda x: results[x]['auc'])
best_res = results[best_model_name]
cm = confusion_matrix(y_test, best_res['y_pred'])

ax4 = axes[1, 1]
im = ax4.imshow(cm, interpolation='nearest', cmap='Blues')
ax4.set_title(f'Confusion Matrix - {best_model_name}', fontsize=12, fontweight='bold')
tick_marks = np.arange(2)
ax4.set_xticks(tick_marks)
ax4.set_yticks(tick_marks)
ax4.set_xticklabels(['Good Credit', 'Bad Credit'])
ax4.set_yticklabels(['Good Credit', 'Bad Credit'])

# Add text annotations
thresh = cm.max() / 2.
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax4.text(j, i, format(cm[i, j], 'd'),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black", fontsize=12, fontweight='bold')

ax4.set_ylabel('True Label')
ax4.set_xlabel('Predicted Label')

plt.tight_layout()
plt.savefig('/mnt/agents/output/credit_model_comparison.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nBest performing model: {best_model_name} (AUC: {results[best_model_name]['auc']:.4f})")

# ============================================
# 6. VISUALIZATION 2: FEATURE IMPORTANCE
# ============================================
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Random Forest Feature Importance
rf_model = results['Random Forest']['model']
importances = rf_model.feature_importances_
indices = np.argsort(importances)[::-1][:15]  # Top 15

ax1 = axes[0]
ax1.barh(range(len(indices)), importances[indices], align='center', color='forestgreen', alpha=0.8)
ax1.set_yticks(range(len(indices)))
ax1.set_yticklabels([feature_cols[i] for i in indices])
ax1.invert_yaxis()
ax1.set_xlabel('Importance')
ax1.set_title('Top 15 Features - Random Forest', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='x')

# Logistic Regression Coefficients
lr_model = results['Logistic Regression']['model']
coefs = lr_model.coef_[0]
coef_indices = np.argsort(np.abs(coefs))[::-1][:15]

ax2 = axes[1]
colors = ['red' if c > 0 else 'blue' for c in coefs[coef_indices]]
ax2.barh(range(len(coef_indices)), coefs[coef_indices], align='center', color=colors, alpha=0.7)
ax2.set_yticks(range(len(coef_indices)))
ax2.set_yticklabels([feature_cols[i] for i in coef_indices])
ax2.invert_yaxis()
ax2.set_xlabel('Coefficient Value')
ax2.set_title('Top 15 Features - Logistic Regression', fontsize=12, fontweight='bold')
ax2.axvline(x=0, color='black', linestyle='--', alpha=0.5)
ax2.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('/mnt/agents/output/credit_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 7. VISUALIZATION 3: RISK ANALYSIS
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Credit Amount Distribution by Default
ax1 = axes[0, 0]
df[df['default']==0]['credit_amount'].hist(bins=30, alpha=0.6, label='Good Credit', color='green', ax=ax1)
df[df['default']==1]['credit_amount'].hist(bins=30, alpha=0.6, label='Bad Credit', color='red', ax=ax1)
ax1.set_xlabel('Credit Amount (DM)')
ax1.set_ylabel('Frequency')
ax1.set_title('Credit Amount Distribution', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Age Distribution by Default
ax2 = axes[0, 1]
df[df['default']==0]['age'].hist(bins=20, alpha=0.6, label='Good Credit', color='green', ax=ax2)
df[df['default']==1]['age'].hist(bins=20, alpha=0.6, label='Bad Credit', color='red', ax=ax2)
ax2.set_xlabel('Age')
ax2.set_ylabel('Frequency')
ax2.set_title('Age Distribution by Credit Status', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Duration vs Default Rate
ax3 = axes[1, 0]
duration_bins = pd.cut(df['duration'], bins=5)
default_by_duration = df.groupby(duration_bins)['default'].agg(['mean', 'count'])
default_by_duration['mean'].plot(kind='bar', ax=ax3, color='steelblue', alpha=0.8)
ax3.set_xlabel('Duration (Months)')
ax3.set_ylabel('Default Rate')
ax3.set_title('Default Rate by Loan Duration', fontsize=12, fontweight='bold')
ax3.tick_params(axis='x', rotation=45)
ax3.grid(True, alpha=0.3, axis='y')

# Credit Score Distribution (using Random Forest probabilities)
ax4 = axes[1, 1]
best_model = results[best_model_name]['model']
if best_model_name == 'Logistic Regression':
    scores = best_model.predict_proba(X_test_scaled)[:, 1]
else:
    scores = best_model.predict_proba(X_test)[:, 1]

# Convert to credit score (300-850 scale)
credit_scores = 300 + (1 - scores) * 550  # Higher score = lower risk

ax4.hist(credit_scores, bins=30, color='purple', alpha=0.7, edgecolor='black')
ax4.axvline(x=600, color='red', linestyle='--', label='Subprime Threshold')
ax4.axvline(x=700, color='orange', linestyle='--', label='Good Threshold')
ax4.set_xlabel('Credit Score')
ax4.set_ylabel('Frequency')
ax4.set_title('Predicted Credit Score Distribution', fontsize=12, fontweight='bold')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/mnt/agents/output/credit_risk_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 8. CREDIT SCORECARD GENERATION
# ============================================
print("\n" + "=" * 60)
print("CREDIT SCORECARD")
print("=" * 60)

# Create a simplified scorecard using logistic regression
lr_model = results['Logistic Regression']['model']

# Calculate score points (using PDO = 50, Base odds = 1:50, Base score = 600)
# Standard scorecard approach
pdo = 50  # Points to double the odds
factor = pdo / np.log(2)
offset = 600 - factor * np.log(50)

# Get coefficients and intercept
coef = lr_model.coef_[0]
intercept = lr_model.intercept_[0]

# Create scorecard DataFrame
scorecard_data = []
for i, feature in enumerate(feature_cols):
    # For continuous variables, score per unit
    score_per_unit = -coef[i] * factor  # Negative because lower prob = higher score
    scorecard_data.append({
        'Feature': feature,
        'Coefficient': coef[i],
        'Score_Per_Unit': score_per_unit,
        'Importance_Rank': abs(coef[i])
    })

scorecard_df = pd.DataFrame(scorecard_data)
scorecard_df = scorecard_df.sort_values('Importance_Rank', ascending=False)
scorecard_df['Base_Score'] = offset - intercept * factor

print("\nTop 10 Scorecard Features:")
print(scorecard_df.head(10)[['Feature', 'Coefficient', 'Score_Per_Unit']].to_string(index=False))

# ============================================
# 9. INTERACTIVE PREDICTION FUNCTION
# ============================================
def predict_credit_risk(applicant_data):
    """
    Predict credit risk for a new applicant.
    
    Parameters:
    applicant_data: dict with keys matching feature names
    """
    # Create DataFrame
    input_df = pd.DataFrame([applicant_data])
    
    # Apply same preprocessing
    input_df['credit_to_income_ratio'] = input_df['credit_amount'] / (input_df['duration'] + 1)
    input_df['credit_amount_log'] = np.log1p(input_df['credit_amount'])
    input_df['duration_years'] = input_df['duration'] / 12
    input_df['is_young'] = (input_df['age'] < 25).astype(int)
    input_df['high_credit'] = (input_df['credit_amount'] > 4000).astype(int)
    input_df['long_duration'] = (input_df['duration'] > 36).astype(int)
    
    # Ensure all columns match training data
    for col in feature_cols:
        if col not in input_df.columns:
            input_df[col] = 0
    
    input_df = input_df[feature_cols]
    
    # Scale
    input_scaled = scaler.transform(input_df)
    
    # Predict
    prob_default = lr_model.predict_proba(input_scaled)[0, 1]
    credit_score = int(300 + (1 - prob_default) * 550)
    
    # Risk category
    if credit_score >= 750:
        risk = "Excellent"
        decision = "Approve - Low Risk"
    elif credit_score >= 700:
        risk = "Good"
        decision = "Approve - Standard Terms"
    elif credit_score >= 650:
        risk = "Fair"
        decision = "Approve - Review Terms"
    elif credit_score >= 600:
        risk = "Poor"
        decision = "Conditional Approval"
    else:
        risk = "Very Poor"
        decision = "Reject - High Risk"
    
    return {
        'default_probability': prob_default,
        'credit_score': credit_score,
        'risk_category': risk,
        'recommendation': decision
    }

# ============================================
# 10. EXAMPLE PREDICTIONS
# ============================================
print("\n" + "=" * 60)
print("SAMPLE PREDICTIONS")
print("=" * 60)

sample_applicants = [
    {
        'status': 4, 'duration': 12, 'credit_history': 3, 'purpose': 0,
        'credit_amount': 1000, 'savings': 4, 'employment': 5,
        'installment_rate': 4, 'personal_status': 3, 'other_debtors': 1,
        'residence': 4, 'property': 2, 'age': 45, 'other_installments': 3,
        'housing': 2, 'existing_credits': 2, 'job': 3, 'dependents': 1,
        'telephone': 2, 'foreign_worker': 2
    },  # Low risk profile
    {
        'status': 2, 'duration': 48, 'credit_history': 1, 'purpose': 10,
        'credit_amount': 8000, 'savings': 1, 'employment': 1,
        'installment_rate': 2, 'personal_status': 1, 'other_debtors': 1,
        'residence': 2, 'property': 4, 'age': 22, 'other_installments': 1,
        'housing': 1, 'existing_credits': 3, 'job': 1, 'dependents': 2,
        'telephone': 1, 'foreign_worker': 1
    }   # High risk profile
]

for i, applicant in enumerate(sample_applicants, 1):
    result = predict_credit_risk(applicant)
    print(f"\nApplicant {i}:")
    print(f"  Credit Score: {result['credit_score']}")
    print(f"  Default Probability: {result['default_probability']:.2%}")
    print(f"  Risk Category: {result['risk_category']}")
    print(f"  Recommendation: {result['recommendation']}")

# ============================================
# 11. FINAL SUMMARY
# ============================================
print("\n" + "=" * 60)
print("MODEL SUMMARY")
print("=" * 60)

print(f"""
Dataset: German Credit Data (UCI ML Repository)
Total Samples: {df.shape[0]}
Features Used: {len(feature_cols)}
Default Rate: {df['default'].mean():.2%}

Model Performance (Best: {best_model_name}):
- AUC-ROC: {results[best_model_name]['auc']:.4f}
- Average Precision: {results[best_model_name]['avg_precision']:.4f}
- F1-Score: {results[best_model_name]['f1']:.4f}

Key Risk Factors Identified:
1. Credit amount and duration
2. Checking account status
3. Credit history
4. Age and employment stability
5. Savings behavior

Credit Score Range: 300-850
Risk Tiers: Excellent (750+), Good (700-749), Fair (650-699), 
            Poor (600-649), Very Poor (<600)
""")

print("\nCharts saved to:")
print("1. /mnt/agents/output/credit_model_comparison.png")
print("2. /mnt/agents/output/credit_feature_importance.png")
print("3. /mnt/agents/output/credit_risk_analysis.png")
