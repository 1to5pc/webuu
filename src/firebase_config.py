import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate('/etc/secrets/markzui-firebase-adminsdk-fbsvc-9b679ece1f.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
