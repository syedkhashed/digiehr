import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Function to initialize Firebase
def initialize_firebase():
    try:
        print("Loading Firebase credentials...")
        with open('ehr.json') as f:
            firebase_credentials = json.load(f)

        print("Initializing Firebase Admin SDK...")
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'digiehr-d9d5b.appspot.com'  # Correct bucket name
            })
            print("Firebase initialized successfully.")
        else:
            print("Firebase app already initialized.")
        
        db = firestore.client()
        print("Firestore client created.")
        return db
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return None

# Test Firestore connection
def test_firestore_connection(db):
    try:
        print("Testing Firestore connection...")
        test_doc_ref = db.collection('users').document('test_user')
        print(f"Accessing document: {test_doc_ref.id}")

        doc = test_doc_ref.get()
        print("Document retrieval called.")

        if doc.exists:
            print("Document exists. Data:")
            print(doc.to_dict())
        else:
            print("Document does not exist.")
    except Exception as e:
        print(f"Error connecting to Firestore: {e}")

# Initialize Firebase
db = initialize_firebase()

if db:
    # Test the Firestore connection
    test_firestore_connection(db)
