import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
cred_path = '/etc/secrets/firebase_credentials.json' if "RENDER" in os.environ else os.path.join(os.path.dirname(__file__), '../firebase_credentials.json')
cred = credentials.Certificate(cred_path)
# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
