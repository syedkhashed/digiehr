import streamlit as st
import requests
import json
import base64
from PIL import Image
from io import BytesIO
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

# Function to initialize Firebase
def initialize_firebase():
    with open('ehr.json') as f:
        firebase_credentials = json.load(f)

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'digiehr-53676.appspot.com'
        })
        
    return storage.bucket()  # Return the bucket

# Step 1: Initialize Aadhaar eKYC Process (Get Session ID & Captcha)
def get_session_and_captcha():
    url = "https://production.deepvue.tech/v1/ekyc/aadhaar/connect?consent=Y&purpose=For KYC"
    
    headers = {
        'x-api-key': '3abed8a648bd4c50878e248da63066b0',
        'client-id': 'free_tier_122210601103_bbc29ac26a',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        session_id = response_data['data']['session_id']
        captcha_base64 = response_data['data']['captcha']

        # Decode captcha image from base64
        captcha_image = base64.b64decode(captcha_base64)
        image = Image.open(BytesIO(captcha_image))

        return session_id, image
    else:
        st.error("Error in fetching session and captcha: {}".format(response.status_code))
        return None, None

# Step 2: Generate OTP after Captcha Validation
def generate_otp(session_id, aadhaar_number, captcha_input):
    url = f"https://production.deepvue.tech/v1/ekyc/aadhaar/generate-otp?aadhaar_number={aadhaar_number}&captcha={captcha_input}&session_id={session_id}&consent=Y&purpose=For KYC"
    
    headers = {
        'x-api-key': '3abed8a648bd4c50878e248da63066b0',
        'client-id': 'free_tier_122210601103_bbc29ac26a',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if response_data['sub_code'] == 'SUCCESS':
            st.success("OTP sent to your registered mobile number.")
            return True
        else:
            st.error("Failed to send OTP: {}".format(response_data['message']))
            return False
    else:
        st.error("Error in generating OTP: {}".format(response.status_code))
        return False

# Step 3: Verify OTP
def verify_otp(session_id, otp_input):
    url = f"https://production.deepvue.tech/v1/ekyc/aadhaar/verify-otp?otp={otp_input}&session_id={session_id}&consent=Y&purpose=For KYC"
    
    headers = {
        'x-api-key': '3abed8a648bd4c50878e248da63066b0',
        'client-id': 'free_tier_122210601103_bbc29ac26a',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if response_data['sub_code'] == 'SUCCESS':
            st.success("Aadhaar eKYC Successful!")
            return response_data['data']
        else:
            st.error("OTP verification failed: {}".format(response_data['message']))
            return None
    else:
        st.error("Error in verifying OTP: {}".format(response.status_code))
        return None

# Function to display the data in a refined layout
def display_user_details(kyc_data):
    name = kyc_data.get('name')
    gender = kyc_data.get('gender')
    dob = kyc_data.get('dateOfBirth')
    photo_base64 = kyc_data.get('photo')
    basic_address = kyc_data.get('address')

    # Decode and display the user's photo
    if photo_base64:
        photo_image = base64.b64decode(photo_base64)
        image = Image.open(BytesIO(photo_image)).resize((80, 100))  # Resize the photo
    else:
        image = None

    # Create a landscape layout for details and photo
    col1, col2 = st.columns([1, 3])  # Two columns with different width

    with col1:
        if image:
            st.image(image, caption="User Photo", use_column_width=True, 
                      output_format="PNG")
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #f0f8ff; padding: 5px; border-radius: 5px;">
            <h3 style="margin: 0; font-size: 16px;">User Details</h3>
            <p style="font-size: 14px;"><strong>Name:</strong> {name}</p>
            <p style="font-size: 14px;"><strong>Gender:</strong> {gender}</p>
            <p style="font-size: 14px;"><strong>Date of Birth:</strong> {dob}</p>
            <p style="font-size: 14px;"><strong>Address:</strong> {basic_address['careOf']}, {basic_address['house']}, {basic_address['street']}, {basic_address['postOffice']}, {basic_address['district']}, {basic_address['state']}, {basic_address['country']} - {basic_address['pin']}</p>
        </div>
        """, unsafe_allow_html=True)

# EHR Management Functions
def upload_file(aadhaar_number, uploaded_file, file_type, upload_date):
    bucket = storage.bucket('digiehr-53676.appspot.com')
    blob = bucket.blob(f"{aadhaar_number}/{uploaded_file.name}")
    blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)

    db = firestore.client()
    doc_ref = db.collection('users').document(aadhaar_number)
    doc_ref.set({
        "files": firestore.ArrayUnion([{
            "name": uploaded_file.name,
            "type": file_type,
            "upload_date": upload_date.strftime('%Y-%m-%d'),
            "path": f"{aadhaar_number}/{uploaded_file.name}"
        }])
    }, merge=True)

    st.success("File uploaded successfully!")

def show_user_files(aadhaar_number):
    db = firestore.client()
    doc_ref = db.collection('users').document(aadhaar_number)
    
    # Check if the document exists
    if doc_ref.get().exists:
        user_files = doc_ref.get().to_dict().get("files", [])
        return user_files
    else:
        st.warning("No files found for this Aadhaar Number.")
        return []

# Main Streamlit App
def main():
    bucket = initialize_firebase()  # Initialize and assign the bucket

    # Initialize session state attributes
    if 'session_id' not in st.session_state:
        st.session_state.session_id, st.session_state.captcha_image = get_session_and_captcha()
    if 'is_logged_in' not in st.session_state:
        st.session_state.is_logged_in = False
    if 'aadhaar_number' not in st.session_state:
        st.session_state.aadhaar_number = None
    if 'otp_sent' not in st.session_state:
        st.session_state.otp_sent = False
    if 'show_files' not in st.session_state:  # Initialize show_files
        st.session_state.show_files = False
    if 'kyc_data' not in st.session_state:
        st.session_state.kyc_data = None

    st.title("Aadhaar eKYC Verification and EHR Management")

    if not st.session_state.is_logged_in:
        # Step 1: Aadhaar Number Input
        st.subheader("Enter Aadhaar Number and Validate CAPTCHA")
        
        st.session_state.aadhaar_number = st.text_input("Aadhaar Number", max_chars=12, key="aadhaar_input")
        
        # Display CAPTCHA Image
        if st.session_state.captcha_image:
            st.image(st.session_state.captcha_image, caption="CAPTCHA", use_column_width=False)

        # Step 2: CAPTCHA Input
        captcha_input = st.text_input("Enter CAPTCHA", key="captcha_input")

        # Step 3: Generate OTP Button
        if st.button("Generate OTP"):
            if st.session_state.aadhaar_number and captcha_input:
                if generate_otp(st.session_state.session_id, st.session_state.aadhaar_number, captcha_input):
                    st.session_state.otp_sent = True
                else:
                    st.error("Failed to generate OTP.")
            else:
                st.error("Please enter Aadhaar Number and CAPTCHA.")

        # Step 4: OTP Input
        if st.session_state.otp_sent:
            st.subheader("Enter OTP")
            otp_input = st.text_input("OTP", type="password", key="otp_input")

            # Verify OTP Button
            if st.button("Verify OTP"):
                if otp_input:
                    kyc_data = verify_otp(st.session_state.session_id, otp_input)
                    if kyc_data:
                        st.session_state.kyc_data = kyc_data
                        st.session_state.is_logged_in = True  # Set login state to True
                        st.success("Welcome! You have successfully logged in.")
                else:
                    st.error("Please enter the OTP.")

    if st.session_state.is_logged_in:
        # New page for displaying user details and upload options
        st.write("---")
        display_user_details(st.session_state.kyc_data)
        st.write("---")
        st.subheader("Upload New Files")

        # Create two main columns
        col1, col2 = st.columns([1, 1])  # Two columns for upload and type/date

        with col1:
            uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "jpg", "jpeg", "png", "txt", "docx", "xlsx"], key="file_uploader")

        with col2:
            file_type = st.selectbox("Select File Type", ["prescription", "test results", "scan data"], key="file_type_select")
            upload_date = st.date_input("Select Upload Date", datetime.today(), key="upload_date_input")

        if st.button("Upload"):
            if uploaded_file is not None:
                if upload_date <= datetime.today().date():
                    try:
                        upload_file(st.session_state.aadhaar_number, uploaded_file, file_type, upload_date)
                    except Exception as e:
                        st.error(f"Error uploading file: {str(e)}")
                else:
                    st.error("Upload date cannot be in the future. Please select a valid date.")
            else:
                st.error("Please select a file to upload.")

        # Show/Hide Files Button
        if st.button("Show/Hide Files"):
            st.session_state.show_files = not st.session_state.show_files  # Toggle visibility

        # Display the files if the state is set to show
        if st.session_state.show_files:
            user_files = show_user_files(st.session_state.aadhaar_number)

            # Sorting and Filtering Options
            st.subheader("Files associated with your Aadhaar Number:")
            filter_col, sort_col = st.columns([1, 1])  # Two columns for filter and sort

            with filter_col:
                filter_type = st.selectbox("Filter by File Type", ["All", "prescription", "test results", "scan data"])

            with sort_col:
                if st.button("Sort by Date"):
                    user_files.sort(key=lambda x: x['upload_date'])

            # Filter files based on selected type
            if filter_type != "All":
                user_files = [file for file in user_files if file['type'] == filter_type]

            if user_files:
                for idx, file in enumerate(user_files):
                    # Zigzag background effect with light colors
                    background_color = "#e6f7ff" if idx % 2 == 0 else "#f0f8ff"
                    st.markdown(
                        f"""
                        <div style="background-color: {background_color}; padding: 5px; border-radius: 5px; margin: 5px 0;">
                            <h5 style="margin: 0;">{file['name']}</h5>
                            <p style="font-size: small; margin: 0;">
                                <em>Type: {file['type']} | Upload Date: {file['upload_date']}</em>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Download button
                    try:
                        st.download_button(
                            label="Download", 
                            data=bucket.blob(file['path']).download_as_bytes(),
                            file_name=file['name'],  # Use the file's original name
                            key=f"download_{idx}",
                            help="Click to download the file"
                        )
                    except Exception as e:
                        st.error(f"Error downloading file: {str(e)}")
            else:
                st.write("No files found for this Aadhaar Number.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
