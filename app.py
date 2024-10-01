import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-ymly9%40digiehr-c071a.iam.gserviceaccount.com",
    })
    firebase_admin.initialize_app(cred)

# Firestore client
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
        if user_files:
            for file in user_files:
                st.write(f"File: {file}")
                st.download_button(label=f"Download {file}", 
                                   data=bucket.blob(file).download_as_bytes(),
                                   file_name=file)
        else:
            st.write("No files found for this Aadhaar Number.")
    else:
        st.write("No files found for this Aadhaar Number.")

    # File Upload Section
    st.write("---")
    st.subheader("Upload New Files")
    uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Upload each file to Firestore
            blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

            # Update Firestore with new file information
            doc_ref.set({
                "files": firestore.ArrayUnion([f"{aadhaar_number}/{uploaded_file.name}"])
            }, merge=True)

        st.success("Files uploaded successfully!")
