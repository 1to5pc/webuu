import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), 'markzui-firebase-adminsdk-fbsvc-9b679ece1f.json'))
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
