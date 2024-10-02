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
        'storageBucket': 'digiehr-c071a.appspot.com'  # Correct bucket name
    })

# Firestore client
db = firestore.client()

# Explicitly initialize the storage bucket after initializing the app
bucket = storage.bucket('digiehr-c071a.appspot.com')  # Specify the bucket name directly

# Aadhaar-based login system
st.title("Aadhaar File Management System")

aadhaar_number = st.text_input("Enter your Aadhaar Number", type="password")

# Variable to check if the user is logged in
is_logged_in = False

# Login button
if st.button("Login"):
    if aadhaar_number:
        st.write("Checking Aadhaar number in Firestore...")
        try:
            doc_ref = db.collection('users').document(aadhaar_number)
            doc = doc_ref.get()
            st.write("Aadhaar number checked.")
            
            if doc.exists:
                st.success("Login successful!")
                is_logged_in = True  # Set the login status to true
                st.write("Files associated with your Aadhaar Number:")

                # Display uploaded files
                user_files = doc_ref.get().to_dict().get("files", [])
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
            st.error(f"Error fetching data: {e}")
    else:
        st.warning("Please enter your Aadhaar Number.")

# Conditional File Upload Section
if is_logged_in:
    st.write("---")
    st.subheader("Upload New Files")
    uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                # Upload each file to Firebase Storage
                blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
                blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

                # Update Firestore with new file information
                doc_ref.set({
                    "files": firestore.ArrayUnion([f"{aadhaar_number}/{uploaded_file.name}"])
                }, merge=True)

                st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            except Exception as e:
                st.error(f"Error uploading file '{uploaded_file.name}': {e}")
