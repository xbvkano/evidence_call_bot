from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Client:
    def __init__(self, phoneNumber, houseSize, cleaningType):
        self.phoneNumber = phoneNumber
        self.houseSize = houseSize
        self.cleaningType = cleaningType

    def getPhoneNumber(self):
        return self.phoneNumber

    def setPhoneNumber(self, phoneNumber):
        self.phoneNumber = phoneNumber

    def getHouseSize(self):
        return self.houseSize

    def setHouseSize(self, houseSize):
        self.houseSize = houseSize

    def getCleaningType(self):
        return self.cleaningType

    def setCleaningType(self, cleaningType):
        self.cleaningType = cleaningType

client1 = Client("test", "test", "test")

# Environment variables for sensitive information
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
URL = f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json"

ADMIN_PHONE_1 = os.getenv("ADMIN_PHONE_1")
ADMIN_PHONE_2 = os.getenv("ADMIN_PHONE_2")

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/voice', methods=["POST"])
def Voice():
    resp = VoiceResponse()
    from_number = request.form.get('From')
    client1.setPhoneNumber(from_number)

    audio = "Hello and thank you for contacting Evidence Cleaning. For online appointment bookings, please visit our website at www.worldwideevidence.com."
    resp.say(audio, voice='female')

    gather = resp.gather(num_digits=1, action="/handle-request", timeout=120, method="POST")
    gather.say("To schedule an appointment over the phone, please press 1.", voice='female')

    return str(resp)

@app.route("/handle-request", methods=['GET', 'POST'])
def handle_request():
    resp = VoiceResponse()
    gather = resp.gather(num_digits=1, action="/handle-key", timeout=120, method="POST")
    gather.say("Select the service you need: Press 1 for move-in or move-out cleanings. Press 2 for standard cleanings. Press 3 for deep cleaning. And if you'd like to hear these options again, press 4.", voice='female')
    resp.redirect("/handle-request")
    return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
    digit_pressed = request.values.get('Digits', None)
    resp = VoiceResponse()

    if digit_pressed == "1":
        client1.setCleaningType("Move in/out")
    elif digit_pressed == "2":
        client1.setCleaningType("Standard Cleaning")
    elif digit_pressed == "3":
        client1.setCleaningType("Deep Cleaning")
    else:
        resp.redirect("/handle-request")
    
    gather = resp.gather(num_digits=1, action="/handle-size", timeout=120, method="POST")
    gather.say("Choose the square footage range for your property. Press 1 for 0 to 1000 square feet. Press 2 for 1000 to 2000 square feet. Press 3 for 2000 to 3000 square feet. Press 4 for 3000 to 4000 square feet. Press 5 for 4000 to 5000 square feet. Press 6 for over 5000 square feet. Press 7 to hear these options again.", voice='female')
    resp.redirect("/handle-key")
    return str(resp)

@app.route("/handle-size", methods=['GET', 'POST'])
def handle_size():
    digit_pressed = request.values.get('Digits', None)
    resp = VoiceResponse()

    if digit_pressed == "1":
        client1.setHouseSize("0-1000")
    elif digit_pressed == "2":
        client1.setHouseSize("1001-2000")
    elif digit_pressed == "3":
        client1.setHouseSize("2001-3000")
    elif digit_pressed == "4":
        client1.setHouseSize("3001-4000")
    elif digit_pressed == "5":
        client1.setHouseSize("4001-5000")
    elif digit_pressed == "6":
        client1.setHouseSize("5000+")
    else:
        resp.say("Please select a valid option")
        resp.redirect("/handle-repeatSize")
        return str(resp)

    resp.say("Your selections regarding the service have been successfully saved. Our team will reach out shortly via text message. We appreciate your choice of Evidence Cleaning. Have a great day!", voice="female")

    data = {
        'From': TWILIO_PHONE_NUMBER,
        'To': ADMIN_PHONE_1,
        'Body': f"Cliente novo no sistema de ligar\nNumber: {client1.getPhoneNumber()}\nSize: {client1.getHouseSize()}\nService: {client1.getCleaningType()}"
    }

    data2 = {
        'From': TWILIO_PHONE_NUMBER,
        'To': ADMIN_PHONE_2,
        'Body': f"Cliente novo no sistema de ligar\nNumber: {client1.getPhoneNumber()}\nSize: {client1.getHouseSize()}\nService: {client1.getCleaningType()}"
    }

    response = requests.post(URL, data=data, auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN))
    requests.post(URL, data=data2, auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN))

    try:
        response_data = response.json()
        print(response_data)
    except ValueError:
        print('Error:', response.text)

    return str(resp)

@app.route("/handle-repeatSize", methods=['GET', 'POST'])
def handle_repeat():
    resp = VoiceResponse()
    gather = resp.gather(num_digits=1, action="/handle-size", method="POST")
    gather.say("Choose the square footage range for your property. Press 1 for 0 to 1000 square feet. Press 2 for 1000 to 2000 square feet. Press 3 for 2000 to 3000 square feet. Press 4 for 3000 to 4000 square feet. Press 5 for 4000 to 5000 square feet. Press 6 for over 5000 square feet. Press 7 to hear these options again.", voice='female')
    resp.redirect("/handle-repeatSize")
    return str(resp)

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
