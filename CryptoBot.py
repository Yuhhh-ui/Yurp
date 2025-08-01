import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import google.generativeai as genai
import re

# Page configuration
st.set_page_config(
    page_title="Kryptonic AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - ADD YOUR GEMINI API KEY HERE
GEMINI_API_KEY = "AIzaSyDEgi35dDHu0BfHas34-QDy0NjXrAQP2nM"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

class CryptoChatbot:
    def _init_(self, gemini_api_key):
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        # Updated model name - try the latest available model
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-1.0-pro')
            except:
                self.model = genai.GenerativeModel('models/gemini-pro')
        
        self.supported_coins = [
            'bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana',
            'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'polygon',
            'ripple', 'litecoin', 'stellar', 'monero', 'tron'
        ]
    
    def get_crypto_price(self, coin_id):
        """Get current price and basic info for a cryptocurrency"""
        try:
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def get_trending_coins(self):
        """Get trending cryptocurrencies"""
        try:
            url = f"{COINGECKO_BASE_URL}/search/trending"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def get_market_overview(self):
        """Get top cryptocurrencies by market cap"""
        try:
            url = f"{COINGECKO_BASE_URL}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 10,
                'page': 1,
                'sparkline': 'false'
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def get_current_market_data(self, num_top_coins=5, num_trending_coins=3):
        """Get current market data to provide context to AI"""
        market_data = self.get_market_overview()
        trending_data = self.get_trending_coins()
        
        context = "Current Crypto Market Data:\n"
        
        if market_data:
            context += f"Top {num_top_coins} Cryptocurrencies by Market Cap:\n"
            for i, coin in enumerate(market_data[:num_top_coins], 1):
                price = coin['current_price']
                change = coin['price_change_percentage_24h']
                context += f"{i}. {coin['name']} ({coin['symbol'].upper()}): ${price:,.2f} ({change:+.2f}%)\n"
        
        if trending_data and 'coins' in trending_data:
            context += f"\nTrending Coins (Top {num_trending_coins}):\n"
            for i, coin in enumerate(trending_data['coins'][:num_trending_coins], 1):
                context += f"{i}. {coin['item']['name']} ({coin['item']['symbol']})\n"
        
        return context
    
    def ask_ai(self, user_question):
        """Ask Gemini AI about cryptocurrency topics and basic conversation"""
        
        try:
            # Get current market data for context
            market_context = self.get_current_market_data()
            
            # Create prompt for Gemini
            prompt = f"""You are "Kryptonic," a young, super intelligent cryptocurrency expert with a Gen Z persona. Your goal is to be an informative, friendly, encouraging, and fun guide for beginners learning about crypto. You can use Gen Z slang but still sound professional and knowledgeable with a casual, friendly, conversational tone. Your responses should be easy to understand and avoid overwhelming jargon.  
  

PERSONALITY:
- Be friendly, enthusiastic, and relatable
- Use simple, everyday language (no fancy financial jargon)
- Be like a knowledgeable friend explaining crypto
- Use emojis but don't overdo it
- Keep it real and honest about risks
- Make complex topics easy to understand

SPECIAL HANDLING:
1. If someone greets you (hello, hi, hey) - respond warmly and introduce yourself as Kryptonic, their crypto buddy
2. If someone asks "who are you", "what are you", "tell me about yourself" - explain you're Kryptonic AI, a crypto expert that helps with crypto questions, prices, and education
3. If someone asks "what can you do", "how can you help" - list your capabilities: crypto explanations, live prices, market data, trading help, etc.
4. For basic conversational stuff like "thanks", "goodbye" - respond appropriately but guide back to crypto
5. If it's completely unrelated to crypto (weather, sports, etc.) - politely redirect: "Hey! I'm all about crypto stuff. What crypto question can I help with?"

RULES:
1. Focus primarily on crypto-related topics If asked respond with: “I’m so sorry, but I do not have the capabilities to answer this question. I can however assist with any and everything cryptocurrency related!
2. Handle basic greetings and questions about yourself naturally
3. Explain things simply but accurately and professionally 
4. Use current market data when it helps
5. Keep responses under 150 words
6. Be encouraging but realistic about crypto investing
7. Always mention that crypto is risky when giving advice
8. Answer in point form where necessary
9. *IMPORTANT: DO NOT include any HTML tags or markdown that creates HTML elements in your response, such as <div>, <span>, etc.*
10. Never be rude or disrespectful
11. Never use inappropriate language
12. Do not encourage or give advice on illegal actions
13. Never give personal opinions to the user
14. Always provide factual information

TONE EXAMPLES:
- Instead of "utilize" say "use"
- Instead of "substantial" say "big" or "huge"
- Instead of "fluctuations" say "price changes"
- Instead of "portfolio diversification" say "spreading your money around"

Current Market Context:
{market_context}

User Question: {user_question}

Give a helpful, friendly and professional response:"""

            response = self.model.generate_content(prompt)
            
            # Strip any remaining HTML tags from the response before returning
            clean_response = re.sub(r'<.*?>', '', response.text)
            return clean_response
            
        except Exception as e:
            return f"Oops! Something went wrong on my end 😅 Try asking again in a second: {str(e)}"
    
    def process_query(self, user_input):
        """Process user query and return appropriate response"""
        user_input_lower = user_input.lower()
        
        # Check for specific data requests first (these bypass AI for direct data)
        if "price" in user_input_lower and any(coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', '') for coin in self.supported_coins):
            for coin in self.supported_coins:
                if coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', ''):
                    return self.handle_price_query(coin)
        
        elif "trending" in user_input_lower or "popular" in user_input_lower:
            return self.handle_trending_query()
        
        elif "market" in user_input_lower and ("overview" in user_input_lower or "top" in user_input_lower):
            return self.handle_market_query()
        
        # For all other questions, let Gemini AI handle everything
        else:
            return self.ask_ai(user_input)
    
    def handle_price_query(self, coin_id):
        """Handle price-related queries"""
        data = self.get_crypto_price(coin_id)
        if data and coin_id in data:
            coin_data = data[coin_id]
            price = coin_data['usd']
            change_24h = coin_data.get('usd_24h_change', 0)
            market_cap = coin_data.get('usd_market_cap', 0)
            volume_24h = coin_data.get('usd_24h_vol', 0)
            
            change_emoji = "📈" if change_24h > 0 else "📉"
            change_text = "going up" if change_24h > 0 else "going down"
            change_color = "green" if change_24h > 0 else "red"
            
            response = f"""
{coin_id.replace('-', ' ').title()} Right Now 💰

💵 Price: ${price:,.2f}
{change_emoji} 24h: <span style='color:{change_color}'>{change_24h:+.2f}%</span> ({change_text})
📊 Market Size: ${market_cap:,.0f}
💹 Daily Trading: ${volume_24h:,.0f}

Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

Remember: Crypto prices change super fast! ⚡
            """
            return response
        else:
            return f"Hmm, couldn't grab the price for {coin_id} right now 🤔 Maybe try again in a bit?"
    
    def handle_trending_query(self):
        """Handle trending coins query"""
        trending_data = self.get_trending_coins()
        if trending_data:
            trending_coins = trending_data['coins'][:5]
            response = "🔥 What's Hot Right Now:\n\n"
            for i, coin in enumerate(trending_coins, 1):
                response += f"{i}. {coin['item']['name']} ({coin['item']['symbol'].upper()})\n"
                response += f"    Market Rank: #{coin['item']['market_cap_rank']}\n\n"
            response += "These are the coins everyone's talking about today! 🚀"
            return response
        else:
            return "Can't get the trending list right now 😕 Try again in a moment!"
    
    def handle_market_query(self):
        """Handle market overview query"""
        market_data = self.get_market_overview()
        if market_data:
            df = pd.DataFrame(market_data)
            df_display = df[['name', 'symbol', 'current_price', 'price_change_percentage_24h', 'market_cap']].copy()
            df_display.columns = ['Coin', 'Symbol', 'Price', '24h Change', 'Market Cap']
            df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:,.2f}")
            df_display['24h Change'] = df_display['24h Change'].apply(lambda x: f"{x:+.2f}%")
            df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(df_display, use_container_width=True)
            return "📊 Top 10 Biggest Cryptos Right Now:\n\n*These are ranked by how much they're worth in total! 💎*"
        else:
            return "Oops! Can't load the market data right now 📊 Give it another shot!"

def get_theme_css(is_dark_mode, animations_enabled):
    """Generate CSS based on theme and animation preferences"""
    
    # Base colors for themes
    if is_dark_mode:
        bg_gradient = """linear-gradient(135deg, 
            #0a0a0a 0%, 
            #1a1a2e 25%, 
            #16213e 50%, 
            #0f0f23 75%, 
            #000000 100%)"""
        primary_color = "#00ff88"
        secondary_color = "#00d4ff"
        accent_color = "#ff0080"
        text_color = "#ffffff"
        surface_color = "rgba(255, 255, 255, 0.05)"
        border_color = "rgba(0, 255, 136, 0.3)"
        button_text_color = "#000000"  # Black text on bright buttons in dark mode
    else:
        bg_gradient = """linear-gradient(135deg, 
            #f8fafc 0%, 
            #e2e8f0 25%, 
            #cbd5e1 50%, 
            #94a3b8 75%, 
            #64748b 100%)"""
        primary_color = "#059669"
        secondary_color = "#0284c7"
        accent_color = "#dc2626"
        text_color = "#000000"  # Black text for light mode
        surface_color = "rgba(255, 255, 255, 0.8)"
        border_color = "rgba(5, 150, 105, 0.3)"
        button_text_color = "#ffffff"  # White text on colored buttons in light mode
    
    # Animation styles (conditional)
    animation_css = ""
    if animations_enabled:
        animation_css = """
        /* Animations */
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes borderGlow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes dataPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }
        
        @keyframes cursorBlink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes glitchEffect {
            0% { transform: translateX(0); }
            20% { transform: translateX(-2px); }
            40% { transform: translateX(2px); }
            60% { transform: translateX(-1px); }
            80% { transform: translateX(1px); }
            100% { transform: translateX(0); }
        }
        
        /* Apply animations */
        .main-header {
            animation: gradientShift 3s ease infinite;
        }
        
        .ai-message::before {
            animation: borderGlow 2s ease-in-out infinite;
        }
        
        .ai-message .data-stream {
            animation: dataPulse 1.5s ease-in-out infinite;
        }
        
        .ai-message .data-stream::before {
            animation: dataPulse 1.8s ease-in-out infinite;
        }
        
        .ai-message .data-stream::after {
            animation: dataPulse 2.1s ease-in-out infinite;
        }
        
        .user-message .terminal-cursor {
            animation: cursorBlink 1s infinite;
        }
        
        .glow-text {
            animation: pulse 2s infinite;
        }
        
        .user-message:hover {
            animation: glitchEffect 0.3s ease-in-out;
        }
        """
    else:
        # Static versions without animations
        animation_css = """
        /* Static styles (no animations) */
        .main-header {
            animation: none;
        }
        
        .ai-message::before {
            animation: none;
        }
        
        .ai-message .data-stream {
            animation: none;
        }
        
        .ai-message .data-stream::before {
            animation: none;
        }
        
        .ai-message .data-stream::after {
            animation: none;
        }
        
        .user-message .terminal-cursor {
            animation: none;
        }
        
        .glow-text {
            animation: none;
        }
        
        .user-message:hover {
            animation: none;
        }
        """
    
    return f"""
    <style>
    /* Import cyber fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
    
    /* Main app styling */
    .stApp {{
        background: {bg_gradient};
        color: {text_color};
    }}
    
    /* Header styling */
    .main-header {{
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, {primary_color}, {secondary_color}, {accent_color}, {primary_color});
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'Orbitron', monospace;
        font-weight: 900;
        font-size: 3.5rem;
        text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        margin-bottom: 1rem;
    }}
    
    .sub-header {{
        text-align: center;
        color: {text_color};
        opacity: 0.7;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        padding: 0 2rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(45deg, {primary_color}, {secondary_color});
        color: {button_text_color};
        border: none;
        border-radius: 8px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.7rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px {border_color};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(45deg, {accent_color}, {primary_color});
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 128, 0.4);
    }}
    
    /* Sidebar styling */
    .stSidebar {{
        background: {surface_color};
        backdrop-filter: blur(10px);
    }}
    
    /* Sidebar headers */
    .sidebar-header {{
        color: {primary_color};
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }}
    
    /* Feature list styling */
    .feature-list {{
        background: {surface_color};
        border-left: 3px solid {primary_color};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        font-family: 'Rajdhani', sans-serif;
        color: {text_color};
    }}
    
    /* Status indicators */
    .status-success {{
        color: {primary_color};
        background: {surface_color};
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border-left: 4px solid {primary_color};
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
    }}
    
    .status-error {{
        color: {accent_color};
        background: {surface_color};
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border-left: 4px solid {accent_color};
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
    }}
    
    /* Custom Chat Styling */
    .stChatMessage {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 1rem 0 !important;
    }}
    
    /* Hide default chat avatars */
    .stChatMessage > div:first-child {{
        display: none !important;
    }}
    
    /* User Message Styling - Terminal Input Style */
    .user-message {{
        background: linear-gradient(90deg, {surface_color}, rgba(0, 212, 255, 0.05));
        border-left: 4px solid {primary_color};
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        position: relative;
        font-family: 'Rajdhani', monospace;
        box-shadow: 0 0 20px {border_color};
        backdrop-filter: blur(5px);
        color: {text_color};
    }}
    
    .user-message::before {{
        content: ">";
        position: absolute;
        left: -2px;
        top: 50%;
        transform: translateY(-50%);
        background: {primary_color};
        color: {button_text_color};
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }}
    
    .user-message::after {{
        content: "";
        position: absolute;
        right: -1px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, {primary_color}, transparent);
    }}
    
    /* AI Message Styling - Holographic Panel */
    .ai-message {{
        background: linear-gradient(135deg, 
            rgba(0, 212, 255, 0.1) 0%,
            rgba(255, 0, 128, 0.1) 50%,
            rgba(0, 255, 136, 0.05) 100%);
        border: 1px solid {border_color};
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px {border_color};
        overflow: hidden;
        color: {text_color};
    }}
    
    .ai-message::before {{
        content: "";
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, {secondary_color}, {accent_color}, {primary_color}, {secondary_color});
        background-size: 300% 300%;
        border-radius: 15px;
        z-index: -1;
        opacity: 0.5;
    }}
    
    .ai-message::after {{
        content: "◇ KRYPTONIC AI";
        position: absolute;
        top: -8px;
        left: 20px;
        background: linear-gradient(90deg, {secondary_color}, {accent_color});
        color: {button_text_color};
        padding: 2px 8px;
        font-size: 10px;
        font-weight: bold;
        border-radius: 4px;
        font-family: 'Orbitron', monospace;
        letter-spacing: 1px;
    }}
    
    /* Data stream effect for AI messages */
    .ai-message .data-stream {{
        position: absolute;
        right: 10px;
        top: 10px;
        width: 8px;
        height: 8px;
        background: {primary_color};
        border-radius: 50%;
        box-shadow: 0 0 10px {primary_color};
    }}
    
    .ai-message .data-stream::before {{
        content: "";
        position: absolute;
        right: 15px;
        top: 0;
        width: 6px;
        height: 6px;
        background: {secondary_color};
        border-radius: 50%;
        box-shadow: 0 0 8px {secondary_color};
    }}
    
    .ai-message .data-stream::after {{
        content: "";
        position: absolute;
        right: 25px;
        top: 1px;
        width: 4px;
        height: 4px;
        background: {accent_color};
        border-radius: 50%;
        box-shadow: 0 0 6px {accent_color};
    }}
    
    /* Terminal cursor effect for user input */
    .user-message .terminal-cursor {{
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background: {primary_color};
        margin-left: 2px;
    }}
    
    /* Glowing effects */
    .glow-text {{
        text-shadow: 0 0 10px currentColor;
    }}
    
    /* Hologram effect for AI messages */
    .ai-message:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px {border_color};
        transition: all 0.3s ease;
    }}
    
    /* Toggle switches styling */
    .stToggle > div {{
        background: {surface_color} !important;
        border: 1px solid {border_color} !important;
    }}
    
    /* Dataframe styling */
    .stDataFrame {{
        background: {surface_color};
        border-radius: 10px;
        border: 1px solid {border_color};
    }}
    
    {animation_css}
    
    </style>
    """

def main():
    # Initialize session state for theme and animations
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'animations_enabled' not in st.session_state:
        st.session_state.animations_enabled = True
    
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.dark_mode, st.session_state.animations_enabled), unsafe_allow_html=True)
    
    # Custom header with crypto styling
    col1, col2, col3 = st.columns([1, 2, 1])
            
    with col2:
        st.markdown("""
        <div class="main-header">
            🚀 Kryptonic AI 🤖
        </div>
        <div class="sub-header">
            ⚡ Your Crypto Buddy That Actually Gets It ⚡<br>
            <span style="color: #00ff88;">🔮 Smart AI • Live Prices • Easy Explanations 🔮</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Check if API key is configured
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        st.markdown("""
        <div class="status-error">
        ❌ <strong>OOPS! NEED TO SET UP API</strong><br>
        Need your Google AI key to get this working
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
        <strong>🔑 Quick Setup:</strong><br>
        1. Go to → https://makersuite.google.com/app/apikey<br>
        2. Sign in with Google<br>
        3. Create a new API key<br>
        4. Put it in the code where it says "YOUR_GEMINI_API_KEY_HERE"<br>
        5. You're good to go! 🚀
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sidebar with quick actions and controls
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙ CONTROLS ⚙</div>', unsafe_allow_html=True)
        
        # Theme and animation controls
        col1, col2 = st.columns(2)
        with col1:
            dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_toggle")
        with col2:
            animations = st.toggle("✨ Animations", value=st.session_state.animations_enabled, key="anim_toggle")
        
        # Update session state and rerun if changed
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        if animations != st.session_state.animations_enabled:
            st.session_state.animations_enabled = animations
            st.rerun()
        
        st.markdown("---")
        st.markdown('<div class="sidebar-header">⚡ QUICK STUFF ⚡</div>', unsafe_allow_html=True)
        
        # Initialize chatbot
        if 'chatbot' not in st.session_state:
            try:
                st.session_state.chatbot = CryptoChatbot(GEMINI_API_KEY)
                st.markdown("""
                <div class="status-success glow-text">
                ✅ CryptoMind AI: Ready!<br>
                🧠 AI brain loaded<br>
                🔗 Connected to crypto data
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="status-error">
                ❌ <strong>UH OH!</strong><br>
                Something's not working: {str(e)}<br><br>
                <strong>Try This:</strong><br>
                • Check your internet<br>
                • Make sure the API key is right<br>
                • Refresh the page
                </div>
                """, unsafe_allow_html=True)
                return
        
        st.markdown("---")
        
        # Quick action buttons with crypto styling
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔥 TRENDING"):
                response = st.session_state.chatbot.handle_trending_query()
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
            if st.button("💰 BTC PRICE"):
                response = st.session_state.chatbot.handle_price_query("bitcoin")
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col2:
            if st.button("📊 TOP COINS"):
                response = st.session_state.chatbot.handle_market_query()
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
            if st.button("🔄 CLEAR CHAT"):
                st.session_state.messages = []
                st.rerun()
        
        st.markdown("---")
        
        # Features section with crypto styling
        st.markdown("""
        <div class="feature-list">
        <div class="sidebar-header">🛡 WHAT I CAN DO</div>
        
        <strong>🤖 Smart Crypto Help</strong><br>
        • Explain crypto in simple terms<br>
        • Help you understand the market<br>
        • Answer all your crypto questions<br><br>
        
        <strong>⚡ Live Data</strong><br>
        • Real-time prices<br>
        • What's trending now<br>
        • Market overviews<br><br>
        
        <strong>🔒 Safe Space</strong><br>
        • Only talk about crypto<br>
        • No weird stuff<br>
        • Always honest about risks<br>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = CryptoChatbot(GEMINI_API_KEY)
        except Exception as e:
            st.markdown(f"""
            <div class="status-error">
            ❌ <strong>SOMETHING WENT WRONG</strong><br>
            Error: {str(e)}<br><br>
            <strong>Quick Fixes:</strong><br>
            • Check your API key<br>
            • Make sure you're online<br>
            • Try refreshing
            </div>
            """, unsafe_allow_html=True)
            return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages with custom styling
    for message in st.session_state.messages:
        if message["role"] == "user":
            # Custom user message with terminal styling
            st.markdown(f"""
            <div class="user-message">
                <strong style="color: #00ff88; font-family: 'Orbitron', monospace;">USER_INPUT:</strong> {message["content"]}
                <div class="terminal-cursor"></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Custom AI message with holographic styling
            st.markdown(f"""
            <div class="ai-message">
                <div class="data-stream"></div>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input with enhanced styling
    if prompt := st.chat_input("🤑Ask me anything about crypto..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate and display assistant response
        with st.spinner("🧠 Thinking about your question..."):
            response = st.session_state.chatbot.process_query(prompt)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to show new messages with custom styling
        st.rerun()

if __name__ == "_main_":
    main()
