[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/1to5pc/webuu/python-package.yml?style=for-the-badge&label=Render%20Build)](https://webuu.onrender.com)


# Flask Firebase Application

This is a Flask application that requires Firebase integration (for additional functionality).

## Prerequisites

- Python 3.10 or higher

### For name search functionality

- Firebase project and credentials
- Firebase Admin SDK

## Firebase Setup (For name search functionality)

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Generate a new private key:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file as `firebase_credentials.json` somewhere
3. Set up Firestore Database:
   - Go to Firebase Console > Cloud Firestore
   - Create a new database in production mode
   - Select a location closest to your users

4. Add student data to Firestore:
   - Create a collection named "studz"
   - Add documents with:
     - Document ID: G0XXXX (where XXXX is student number)
     - Field name: "name"
     - Field value: Student's name

   Example structure:

   ```plaintext
   studz/
   ├── G01234
   │   └── name: "John Doe"
   ├── G05678
   │   └── name: "Jane Smith"
   ```

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/1to5pc/webuu.git
   cd webuu
   ```

2. Place your Firebase credentials:

   ```bash
   cp path/to/firebase_credentials.json ./firebase_credentials.json
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     
     source venv/bin/activate
     ```

5. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the application:

   ```bash
   python src/app.py
   ```

⚠️ **Important**: This application requires valid Firebase credentials to run. Make sure you have:

- Created a Firebase project
- Downloaded the credentials JSON file
- Placed the credentials file in the correct location
