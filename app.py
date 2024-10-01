import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json

# Load Firebase credentials from the JSON file
with open('digiehr_firestore.json') as f:
    firebase_credentials = json.load(f)

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'digiehr-c071a.appspot.com'  # Ensure correct bucket name
    })

# Firestore client
db = firestore.client()

# Storage bucket
bucket = storage.bucket()  # Initialize the bucket after the app is initialized

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
            # Upload each file to Firebase Storage
            blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

            # Update Firestore with new file information
            doc_ref.set({
                "files": firestore.ArrayUnion([f"{aadhaar_number}/{uploaded_file.name}"])
            }, merge=True)

        st.success("Files uploaded successfully!")
