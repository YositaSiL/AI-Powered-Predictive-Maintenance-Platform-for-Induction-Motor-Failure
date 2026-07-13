import joblib

model = joblib.load("saved_models/maintenance_model.pkl")

print("MODEL LOADED SUCCESSFULLY")
print(type(model))