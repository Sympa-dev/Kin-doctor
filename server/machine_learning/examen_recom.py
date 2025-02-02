import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Charger les données
data = pd.read_csv('consultation_data.csv')  # Remplacez par vos données

# Prétraitement des données
X = data[['age', 'gender', 'symptoms', 'diagnosis']]  # Features
y = data['recommended_exam']  # Target

# Encodage des données catégoriques
X = pd.get_dummies(X)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraînement du modèle
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Sauvegarde du modèle
joblib.dump(model, 'examen_recom.py')  # Corrected filename to match what's being loaded
