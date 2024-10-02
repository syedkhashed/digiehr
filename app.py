import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    firebase_credentials = st.secrets["FIREBASE_CREDENTIALS"]
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()


# Function to test Firestore connection
def test_firestore_connection():
    try:
        st.write("Testing Firestore connection...")
        doc_ref = db.collection('users').limit(1).get()  # Fetching one document
        if doc_ref:
            st.success("Firestore connection successful! Found documents:")
            for doc in doc_ref:
                st.write(f"Document ID: {doc.id}, Data: {doc.to_dict()}")
        else:
            st.warning("No documents found in 'users' collection.")
    except Exception as e:
        st.error(f"Error connecting to Firestore: {e}")

# Streamlit interface
st.title("Firebase Firestore Test")

# Button to test connection
if st.button("Test Firestore Connection"):
    test_firestore_connection()
