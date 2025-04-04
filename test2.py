import streamlit as st
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv("D:\\coding\\python\\.env")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Add this to your .env

# Initialize LangChain Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are SAHAS, a disaster alert assistant. Provide precise information about flood and assist in finding nearby safe hospitals."),
    ("user", "{question}")
])

# Initialize Groq LLM
llm = ChatGroq(model="llama3-70b-8192")
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# Streamlit Page Configuration
st.set_page_config(page_title="SAHAS - Hazard Alert System", page_icon="⚠️", layout="wide")

# Custom CSS for Dark Mode
dark_mode_css = """
    <style>
    body, .stApp {
        background-color: #121212 !important;
        color: #FFFFFF !important;
    }
    .stSidebar, .css-1lcbmhc, .css-1d391kg, .css-qrbaxs {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    .stMarkdown, .stChatMessage, .css-1aumxhk {
        background-color: #222 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
    .stTextInput>div>div>input {
        background-color: #333333 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 10px !important;
    }
    .stButton>button {
        background-color: #444 !important;
        color: white !important;
        border-radius: 10px !important;
    }
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #222;
    }
    ::-webkit-scrollbar-thumb {
        background: #666;
        border-radius: 10px;
    }
    </style>
"""

# Sidebar
st.sidebar.markdown("## Settings")

# Dark Mode Toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if st.sidebar.button("Toggle Dark Mode"):
    st.session_state.dark_mode = not st.session_state.dark_mode

if st.session_state.dark_mode:
    st.markdown(dark_mode_css, unsafe_allow_html=True)

st.title("SAHAS - Satellite Assisted Hazard Alert System")

# Get Geolocation
st.markdown("### 📍 Your Current Location")
location = get_geolocation()

if location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    st.success(f"Latitude: {lat}, Longitude: {lon}")

    # --- Google Places API: Find Nearest Hospital ---
    def find_nearest_hospital(lat, lon, api_key):
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&type=hospital&key={api_key}"
        response = requests.get(url)
        results = response.json().get("results")
        if results:
            hospital = results[0]
            name = hospital["name"]
            dest_lat = hospital["geometry"]["location"]["lat"]
            dest_lon = hospital["geometry"]["location"]["lng"]
            return name, dest_lat, dest_lon
        return None, None, None

    def get_directions(lat, lon, dest_lat, dest_lon, api_key):
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lon}&destination={dest_lat},{dest_lon}&key={api_key}"
        response = requests.get(url)
        steps = response.json()["routes"][0]["legs"][0]["steps"]
        directions = "\n".join([step["html_instructions"] for step in steps])
        return directions

    name, dest_lat, dest_lon = find_nearest_hospital(lat, lon, GOOGLE_API_KEY)

    if name:
        st.markdown(f"### 🏥 Nearest Hospital: **{name}**")
        directions = get_directions(lat, lon, dest_lat, dest_lon, GOOGLE_API_KEY)
        st.markdown("#### 🧭 Directions:")
        st.markdown(directions, unsafe_allow_html=True)
    else:
        st.warning("No hospital found nearby.")

# --- Groq Chatbot UI ---
st.markdown("### 🤖 SAHAS Assistant")

if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?", "timestamp": datetime.now().strftime("%H:%M %p") }]

for msg in st.session_state.messages:
    role = "assistant" if msg["role"] == "assistant" else "user"
    st.markdown(f"**{role.capitalize()}**: {msg['content']}  \n*{msg['timestamp']}*")

user_input = st.text_input("Ask about disaster risks in your area...")
if st.button("Send"):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": datetime.now().strftime("%H:%M %p")})
        with st.spinner("Generating response..."):
            try:
                response = chain.invoke({'question': user_input})
                st.session_state.messages.append({"role": "assistant", "content": response, "timestamp": datetime.now().strftime("%H:%M %p")})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}", "timestamp": datetime.now().strftime("%H:%M %p")})
