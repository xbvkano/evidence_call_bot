import os
import asyncio
import atexit
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from prisma import Prisma

# ─── Load environment variables from your .env file ────────────────────────
load_dotenv()

# ─── Prisma client setup & immediate connect ──────────────────────────────
db = Prisma()
# Connect to the database as soon as this module is imported
asyncio.get_event_loop().run_until_complete(db.connect())
# Ensure we cleanly disconnect on process exit
atexit.register(lambda: asyncio.get_event_loop().run_until_complete(db.disconnect()))

# ─── Flask app setup ───────────────────────────────────────────────────────
app = Flask(__name__)
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

# ─── Client model ────────────────────────────────────────────────────────────
class Client:
    def __init__(self, phoneNumber, houseSize, cleaningType):
        self.phoneNumber  = phoneNumber
        self.houseSize    = houseSize
        self.cleaningType = cleaningType
        self.calledNumber = None
        self.section      = None

    def getPhoneNumber(self):  return self.phoneNumber
    def setPhoneNumber(self, phoneNumber):  self.phoneNumber = phoneNumber

    def getHouseSize(self):  return self.houseSize
    def setHouseSize(self, houseSize):  self.houseSize = houseSize

    def getCleaningType(self):  return self.cleaningType
    def setCleaningType(self, cleaningType):  self.cleaningType = cleaningType

    def getCalledNumber(self):  return self.calledNumber
    def setCalledNumber(self, calledNumber):  self.calledNumber = calledNumber

    def getSection(self):  return self.section
    def setSection(self, section):  self.section = section

# single shared client object (for demo; in production track per-session)
client1 = Client("test", "test", "test")

# ─── Twilio & Admin configuration ──────────────────────────────────────────
ACCOUNT_SID          = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN           = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER  = os.getenv("TWILIO_PHONE_NUMBER")
URL                  = f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json"
ADMIN_PHONE_1        = os.getenv("ADMIN_PHONE_1")
ADMIN_PHONE_2        = os.getenv("ADMIN_PHONE_2")

# ─── Your multiple Twilio incoming numbers ─────────────────────────────────
TWILIO_PHONE_SOURCE1 = os.getenv("TWILIO_PHONE_SOURCE1")
TWILIO_PHONE_SOURCE2 = os.getenv("TWILIO_PHONE_SOURCE2")
TWILIO_PHONE_SOURCE3 = os.getenv("TWILIO_PHONE_SOURCE3")
TWILIO_PHONE_SOURCE4 = os.getenv("TWILIO_PHONE_SOURCE4")
TWILIO_PHONE_SOURCE5 = os.getenv("TWILIO_PHONE_SOURCE5")

SECTION_MAP = {
    TWILIO_PHONE_SOURCE1: "Instagram/Facebook",
    TWILIO_PHONE_SOURCE2: "Google",
    TWILIO_PHONE_SOURCE3: "Yelp",
    TWILIO_PHONE_SOURCE4: "The Durango Hills Golf Club",
    TWILIO_PHONE_SOURCE5: "V27-Red Rock Country Club",
}

# ─── Routes & IVR logic ──────────────────────────────────────────────────────
@app.route('/')
def index():
    return "Hello, World!"

@app.route('/voice', methods=["POST"])
def Voice():
    """Entry point for incoming calls: capture caller & called numbers."""
    resp = VoiceResponse()
    from_number = request.form.get('From')
    to_number   = request.form.get('To')

    client1.setPhoneNumber(from_number)
    client1.setCalledNumber(to_number)
    client1.setSection(SECTION_MAP.get(to_number, "Unknown Section"))

    resp.say(
        "Hello and thank you for contacting Evidence Cleaning. "
        "For online appointment bookings, please visit our website at www.worldwideevidence.com.",
        voice='female'
    )
    gather = resp.gather(num_digits=1, action="/handle-request", timeout=120, method="POST")
    gather.say("To schedule an appointment over the phone, please press 1.", voice='female')
    return str(resp)

