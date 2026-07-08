import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Path to the JSON key we just saved
key_path = os.path.join(os.path.dirname(__file__), "firebase-key.json")

try:
    # Initialize Firebase
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    print("✅ Successfully connected to Firebase!")
    print("⏳ Pushing a test case to the cloud...")

    # Data to push
    test_case = {
        "reference_no": "TEST-SYNC-001",
        "complainant_name": "Juan Dela Cruz",
        "complainant_email": "juan@example.com",
        "complainant_address": "Ermita, Manila",
        "incident_location": "Rizal Park",
        "vehicle_type": "Motor",
        "vehicle_details": "Honda Click 125i, Black",
        "status": "Unsolved",
        "narrative": "This is an automated test to verify real-time syncing.",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Push to 'cases' collection
    doc_ref = db.collection("cases").document("TEST-SYNC-001")
    doc_ref.set(test_case)

    print("🚀 Boom! Data pushed successfully.")
    print(
        "👉 Look at your Firebase Console right now. You should see a 'cases' collection appear with your test data!"
    )

except Exception as e:
    print("❌ Error:", e)
