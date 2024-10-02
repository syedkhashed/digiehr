import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Check if Firebase has been initialized already
if not firebase_admin._apps:
    # Get the credentials from secrets
    firebase_credentials = st.secrets["FIREBASE_CREDENTIALS"]

    # Create a credentials object
    cred = credentials.Certificate(firebase_credentials)

    # Initialize Firebase Admin SDK
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()
