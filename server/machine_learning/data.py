import pandas as pd

data = {
    "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    "age": [45, 34, 25, 60, 50, 29, 38, 22, 70, 55, 40, 33, 47, 28, 63],
    "gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male"],
    "symptoms": [
        "Fever", "Cough", "Headache", "Chest Pain", "Abdominal Pain", "Back Pain", 
        "Shortness of Breath", "Skin Rash", "Vision Loss", "Dizziness", 
        "Joint Pain", "Fatigue", "Nausea", "Fever and Cough", "Swelling"
    ],
    "diagnosis": [
        "Malaria", "Pneumonia", "Migraine", "Heart Disease", "Appendicitis", 
        "Spinal Injury", "Asthma", "Allergy", "Cataract", "Hypertension", 
        "Arthritis", "Diabetes", "Hepatitis", "COVID-19", "Kidney Disease"
    ],
    "recommended_exam": [
        "Blood Test", "Chest X-Ray", "CT Scan", "ECG", "Ultrasound", 
        "MRI", "Lung Function Test", "Skin Biopsy", "Eye Examination", 
        "Blood Pressure Test", "X-Ray", "Blood Sugar Test", "Liver Function Test", 
        "PCR Test", "Ultrasound"
    ]
}

df = pd.DataFrame(data)
df.to_csv('consultation_data.csv', index=False)
print("Fichier 'consultation_data.csv' créé avec succès.")
