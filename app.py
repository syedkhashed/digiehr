import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json

# Function to initialize Firebase
def initialize_firebase():
    try:
        # Load Firebase credentials from the JSON file
        with open('ehr.json') as f:
            firebase_credentials = json.load(f)

        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'digiehr-d9d5b.appspot.com'  # Correct bucket name
            })
            st.success("Firebase initialized successfully.")
        else:
            st.info("Firebase app already initialized.")
        
        # Firestore client
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")
        return None

# Test Firestore connection
def test_firestore_connection(db):
    try:
        # Test Firestore connection
        test_doc_ref = db.collection('users').document('test_user')
        doc = test_doc_ref.get()
        if doc.exists:
            st.success("Firestore connection successful.")
        else:
            st.warning("Test document does not exist.")
    except Exception as e:
        st.error(f"Error connecting to Firestore: {e}")

# Initialize Firebase
db = initialize_firebase()

if db:
    # Test the Firestore connection
    test_firestore_connection(db)

    # Explicitly initialize the storage bucket after initializing the app
    bucket = storage.bucket('digiehr-d9d5b.appspot.com')

    # Aadhaar-based login system
    st.title("Aadhaar File Management System")

    aadhaar_number = st.text_input("Enter your Aadhaar Number", type="password")

    # Variable to check if the user is logged in
    is_logged_in = False

    # Login button
    if st.button("Login"):
        if aadhaar_number:
            # Check if Aadhaar number exists in Firestore
            doc_ref = db.collection('users').document(aadhaar_number)
            st.write(f"Accessing document: {doc_ref.id}")

            try:
                doc = doc_ref.get()
                if doc.exists:
                    st.success("Login successful!")
                    is_logged_in = True
                    st.write("Files associated with your Aadhaar Number:")

                    user_files = doc.to_dict().get("files", [])
                    if user_files:
                        for file in user_files:
                            st.write(f"File: {file}")
                            st.download_button(
                                label=f"Download {file}",
                                data=bucket.blob(file).download_as_bytes(),
                                file_name=file
                            )
                    else:
                        st.write("No files found for this Aadhaar Number.")
                else:
                    st.error("No files found for this Aadhaar Number.")
            except Exception as e:
                st.error(f"Error retrieving document: {e}")
        else:
            st.warning("Please enter your Aadhaar Number.")

    # Conditional File Upload Section
    if is_logged_in:
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
