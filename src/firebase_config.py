import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), 'firebase_credentials.json'))
# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