@app.route("/handle-request", methods=['GET', 'POST'])
def handle_request():
    """Second menu: choose which service."""
    resp = VoiceResponse()
    gather = resp.gather(num_digits=1, action="/handle-key", timeout=120, method="POST")
    gather.say(
        "Select the service you need: Press 1 for move-in or move-out cleanings. "
        "Press 2 for standard cleanings. Press 3 for deep cleaning. "
        "Press 4 to hear these options again.",
        voice='female'
    )
    resp.redirect("/handle-request")
    return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
    """Third menu: choose cleaning type."""
    digit = request.values.get('Digits')
    resp  = VoiceResponse()

    if digit == "1":
        client1.setCleaningType("Move in/out")
    elif digit == "2":
        client1.setCleaningType("Standard Cleaning")
    elif digit == "3":
        client1.setCleaningType("Deep Cleaning")
    else:
        return str(resp.redirect("/handle-request"))

    gather = resp.gather(num_digits=1, action="/handle-size", timeout=120, method="POST")
    gather.say(
        "Choose the square footage range for your property: "
        "Press 1 for 0–1000, 2 for 1001–2000, 3 for 2001–3000, "
        "4 for 3001–4000, 5 for 4001–5000, 6 for over 5000, "
        "7 to repeat.",
        voice='female'
    )
    resp.redirect("/handle-key")
    return str(resp)

@app.route("/handle-size", methods=['GET', 'POST'])
def handle_size():
    """Final menu: store size, send SMS, and log the call in the DB."""
    digit = request.values.get('Digits')
    resp  = VoiceResponse()

    size_map = {
        "1": "0-1000", "2": "1001-2000", "3": "2001-3000",
        "4": "3001-4000", "5": "4001-5000", "6": "5000+"
    }
    if digit not in size_map:
        resp.say("Please select a valid option.", voice='female')
        return str(resp.redirect("/handle-repeatSize"))

    client1.setHouseSize(size_map[digit])

    # confirmation to caller
    resp.say(
        "Your selections have been saved. Our team will text you shortly. "
        "Thank you for choosing Evidence Cleaning. Have a great day!",
        voice='female'
    )

    # prepare SMS to admins
    sms_body = (
        f"New call on {client1.getCalledNumber()} ({client1.getSection()})\n"
        f"Caller:  {client1.getPhoneNumber()}\n"
        f"Size:    {client1.getHouseSize()}\n"
        f"Service: {client1.getCleaningType()}"
    )
    data1 = {'From': TWILIO_PHONE_NUMBER, 'To': ADMIN_PHONE_1, 'Body': sms_body}
    data2 = {'From': TWILIO_PHONE_NUMBER, 'To': ADMIN_PHONE_2, 'Body': sms_body}

    # send SMS
    resp1 = requests.post(URL, data=data1, auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN))
    requests.post(URL,            data=data2, auth=HTTPBasicAuth(ACCOUNT_SID, AUTH_TOKEN))

    # log into Prisma DB
    async def log_call():
        await db.call.create({
            "caller":  client1.getPhoneNumber(),
            "called":  client1.getCalledNumber(),
            "size":    client1.getHouseSize(),
            "service": client1.getCleaningType(),
            "section": client1.getSection(),
        })

    asyncio.get_event_loop().run_until_complete(log_call())

    # optional debug
    try:
        print("SMS sent:", resp1.json())
    except ValueError:
        print("SMS error:", resp1.text)

    return str(resp)

@app.route("/handle-repeatSize", methods=['GET', 'POST'])
def handle_repeat():
    """Repeat the size menu if an invalid choice was made."""
    resp = VoiceResponse()
    gather = resp.gather(num_digits=1, action="/handle-size", method="POST")
    gather.say(
        "Choose the square footage range again: Press 1 for 0–1000, … 7 to repeat.",
        voice='female'
    )
    resp.redirect("/handle-repeatSize")
    return str(resp)

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
