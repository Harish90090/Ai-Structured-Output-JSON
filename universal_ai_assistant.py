import streamlit as st
import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title=" Universal AI Assistant",
    layout="wide"
)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv('GEMINI_API_KEY')

st.title("🤖 Universal AI Assistant")
st.markdown("**Powered by Google Gemini AI** - Get structured JSON responses for any task!")

# Available Gemini models
AVAILABLE_MODELS = {
    "gemini-2.0-flash": "Fast & versatile (Recommended)",
    "gemini-1.5-flash": "Fast & efficient", 
    "gemini-1.5-pro": "Advanced reasoning",
    "gemini-2.5-flash-preview-03-25": "Latest Flash preview",
    "gemini-2.5-pro-preview-03-25": "Latest Pro preview"
}

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    api_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your API key from https://aistudio.google.com/"
    )
    
    if api_key:
        st.session_state.api_key = api_key
    
    selected_model = st.selectbox(
        "Select Model",
        options=list(AVAILABLE_MODELS.keys()),
        format_func=lambda x: f"{x} - {AVAILABLE_MODELS[x]}",
        index=0
    )
    
    st.subheader("Response Format")
    response_type = st.selectbox(
        "Output Structure",
        ["Auto JSON", "Structured Data", "Key-Value Pairs", "Custom Schema"]
    )
    

    


# Initialize Gemini API
def setup_gemini():
    if not st.session_state.api_key:
        st.error(" Please enter your Gemini API key in the sidebar")
        return None
    
    try:
        genai.configure(api_key=st.session_state.api_key)
        return genai.GenerativeModel(selected_model)
    except Exception as e:
        st.error(f" API configuration failed: {str(e)}")
        return None

# Function to extract JSON from response
def extract_json_from_text(text):
    """Extract JSON from text response"""
    try:
        # Try to parse directly first
        return json.loads(text)
    except:
        # Try to find JSON pattern in text
        json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return None

# Function to generate structured response
def generate_structured_response(user_input):
    model = setup_gemini()
    if not model:
        return None
    
    prompt = f"""
    Analyze this request and generate a comprehensive, structured response in VALID JSON format.
    
    USER REQUEST: {user_input}
    
    REQUIREMENTS:
    1. Return ONLY valid JSON, no additional text
    2. Structure should match the request type
    3. Include all relevant details in organized format
    4. Use proper JSON syntax
    5. Make it comprehensive and actionable
    
    JSON STRUCTURE GUIDELINES:
    - For plans: include timeline, steps, resources, expected_outcomes
    - For analysis: include summary, key_findings, recommendations, risks
    - For ideas: include categories, descriptions, feasibility, steps
    - For schedules: include time_blocks, activities, goals, adjustments
    
    Response must be pure JSON:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ API Error: {str(e)}")
        return None

# Function to display JSON in a user-friendly way
def display_structured_data(data):
    if not data or not isinstance(data, dict):
        st.error("Invalid data format received")
        return
    
    # Display main sections
    for key, value in data.items():
        key_display = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            with st.expander(f"📁 {key_display}"):
                for sub_key, sub_value in value.items():
                    display_item(sub_key, sub_value)
        elif isinstance(value, list):
            with st.expander(f"📋 {key_display} ({len(value)} items)"):
                for i, item in enumerate(value, 1):
                    if isinstance(item, dict):
                        st.subheader(f"Item {i}")
                        for k, v in item.items():
                            display_item(k, v)
                    else:
                        st.write(f"• {item}")
        else:
            display_item(key, value)

def display_item(key, value):
    """Display individual key-value pairs"""
    key_display = key.replace('_', ' ').title()
    
    if isinstance(value, bool):
        st.write(f"**{key_display}:** {' Yes' if value else '❌ No'}")
    elif isinstance(value, (int, float)):
        st.metric(key_display, value)
    elif isinstance(value, list):
        st.write(f"**{key_display}:**")
        for item in value:
            st.write(f"• {item}")
    elif value is None or value == "":
        st.write(f"**{key_display}:** Not specified")
    else:
        st.write(f"**{key_display}:** {value}")

# Main application layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Your Request")
    user_input = st.text_area(
        "Describe what you need:",
        placeholder="e.g., Create a marketing plan, Analyze data, Generate ideas, Build schedule...",
        height=150,
        key="user_input"
    )
    
    # Action buttons
    st.subheader(" Quick Actions")
    if st.button("Generate Plan", use_container_width=True):
        if user_input:
            st.session_state.action = "plan"
    
    if st.button("Analyze Data", use_container_width=True):
        if user_input:
            st.session_state.action = "analyze"
    
    if st.button("Brainstorm", use_container_width=True):
        if user_input:
            st.session_state.action = "brainstorm"

with col2:
    st.subheader(" Generate Response")
    
    if st.button(" Process Request", type="primary", use_container_width=True):
        if user_input and st.session_state.api_key:
            with st.spinner("AI is processing your request..."):
                # Generate response
                response_text = generate_structured_response(user_input)
                
                if response_text:
                    # Try to parse JSON
                    json_data = extract_json_from_text(response_text)
                    
                    if json_data:
                        st.success("Response Generated Successfully!")
                        
                        # Display model info
                        st.info(f"**Model used:** {selected_model}")
                        
                        # Display structured data
                        display_structured_data(json_data)
                        
                        # Show raw JSON
                        with st.expander(" View Raw JSON"):
                            st.code(json.dumps(json_data, indent=2), language='json')
                        
                        # Download JSON
                        json_str = json.dumps(json_data, indent=2)
                        st.download_button(
                            label=" Download JSON",
                            data=json_str,
                            file_name=f"ai_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        
                        # Add to conversation history
                        st.session_state.conversation_history.append({
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'request': user_input,
                            'response': json_data,
                            'model': selected_model
                        })
                    else:
                        st.error(" Failed to parse JSON response")
                        st.info(" Raw response for debugging:")
                        st.code(response_text)
                else:
                    st.error("Failed to generate response. Please try again.")
        else:
            if not user_input:
                st.error("Please enter your request")
            if not st.session_state.api_key:
                st.error(" Please enter your Gemini API key in the sidebar")

# Conversation history
if st.session_state.conversation_history:
    st.subheader(" Recent Conversations")
    for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
        with st.expander(f" {conv['timestamp']} - {conv['request'][:60]}..."):
            st.write(f"**Model:** {conv['model']}")
            st.write(f"**Request:** {conv['request']}")
            st.json(conv['response'])



