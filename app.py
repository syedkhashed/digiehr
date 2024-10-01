import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debugging: Check if environment variables are loaded
firebase_type = os.getenv("FIREBASE_TYPE")
firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY")
firebase_client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
firebase_client_id = os.getenv("FIREBASE_CLIENT_ID")

# Print debug messages
if not firebase_type:
    st.warning("FIREBASE_TYPE is not set.")
if not firebase_project_id:
    st.warning("FIREBASE_PROJECT_ID is not set.")
if not firebase_private_key:
    st.warning("FIREBASE_PRIVATE_KEY is not set.")
if not firebase_client_email:
    st.warning("FIREBASE_CLIENT_EMAIL is not set.")
if not firebase_client_id:
    st.warning("FIREBASE_CLIENT_ID is not set.")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_credentials = {
        "type": firebase_type,
        "project_id": firebase_project_id,
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": firebase_private_key.replace('\\n', '\n') if firebase_private_key else None,
        "client_email": firebase_client_email,
        "client_id": firebase_client_id,
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    }

    # Check if credentials are correctly formatted
    if firebase_credentials["private_key"] is None:
        st.error("Firebase private key is not set in the environment variables.")
    else:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'your-firebase-bucket-name.appspot.com'  # Replace with your Firebase Storage bucket name
        })

# Firebase Services
bucket = storage.bucket()
db = firestore.client()

# Aadhaar-based login system
st.title("Aadhaar File Management System")

aadhaar_number = st.text_input("Enter your Aadhaar Number", type="password")

if aadhaar_number:
    # Check if Aadhaar number exists in Firestore
    doc_ref = db.collection('users').document(aadhaar_number)
    doc = doc_ref.get()

    if doc.exists:
        st.write("Files associated with your Aadhaar Number:")

        # Display uploaded files
        user_files = doc_ref.get().to_dict().get("files", [])
        for file in user_files:
            st.write(f"File: {file}")
            st.download_button(label=f"Download {file}", 
                               data=bucket.blob(file).download_as_bytes(),
                               file_name=file)
    else:
        st.write("No files found for this Aadhaar Number.")

    # File Upload Section
    st.write("---")
    st.subheader("Upload New Files")
    uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Upload each file to Firebase Storage
            blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

            # Update Firestore with new file information
            doc_ref.set({
                "files": firestore.ArrayUnion([f"{aadhaar_number}/{uploaded_file.name}"])
            }, merge=True)

        st.success("Files uploaded successfully!")
