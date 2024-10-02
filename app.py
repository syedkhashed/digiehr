import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import time

# Initialize Firebase Admin SDK
firebase_credentials = st.secrets["FIREBASE_CREDENTIALS"]
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'digiehr-f3177.appspot.com'
        })
        st.success("Firebase Admin initialized.")
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")

# Firestore client
try:
    db = firestore.client()
    bucket = storage.bucket('digiehr-f3177.appspot.com')
    st.success("Firestore and Storage initialized.")
except Exception as e:
    st.error(f"Error connecting to Firestore: {e}")

# Function to test Firestore connection
def test_firestore_connection():
    try:
        st.write("Testing Firestore connection...")
        db.collection('users').limit(1).get()  # This should trigger a connection
        st.success("Firestore connection successful!")
        return True
    except Exception as e:
        st.error(f"Firestore connection error: {e}")
        return False

# Aadhaar-based login system
st.title("Aadhaar File Management System")

aadhaar_number = st.text_input("Enter your Aadhaar Number", type="password")

# Variable to check if the user is logged in
is_logged_in = False

# Check Firestore connection
if test_firestore_connection():
    st.success("Firestore connection successful!")

# Login button
if st.button("Login"):
    if aadhaar_number:
        st.write("Checking Aadhaar Number...")
        doc_ref = db.collection('users').document(aadhaar_number)

        doc = fetch_user_doc(doc_ref)
        if doc is None:
            st.stop()  # Exit if timed out or error occurred

        if doc.exists:
            st.success("Login successful!")
            is_logged_in = True
            st.write("Files associated with your Aadhaar Number:")

            user_files = doc.to_dict().get("files", [])
            if user_files:
                for file in user_files:
                    st.write(f"File: {file}")
                    st.download_button(label=f"Download {file}", 
                                       data=bucket.blob(file).download_as_bytes(),
                                       file_name=file)
            else:
                st.write("No files found for this Aadhaar Number.")
        else:
            st.error("No files found for this Aadhaar Number.")
    else:
        st.warning("Please enter your Aadhaar Number.")

# Conditional File Upload Section
if is_logged_in:
    st.write("---")
    st.subheader("Upload New Files")
    uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

            # Update Firestore with new file information
            doc_ref.set({
                "files": firestore.ArrayUnion([f"{aadhaar_number}/{uploaded_file.name}"])
            }, merge=True)

        st.success("Files uploaded successfully!")
