import streamlit as st
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq

load_dotenv()

st.set_page_config(
    page_title=" Universal AI Assistant",
    layout="wide"
)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Get API key from environment variable ONLY (Render sets this)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

st.title(" Universal AI Assistant")
st.markdown("**Powered by Groq API** - Get structured JSON responses for any task!")

# Available Groq models
AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "Llama 3.3 70B - Most capable",
    "llama-3.1-8b-instant": "Llama 3.1 8B - Fast & efficient",
    "llama-3.2-1b-preview": "Llama 3.2 1B - Lightweight",
    "llama-3.2-3b-preview": "Llama 3.2 3B - Balanced",
    "llama-3.2-90b-vision-preview": "Llama 3.2 90B Vision - Multimodal",
    "llama-guard-3-8b": "Llama Guard 3 8B - Safety focused",
    "gemma2-9b-it": "Gemma2 9B - Google's model",
    "mixtral-8x7b-32768": "Mixtral 8x7B - Expert mixture",
}

# Sidebar for configuration ONLY
with st.sidebar:
    st.header(" Configuration")
    
    selected_model = st.selectbox(
        " Select Model",
        options=list(AVAILABLE_MODELS.keys()),
        format_func=lambda x: f"{x} - {AVAILABLE_MODELS[x]}",
        index=0
    )
    
    # Temperature slider for creativity control
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower = more deterministic, Higher = more creative"
    )
    
    st.subheader(" Response Format")
    response_type = st.selectbox(
        "Output Structure",
        ["Auto JSON", "Structured Data", "Key-Value Pairs", "Custom Schema"]
    )
    
    # Display deployment status
    st.divider()
    if GROQ_API_KEY:
        st.success(" API Connected")
        st.caption("Ready to process requests")
    else:
        st.error(" API Not Configured")
        st.caption("Please set GROQ_API_KEY in environment variables")
    
    st.info(" **Tip:** For JSON output, use models like llama-3.3-70b for best results")

# Initialize Groq client
def setup_groq():
    if not GROQ_API_KEY:
        st.error(" API is not configured. Please set GROQ_API_KEY environment variable.")
        return None
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        return client
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
    client = setup_groq()
    if not client:
        return None
    
    # System prompt for JSON formatting
    system_prompt = """You are a JSON formatting assistant. Your task is to convert user requests into well-structured JSON format.

    REQUIREMENTS:
    1. Return ONLY valid JSON, no additional text, no markdown, no explanations
    2. Structure should match the request type
    3. Include all relevant details in organized format
    4. Use proper JSON syntax with double quotes
    5. Make responses comprehensive and actionable
    
    JSON STRUCTURE GUIDELINES:
    - For plans: include timeline, steps, resources, expected_outcomes
    - For analysis: include summary, key_findings, recommendations, risks
    - For ideas: include categories, descriptions, feasibility, steps
    - For schedules: include time_blocks, activities, goals, adjustments
    
    IMPORTANT: Output must be pure JSON only, starting with { and ending with }"""
    
    try:
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this request to structured JSON: {user_input}"}
            ],
            temperature=temperature,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f" API Error: {str(e)}")
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
            with st.expander(f" {key_display}"):
                for sub_key, sub_value in value.items():
                    display_item(sub_key, sub_value)
        elif isinstance(value, list):
            with st.expander(f" {key_display} ({len(value)} items)"):
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
        st.write(f"**{key_display}:** {' Yes' if value else ' No'}")
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
    st.subheader(" Your Request")
    user_input = st.text_area(
        "Describe what you need:",
        placeholder="e.g., Create a marketing plan, Analyze data, Generate ideas, Build schedule...",
        height=150,
        key="user_input",
        help="Be specific for better JSON structure"
    )
    
    # Action buttons
    st.subheader(" Quick Actions")
    col1_1, col1_2, col1_3 = st.columns(3)
    
    with col1_1:
        if st.button(" Generate Plan", use_container_width=True):
            if user_input:
                st.session_state.action = "plan"
    
    with col1_2:
        if st.button(" Analyze", use_container_width=True):
            if user_input:
                st.session_state.action = "analyze"
    
    with col1_3:
        if st.button(" Brainstorm", use_container_width=True):
            if user_input:
                st.session_state.action = "brainstorm"

with col2:
    st.subheader(" Generate Response")
    
    if st.button(" Process Request", type="primary", use_container_width=True):
        if not GROQ_API_KEY:
            st.error(" API is not configured. Please set GROQ_API_KEY environment variable in Render.")
        elif not user_input:
            st.error(" Please enter your request")
        else:
            with st.spinner(" AI is processing your request..."):
                # Generate response
                response_text = generate_structured_response(user_input)
                
                if response_text:
                    # Try to parse JSON
                    json_data = extract_json_from_text(response_text)
                    
                    if json_data:
                        st.success(" Response Generated Successfully!")
                        
                        # Display model info
                        st.info(f"**Model used:** {selected_model} | **Temperature:** {temperature}")
                        
                        # Display structured data
                        display_structured_data(json_data)
                        
                        # Show raw JSON
                        with st.expander(" View Raw JSON"):
                            st.code(json.dumps(json_data, indent=2), language='json')
                        
                        # Download JSON
                        json_str = json.dumps(json_data, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"ai_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
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
                    st.error("❌ Failed to generate response. Please try again.")

# Conversation history
if st.session_state.conversation_history:
    st.divider()
    st.subheader(" Recent Conversations")
    for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
        with st.expander(f" {conv['timestamp']} - {conv['request'][:60]}..."):
            st.write(f"**Model:** {conv['model']}")
            st.write(f"**Request:** {conv['request']}")
            st.json(conv['response'])
            
            # Quick action to reuse
            if st.button(f" Reuse this request", key=f"reuse_{i}"):
                st.session_state.user_input = conv['request']
                st.rerun()

# Footer
st.divider()
st.caption("Powered by Groq API |  Fast inference |  Structured JSON outputs")

