from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

phone_number = '+34623551372'  # User's phone number in E.164 format
friendly_name = "ATIQUITO"

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')

# Initialize the Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

service = client.verify.services.create(friendly_name=friendly_name)
service_sid = service.sid


channel = 'call'  # 'sms' or 'call'

verification = client.verify.services(service_sid).verifications.create(
    to=phone_number,
    channel=channel
)

print(f"Verification status: {verification.status}")

code = input("Enter the verification code: ") # The verification code provided by the user

verification_check = client.verify.services(service_sid).verification_checks.create(
    to=phone_number,
    code=code
)

if verification_check.status == 'approved':
    print('Phone number verified successfully.')
else:
    print('Verification failed. Please try again.')

