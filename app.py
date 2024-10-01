import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debugging: Print all Firebase environment variables (remove this in production)
st.write({
    "FIREBASE_TYPE": os.getenv("FIREBASE_TYPE"),
    "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
    "FIREBASE_PRIVATE_KEY": os.getenv("FIREBASE_PRIVATE_KEY"),  # Be careful not to expose sensitive data
    "FIREBASE_CLIENT_EMAIL": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "FIREBASE_CLIENT_ID": os.getenv("FIREBASE_CLIENT_ID"),
})

# Initialize Firebase
if not firebase_admin._apps:
    firebase_credentials = {
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
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
