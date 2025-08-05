import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import google.generativeai as genai
import re
from typing import List, Dict
import time

# --- Define Colors and Styles ---
BG_GRADIENT_COLOR_1 = "#2a1a4a"
BG_GRADIENT_COLOR_2 = "#1e1538"
BG_GRADIENT_COLOR_3 = "#161028"
BG_GRADIENT_COLOR_4 = "#0f0818"
BG_GRADIENT_COLOR_5 = "#000000"

TEXT_COLOR = "white"
BUTTON_BG_COLOR = "white"
BUTTON_TEXT_COLOR = "#1f2937"
HIGHLIGHT_GRADIENT_START = "#8b5cf6"
HIGHLIGHT_GRADIENT_MIDDLE = "#3b82f6"
HIGHLIGHT_GRADIENT_END = "#ec4899"
STARS_COLOR = "#fbbf24"

# Chatbot specific colors
PRIMARY_COLOR = "#00ff88"
SECONDARY_COLOR = "#00d4ff"
ACCENT_COLOR = "#ff0080"
SURFACE_COLOR = "rgba(255, 255, 255, 0.05)"
BORDER_COLOR = "rgba(0, 255, 136, 0.3)"

# API Configuration
GEMINI_API_KEY = "AIzaSyDEgi35dDHu0BfHas34-QDy0NjXrAQP2nM"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Kryptonic AI - Your Crypto Guide",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Expanded list of supported languages ---
LANGUAGE_OPTIONS = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Chinese (Simplified)': 'zh-Hans',
    'Arabic': 'ar',
    'Hindi': 'hi',
    'Bengali': 'bn',
    'Indonesian': 'id',
    'Dutch': 'nl',
    'Polish': 'pl',
    'Thai': 'th',
    'Turkish': 'tr',
    'Vietnamese': 'vi',
    'Romanian': 'ro',
    'Ukrainian': 'uk'
}

def translate_text(text: str, target_language_code: str) -> str:
    """
    Translates text to a target language using the Gemini API.
    
    Args:
        text (str): The text to be translated.
        target_language_code (str): The language code (e.g., 'en', 'es', 'fr').
        
    Returns:
        str: The translated text, or a fallback message if translation fails.
    """
    if target_language_code == 'en':
        return text

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        prompt = f"""
        Translate the following text into the language with the code '{target_language_code}':
        
        TEXT TO TRANSLATE:
        "{text}"
        
        Translated Text:
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return f"Translation failed. Original response: {text}"

def remove_html_tags(text):
    """Remove all HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

class CryptoChatbot:
    """A chatbot class that fetches real-time crypto data and answers user queries."""
    def __init__(self, gemini_api_key):  # Fixed: __init__ instead of _init_
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        
        # Initialize the generative model
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            try:
                self.model = genai.GenerativeModel('gemini-1.0-pro')
            except Exception:
                self.model = genai.GenerativeModel('models/gemini-pro')
        
        self.supported_coins = [
            'bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana',
            'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'polygon',
            'ripple', 'litecoin', 'stellar', 'monero', 'tron'
        ]

        # CSV data functionality removed as requested by the user.
        self.csv_data = pd.DataFrame()
    
    def get_crypto_price(self, coin_id):
        """Get current price and basic info for a cryptocurrency."""
        try:
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching data for {coin_id}: {e}")
            return None
    
    def get_trending_coins(self):
        """Get trending cryptocurrencies."""
        try:
            url = f"{COINGECKO_BASE_URL}/search/trending"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching trending coins: {e}")
            return None
    
    def get_market_overview_df(self):
        """Get top cryptocurrencies by market cap and return a DataFrame."""
        try:
            url = f"{COINGECKO_BASE_URL}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 10,
                'page': 1,
                'sparkline': 'false'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            market_data = response.json()
            
            df = pd.DataFrame(market_data)
            df_display = df[['name', 'symbol', 'current_price', 'price_change_percentage_24h', 'market_cap']].copy()
            df_display.columns = ['Coin', 'Symbol', 'Price', '24h Change', 'Market Cap']
            df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:,.2f}")
            df_display['24h Change'] = df_display['24h Change'].apply(lambda x: f"{x:+.2f}%")
            df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"${x:,.0f}")
            
            return df_display
        except Exception as e:
            st.error(f"Error fetching market overview: {e}")
            return pd.DataFrame()
            
    def get_current_market_data(self, num_top_coins=5, num_trending_coins=3):
        """Get current market data to provide context to AI."""
        market_data = self.get_market_overview_df()
        trending_data = self.get_trending_coins()
        
        context = "Current Crypto Market Data:\n"
        
        if not market_data.empty:
            context += f"Top {num_top_coins} Cryptocurrencies by Market Cap:\n"
            for i, row in market_data.head(num_top_coins).iterrows():
                context += f"{i+1}. {row['Coin']} ({row['Symbol']}): {row['Price']} ({row['24h Change']})\n"
        
        if trending_data and 'coins' in trending_data:
            context += f"\nTrending Coins (Top {num_trending_coins}):\n"
            for i, coin in enumerate(trending_data['coins'][:num_trending_coins], 1):
                context += f"{i}. {coin['item']['name']} ({coin['item']['symbol']})\n"
        
        return context
    
    def build_conversation_context(self, messages):
        """Build conversation context from message history."""
        if not messages:
            return ""
        
        context = "Previous conversation context:\n"
        # Only include the last 10 messages to avoid token limits
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for msg in recent_messages:
            if msg["role"] == "user":
                context += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant" and msg.get("type") != "dataframe":
                # Truncate long responses for context
                content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                context += f"Kryptonic: {content}\n"
        
        return context

def ask_ai(self, user_question, conversation_history):
        """
        Ask Gemini AI about cryptocurrency topics with conversation memory.
        
        The model now generates a response in English, which is then translated.
        This removes ambiguity from the prompt and ensures consistent translation.
        """
        try:
            market_context = self.get_current_market_data()
            conversation_context = self.build_conversation_context(conversation_history)
            
            # Check if this is the first interaction
            is_first_interaction = len([msg for msg in conversation_history if msg["role"] == "user"]) == 0
            
            base_prompt = f"""You are "Kryptonic," a super chill Gen Z crypto expert who talks like a real person having a casual conversation with a friend. You're knowledgeable but keep it fun and natural.

CONVERSATION STYLE:
- Talk like you're texting a friend - use "heyyyy", "yooo", "omggg", "ngl", "fr fr"
- Be conversational and flowing - don't jump straight into facts
- Start responses naturally like: "yooo what's good!", "heyy!", "omg yes!", "ngl that's a great question!"
- Mix casual chat with helpful info
- Use emojis naturally (not too many though)
- Keep it real and relatable

PERSONALITY:
- Friendly, enthusiastic bestie energy
- Smart but not show-offy about it  
- Honest about crypto being risky
- Makes complex stuff simple
- Actually cares about helping people

{"FIRST TIME MEETING: Introduce yourself naturally like meeting a new friend - be excited and welcoming!" if is_first_interaction else "CONTINUING CHAT: Keep the conversation flowing naturally, reference what we talked about before"}

RESPONSE FLOW:
1. Start with a natural greeting/reaction
2. Then smoothly transition to answering their question
3. Maybe ask something back to keep convo going
4. Keep it under 150 words total

HANDLE DIFFERENT SITUATIONS:
- If they ask who you are: "yooo I'm Kryptonic! I'm like your crypto bestie who helps you understand all this wild crypto stuff"
- If completely off-topic: "heyy that's cool but I'm all about crypto! what crypto stuff you wanna know about?"
- Basic thanks/bye: respond naturally but guide back to crypto

IMPORTANT RULES:
- No HTML tags or markdown formatting
- Be encouraging but always mention crypto risks
- Keep responses conversational and flowing
- Don't be preachy or formal
- Actually sound like a real person

{conversation_context}

Current Market Context:
{market_context}

User Question: {user_question}

Respond naturally and conversationally:"""

            response = self.model.generate_content(base_prompt)
            
            clean_response = remove_html_tags(response.text)
            return clean_response
            
        except Exception as e:
            return f"Oops! Something went wrong on my end 😅 Try asking again in a second: {str(e)}"
    
    def handle_price_query(self, coin_id):
        """Handle price-related queries - same as app.py style"""
        data = self.get_crypto_price(coin_id)
        if data and coin_id in data:
            coin_data = data[coin_id]
            price = coin_data.get('usd', 0)
            change_24h = coin_data.get('usd_24h_change', 0)
            market_cap = coin_data.get('usd_market_cap', 0)
            volume_24h = coin_data.get('usd_24h_vol', 0)
            
            response_str = f"""{coin_id.replace('-', ' ').title()} Right Now 💰

💵 Price: ${price:,.2f}
{"📈" if change_24h > 0 else "📉"} 24h: {change_24h:+.2f}%
📊 Market Cap: ${market_cap:,.0f}
💹 Daily Trading: ${volume_24h:,.0f}

Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

Remember: Crypto prices change super fast! ⚡"""
            return response_str
        else:
            return f"Hmm, couldn't grab the price for {coin_id} right now 🤔 Maybe try again in a bit?"
    
    def handle_trending_query(self):
        """Handle trending coins query - same as app.py style"""
        trending_data = self.get_trending_coins()
        if trending_data and 'coins' in trending_data:
            trending_coins = trending_data['coins'][:5]
            response = "🔥 What's Hot Right Now:\n\n"
            for i, coin in enumerate(trending_coins, 1):
                response += f"{i}. {coin['item']['name']} ({coin['item']['symbol'].upper()})\n"
                response += f"    Market Rank: #{coin['item']['market_cap_rank']}\n\n"
            response += "These are the coins everyone's talking about today! 🚀"
            return response
        else:
            return "Can't get the trending list right now 😕 Try again in a moment!"
    
    def process_query(self, user_input, language_code, conversation_history):
        """Process user query and return appropriate response."""
        user_input_lower = user_input.lower()
        
        # 1. Check for price queries
        if "price" in user_input_lower and any(coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', '') for coin in self.supported_coins):
            for coin in self.supported_coins:
                if coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', ''):
                    response = self.handle_price_query(coin)
                    return translate_text(response, language_code)
        
        # 2. Check for trending queries
        elif "trending" in user_input_lower or "popular" in user_input_lower:
            response = self.handle_trending_query()
            return translate_text(response, language_code)
        
        # 3. Check for market overview queries
        elif "market" in user_input_lower and ("overview" in user_input_lower or "top" in user_input_lower):
            return "market_overview_requested"  # Special flag for handling in main function
        
        # 4. Fallback to the generative model for all other questions
        else:
            # The AI model generates a response in English.
            response = self.ask_ai(user_input, conversation_history)
            # This response is then translated into the selected language.
            return translate_text(response, language_code)

def get_theme_css(is_dark_mode, animations_enabled):
    """Generate CSS based on theme and animation preferences."""
    
    if is_dark_mode:
        bg_gradient = f"linear-gradient(135deg, {BG_GRADIENT_COLOR_1}, {BG_GRADIENT_COLOR_2}, {BG_GRADIENT_COLOR_3}, {BG_GRADIENT_COLOR_4}, {BG_GRADIENT_COLOR_5})"
        primary_color_chat = PRIMARY_COLOR
        secondary_color_chat = SECONDARY_COLOR
        accent_color_chat = ACCENT_COLOR
        text_color_chat = TEXT_COLOR
        surface_color_chat = SURFACE_COLOR
        border_color_chat = BORDER_COLOR
        button_text_color_chat = "#000000"
        sidebar_header_color = primary_color_chat
        main_text_color = TEXT_COLOR
        sidebar_text_color = TEXT_COLOR
        toggle_label_color = TEXT_COLOR
    else:
        bg_gradient = "linear-gradient(135deg, #f0f2f6, #e9eef2)"
        primary_color_chat = "#059669"
        secondary_color_chat = "#0284c7"
        accent_color_chat = "#dc2626"
        text_color_chat = "#000000"
        surface_color_chat = "rgba(255, 255, 255, 0.9)"
        border_color_chat = "rgba(5, 150, 105, 0.5)"
        button_text_color_chat = "#ffffff"
        sidebar_header_color = "#000000"
        main_text_color = "#000000"
        sidebar_text_color = "#000000"
        toggle_label_color = "#000000"
    
    animation_css = ""
    if animations_enabled:
        animation_css = """
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
            0%, 100% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.2); opacity: 0.5; }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px); }
            25% { transform: translateY(-15px) translateX(5px); }
            50% { transform: translateY(-5px) translateX(-5px); }
            75% { transform: translateY(-20px) translateX(8px); }
        }
        @keyframes glitchEffect {
            0% { transform: translateX(0); }
            20% { transform: translateX(-2px); }
            40% { transform: translateX(2px); }
            60% { transform: translateX(-1px); }
            80% { transform: translateX(1px); }
            100% { transform: translateX(0); }
        }
        .main-header { animation: gradientShift 3s ease infinite; }
        .ai-message::before { animation: borderGlow 2s ease-in-out infinite; }
        .ai-message .data-stream { animation: dataPulse 1.5s ease-in-out infinite; }
        .ai-message .data-stream::before { animation: dataPulse 1.8s ease-in-out infinite; }
        .ai-message .data-stream::after { animation: dataPulse 2.1s ease-in-out infinite; }
        .user-message .terminal-cursor { animation: cursorBlink 1s infinite; }
        .glow-text { animation: pulse 2s infinite; }
        .user-message:hover { animation: glitchEffect 0.3s ease-in-out; }
        .glow-orb { animation: pulse 4s ease-in-out infinite; }
        .crystal-placeholder { animation: float 8s ease-in-out infinite; }
        """
    else:
        animation_css = """
        .main-header { animation: none; }
        .ai-message::before { animation: none; }
        .ai-message .data-stream { animation: none; }
        .ai-message .data-stream::before { animation: none; }
        .ai-message .data-stream::after { animation: none; }
        .user-message .terminal-cursor { animation: none; }
        .glow-text { animation: none; }
        .user-message:hover { animation: none; }
        .glow-orb { animation: none; }
        .crystal-placeholder { animation: none; }
        """
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    body {{
        font-family: 'Inter', sans-serif;
        background: {bg_gradient};
        color: {main_text_color};
        overflow-x: hidden;
        min-height: 100vh;
        position: relative;
    }}
    .stApp {{
        background: {bg_gradient};
        color: {main_text_color};
        font-family: 'Inter', sans-serif;
    }}
    .main .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 0;
        position: relative;
        z-index: 20;
    }}
    .logo-section {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}
    .logo-shield {{
        width: 45px;
        height: 45px;
        background: linear-gradient(135deg, #4338ca, #7c3aed, {PRIMARY_COLOR});
        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }}
    .logo-shield::before {{
        content: '⚔';
        font-size: 18px;
        position: absolute;
    }}
    .logo-text {{
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: {main_text_color};
    }}
    .nav-links-container {{
        display: flex;
        align-items: center;
        gap: 2.5rem;
    }}
    .stars-text {{
        color: {STARS_COLOR};
        font-size: 0.9rem;
        letter-spacing: 2px;
        white-space: nowrap;
    }}
    .main-content {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 2rem;
        position: relative;
        z-index: 10;
        max-width: 1000px;
        margin: 0 auto;
        min-height: calc(100vh - 120px);
    }}
    .hero-title {{
        font-family: 'Inter', sans-serif;
        font-size: clamp(2.8rem, 7vw, 5.5rem);
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 3rem;
        letter-spacing: -0.02em;
        color: {main_text_color};
    }}
    .hero-title .highlight {{
        background: linear-gradient(135deg, {HIGHLIGHT_GRADIENT_START} 0%, {HIGHLIGHT_GRADIENT_MIDDLE} 50%, {HIGHLIGHT_GRADIENT_END} 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease-in-out infinite;
    }}
    .glow-orb {{
        position: absolute;
        border-radius: 50%;
        filter: blur(40px);
        opacity: 0.3;
        pointer-events: none;
        animation: pulse 4s ease-in-out infinite;
    }}
    .glow-1 {{ top: 20%; left: 10%; width: 200px; height: 200px; background: radial-gradient(circle, {HIGHLIGHT_GRADIENT_START} 0%, transparent 70%); animation-delay: -1s; }}
    .glow-2 {{ bottom: 30%; right: 15%; width: 150px; height: 150px; background: radial-gradient(circle, {HIGHLIGHT_GRADIENT_MIDDLE} 0%, transparent 70%); animation-delay: -2s; }}
    .glow-3 {{ top: 60%; left: 20%; width: 180px; height: 180px; background: radial-gradient(circle, {HIGHLIGHT_GRADIENT_END} 0%, transparent 70%); animation-delay: -3s; }}
    .crystal-placeholder {{
        position: absolute;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.8), rgba(59, 130, 246, 0.9), rgba(236, 72, 153, 0.8));
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        opacity: 0.6;
        pointer-events: none;
        z-index: 5;
        animation: float 8s ease-in-out infinite;
    }}
    .crystal-diamond-p {{ top: 15%; left: 15%; width: 120px; height: 120px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); animation-delay: -2s; }}
    .crystal-octagon-p {{ top: 25%; right: 12%; width: 100px; height: 100px; clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%); animation-delay: -4s; }}
    .crystal-sphere-p {{ bottom: 25%; right: 15%; width: 80px; height: 80px; border-radius: 50%; animation-delay: -1s; }}
    .crystal-ring-p {{ bottom: 20%; left: 8%; width: 150px; height: 150px; border-radius: 50%; border: 20px solid transparent; background-clip: padding-box; background: conic-gradient(from 0deg, rgba(139, 92, 246, 0.6) 0deg, rgba(59, 130, 246, 0.8) 120deg, rgba(236, 72, 153, 0.6) 240deg, rgba(139, 92, 246, 0.6) 360deg); animation-delay: -3s; }}
    .crystal-cube-p {{ top: 45%; left: 3%; width: 70px; height: 70px; animation-delay: -5s; }}
    .crystal-triangle-p {{ top: 55%; right: 8%; width: 90px; height: 90px; clip-path: polygon(50% 0%, 0% 100%, 100% 100%); animation-delay: -6s; }}
    
    /* Chatbot specific styling */
    .chat-header {{
        text-align: center; padding: 2rem 0;
        background: linear-gradient(90deg, {PRIMARY_COLOR}, {SECONDARY_COLOR}, {ACCENT_COLOR}, {PRIMARY_COLOR});
        background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-family: 'Orbitron', monospace; font-weight: 900; font-size: 3.5rem;
        text-shadow: 0 0 30px rgba(5, 150, 105, 0.5); margin-bottom: 1rem;
    }}
    .sub-header {{
        text-align: center; color: {main_text_color}; opacity: 0.7;
        font-family: 'Rajdhani', sans-serif; font-size: 1.2rem;
        margin-bottom: 2rem; padding: 0 2rem;
    }}
    .stSidebar {{ background: {surface_color_chat}; backdrop-filter: blur(10px); }}
    .sidebar-header {{
        color: {sidebar_header_color}; font-family: 'Orbitron', monospace;
        font-weight: 700; font-size: 1.3rem; text-align: center;
        margin-bottom: 1rem; text-shadow: 0 0 10px rgba(5, 150, 105, 0.5);
    }}
    .feature-list {{
        background: {surface_color_chat}; border-left: 3px solid {primary_color_chat};
        padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0;
        font-family: 'Rajdhani', sans-serif; color: {sidebar_text_color};
    }}
    .status-success {{
        color: {primary_color_chat}; background: {surface_color_chat}; padding: 0.5rem 1rem;
        border-radius: 6px; border-left: 4px solid {primary_color_chat};
        font-family: 'Rajdhani', sans-serif; font-weight: 600;
    }}
    .status-error {{
        color: {accent_color_chat}; background: {surface_color_chat}; padding: 0.5rem 1rem;
        border-radius: 6px; border-left: 4px solid {accent_color_chat};
        font-family: 'Rajdhani', sans-serif; font-weight: 600;
    }}
    
    /* Fix toggle label colors for light mode */
    .stToggle label, .stSelectbox label {{
        color: {toggle_label_color} !important;
    }}
    .stSidebar .stMarkdown {{
        color: {sidebar_text_color} !important;
    }}
    .stSidebar p {{
        color: {sidebar_text_color} !important;
    }}
    .stSidebar div[data-testid="stMarkdownContainer"] {{
        color: {sidebar_text_color} !important;
    }}
    
    .stChatMessage {{ background: transparent !important; border: none !important; padding: 0 !important; margin: 1rem 0 !important; }}
    .stChatMessage > div:first-child {{ display: none !important; }}
    .user-message {{
        background: {surface_color_chat};
        border-left: 4px solid {primary_color_chat}; border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem; margin: 1rem 0; position: relative;
        font-family: 'Rajdhani', monospace; box-shadow: 0 0 20px {border_color_chat};
        backdrop-filter: blur(5px); color: {text_color_chat};
    }}
    .user-message::before {{
        content: ">"; position: absolute; left: -2px; top: 50%; transform: translateY(-50%);
        background: {primary_color_chat}; color: {button_text_color_chat}; width: 20px;
        height: 20px; border-radius: 50%; display: flex; align-items: center;
        justify-content: center; font-weight: bold; font-size: 12px;
        box-shadow: 0 0 10px rgba(5, 150, 105, 0.5);
    }}
    .user-message::after {{
        content: ""; position: absolute; right: -1px; top: 0; bottom: 0;
        width: 2px; background: linear-gradient(180deg, {primary_color_chat}, transparent);
    }}
    .ai-message {{
        background: {surface_color_chat};
        border: 1px solid {border_color_chat}; border-radius: 15px;
        padding: 1.5rem; margin: 1rem 0; position: relative;
        backdrop-filter: blur(10px); box-shadow: 0 8px 32px {border_color_chat};
        overflow: hidden; color: {text_color_chat};
    }}
    .ai-message::before {{
        content: ""; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px;
        background: linear-gradient(45deg, {secondary_color_chat}, {accent_color_chat}, {primary_color_chat}, {secondary_color_chat});
        background-size: 300% 300%; border-radius: 15px; z-index: -1; opacity: 0.5;
    }}
    .ai-message::after {{
        content: "◇ KRYPTONIC AI"; position: absolute; top: -8px; left: 20px;
        background: linear-gradient(90deg, {secondary_color_chat}, {accent_color_chat});
        color: {button_text_color_chat}; padding: 2px 8px; font-size: 10px;
        font-weight: bold; border-radius: 4px; font-family: 'Orbitron', monospace;
        letter-spacing: 1px;
    }}
    .ai-message .data-stream {{
        position: absolute; right: 10px; top: 10px; width: 8px; height: 8px;
        background: {primary_color_chat}; border-radius: 50%; box-shadow: 0 0 10px {primary_color_chat};
    }}
    .ai-message .data-stream::before {{
        content: ""; position: absolute; right: 15px; top: 0; width: 6px; height: 6px;
        background: {secondary_color_chat}; border-radius: 50%; box-shadow: 0 0 8px {secondary_color_chat};
    }}
    .ai-message .data-stream::after {{
        content: ""; position: absolute; right: 25px; top: 1px; width: 4px; height: 4px;
        background: {accent_color_chat}; border-radius: 50%; box-shadow: 0 0 6px {accent_color_chat};
    }}
    .user-message .terminal-cursor {{
        display: inline-block; width: 2px; height: 1.2em;
        background: {primary_color_chat}; margin-left: 2px;
    }}
    .glow-text {{ text-shadow: 0 0 10px currentColor; }}
    .ai-message:hover {{ transform: translateY(-2px); box-shadow: 0 12px 40px {border_color_chat}; transition: all 0.3s ease; }}
    .stToggle > div {{ background: {surface_color_chat} !important; border: 1px solid {border_color_chat} !important; }}
    .stDataFrame {{ background: {surface_color_chat}; border-radius: 10px; border: 1px solid {border_color_chat}; }}
    .stButton > button {{
        background: linear-gradient(45deg, {primary_color_chat}, {secondary_color_chat});
        color: {button_text_color_chat}; border: none; border-radius: 8px;
        font-family: 'Rajdhani', sans-serif; font-weight: 600; font-size: 1rem;
        padding: 0.7rem 1.5rem; transition: all 0.3s ease;
        box-shadow: 0 4px 15px {border_color_chat}; text-transform: uppercase; letter-spacing: 1px;
    }}
    .stButton > button:hover {{
        background: linear-gradient(45deg, {accent_color_chat}, {primary_color_chat});
        transform: translateY(-2px); box-shadow: 6px 20px rgba(255, 0, 128, 0.4);
    }}

    /* Photosensitivity Warning Modal */
    .modal-overlay {{
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.8); z-index: 1000;
        display: flex; justify-content: center; align-items: center;
    }}
    .modal-content {{
        background: {BG_GRADIENT_COLOR_2}; padding: 2rem; border-radius: 15px;
        max-width: 500px; text-align: center;
        border: 2px solid {ACCENT_COLOR}; box-shadow: 0 0 30px {ACCENT_COLOR};
        display: flex; flex-direction: column; gap: 1rem;
    }}
    .modal-title {{
        color: {ACCENT_COLOR}; font-family: 'Orbitron', monospace;
        font-size: 1.8rem; margin-bottom: 0.5rem;
    }}
    .modal-text {{
        color: {TEXT_COLOR}; font-family: 'Rajdhani', sans-serif;
        font-size: 1rem; margin-bottom: 1rem;
    }}
    .modal-buttons {{
        display: flex; justify-content: center; gap: 1rem;
    }}
    .modal-buttons .stButton > button {{
        background: {ACCENT_COLOR}; color: white;
        border: none; border-radius: 8px; padding: 0.7rem 1.5rem;
        font-family: 'Rajdhani', sans-serif; font-weight: 600;
        box-shadow: none;
    }}
    .modal-buttons .stButton > button:hover {{
        background: linear-gradient(45deg, {accent_color_chat}, {primary_color_chat});
        transform: translateY(-2px);
    }}
    .modal-buttons .stButton:last-child > button {{
        background: transparent; color: {TEXT_COLOR};
        border: 2px solid {TEXT_COLOR}; padding: 0.7rem 1.5rem;
        font-family: 'Rajdhani', sans-serif;
        box-shadow: none;
    }}
    .modal-buttons .stButton:last-child > button:hover {{
        background: {TEXT_COLOR};
        color: {BG_GRADIENT_COLOR_2};
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .main .block-container {{ padding-left: 1.5rem; padding-right: 1.5rem; }}
        .header-container {{ flex-direction: column; gap: 1rem; }}
        .nav-links-container {{ gap: 1.5rem; }}
        .hero-title {{ font-size: 3rem; margin-bottom: 2rem; }}
        .crystal-placeholder, .glow-orb {{ transform: scale(0.7); }}
        .modal-content {{ width: 90%; padding: 1.5rem; }}
        .modal-buttons {{ flex-direction: column; gap: 0.5rem; }}
    }}
    @media (max-width: 480px) {{
        .main .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        .logo-text {{ font-size: 1.2rem; }}
        .nav-links-container {{ flex-wrap: wrap; justify-content: center; gap: 1rem; }}
        .hero-title {{ font-size: 2.2rem; }}
        .crystal-placeholder, .glow-orb {{ display: none; }}
        .modal-title {{ font-size: 1.5rem; }}
        .modal-text {{ font-size: 0.9rem; }}
    }}
    
    {animation_css}
    </style>
    """

def welcome_page():
    # --- Ambient Glow Effects and Crystal Shapes ---
    st.markdown(f'<div class="glow-orb glow-1"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glow-orb glow-2"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glow-orb glow-3"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-diamond-p"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-octagon-p"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-sphere-p"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-ring-p"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-cube-p"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="crystal-placeholder crystal-triangle-p"></div>', unsafe_allow_html=True)

    # --- Header Section ---
    header_cols = st.columns([1, 2, 1])

    with header_cols[0]:
        st.markdown(
            """
            <div class="logo-section">
                <div class="logo-shield"></div>
                <div class="logo-text">CRYPTO KNIGHT</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_cols[1]:
        nav_cols = st.columns([1, 1, 1])
        with nav_cols[0]:
            if st.button("LOG IN", key="nav_login"):
                st.session_state.page = "login"
        with nav_cols[1]:
            st.markdown(f'<span class="stars-text">★★★★★</span>', unsafe_allow_html=True)
        with nav_cols[2]:
            if st.button("ABOUT", key="nav_about"):
                st.session_state.page = "about"

    with header_cols[2]:
        if st.button("Sign up →", key="signup_button"):
            st.session_state.page = "signup"

    # --- Main Content (Hero Section) ---
    st.markdown(
        f"""
        <div class="main-content">
            <h1 class="hero-title">
                Welcome to <span class="highlight">Crypto Knight</span>,<br>
                Your crypto guide, where<br>
                <span class="highlight">futures collide</span>
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Start a chat button ---
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.button("Start a chat", key="get_started_btn"):
        st.session_state.page = "chatbot"
        # Reset the modal state to ensure it shows up when entering the chat page
        st.session_state.show_animation_warning = True
        st.session_state.modal_shown_time = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def show_animation_warning_modal():
    """Displays a modal warning for photosensitive users with native Streamlit buttons."""
    # Check the state variable, which is now managed by the main() function's timer
    if st.session_state.show_animation_warning:
        # Create a container for the modal overlay
        modal_container = st.container()
        with modal_container:
            st.markdown(
                """
                <div class="modal-overlay">
                    <div class="modal-content">
                        <div class="modal-title">⚠ Photosensitivity Warning</div>
                        <div class="modal-text">
                            This application contains animations and flashing effects that may affect users who are photosensitive.
                            You can turn them off by switching it off in the sidebar.
                        </div>
                        <div class="modal-buttons">
                """,
                unsafe_allow_html=True
            )
            
            # Use columns for buttons to be side-by-side
            col1, col2 = st.columns(2)
            with col1:
                # Use a specific key for this button
                if st.button("Turn Animations Off", key="disable_animations_modal_btn"):
                    st.session_state.animations_enabled = False
                    st.session_state.show_animation_warning = False
                    st.session_state.modal_shown_time = None
                    st.rerun()
            with col2:
                # Use a specific key for this button
                if st.button("Dismiss", key="dismiss_modal_btn"):
                    st.session_state.show_animation_warning = False
                    st.session_state.modal_shown_time = None
                    st.rerun()

            st.markdown(
                """
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def chatbot_page():
    # Show the photosensitivity warning if it hasn't been dismissed
    show_animation_warning_modal()

    # --- Custom Header with crypto styling ---
    st.markdown("""
    <div style='text-align: center;'>
    <h1 class="chat-header">
        🚀 Kryptonic AI 🤖
    </h1>
    <div class="sub-header">
        ⚡ Your Crypto Buddy That Actually Gets It ⚡<br>
        <span style="color: #059669;">🔮 Smart AI • Live Prices • Easy Explanations 🔮</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Sidebar with quick actions and controls ---
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙ CONTROLS ⚙</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_toggle")
        with col2:
            animations = st.toggle("✨ Animations", value=st.session_state.animations_enabled, key="anim_toggle")
        
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        if animations != st.session_state.animations_enabled:
            st.session_state.animations_enabled = animations
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="sidebar-header">🌐 LANGUAGE 🌐</div>', unsafe_allow_html=True)
        
        # Use the expanded LANGUAGE_OPTIONS dictionary
        current_lang_name = next((name for name, code in LANGUAGE_OPTIONS.items() if code == st.session_state.selected_lang_code), 'English')
        default_index = list(LANGUAGE_OPTIONS.keys()).index(current_lang_name)
        selected_lang_name = st.selectbox(
            "Select Response Language",
            list(LANGUAGE_OPTIONS.keys()),
            index=default_index
        )
        
        # Update session state with the new language code
        st.session_state.selected_lang_code = LANGUAGE_OPTIONS[selected_lang_name]

        st.markdown("---")
        st.markdown('<div class="sidebar-header">⚡ QUICK STUFF ⚡</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔥 TRENDING"):
                response = st.session_state.chatbot.handle_trending_query()
                translated_response = translate_text(response, st.session_state.selected_lang_code)
                st.session_state.messages.append({"role": "assistant", "content": translated_response})
                st.rerun()
            
            if st.button("💰 BTC PRICE"):
                response = st.session_state.chatbot.handle_price_query("bitcoin")
                translated_response = translate_text(response, st.session_state.selected_lang_code)
                st.session_state.messages.append({"role": "assistant", "content": translated_response})
                st.rerun()
        
        with col2:
            if st.button("📊 TOP COINS"):
                # Handle market overview properly
                message_text = "📊 Top 10 Biggest Cryptos Right Now:\n\n*These are ranked by how much they're worth in total! 💎*"
                translated_message = translate_text(message_text, st.session_state.selected_lang_code)
                
                df = st.session_state.chatbot.get_market_overview_df()
                
                if not df.empty:
                    st.session_state.messages.append({"role": "assistant", "content": translated_message, "type": "text"})
                    st.session_state.messages.append({"role": "assistant", "content": df, "type": "dataframe"})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": translate_text("Oops! Can't load the market data right now 📊 Give it another shot!", st.session_state.selected_lang_code), "type": "text"})
                
                st.rerun()
            
            if st.button("🔄 CLEAR CHAT"):
                st.session_state.messages = []
                st.rerun()
        
        st.markdown("---")
        
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
    
    # Display chat messages with custom styling
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong style="color: #00ff88; font-family: 'Orbitron', monospace;">USER_INPUT:</strong> {message["content"]}
                <div class="terminal-cursor"></div>
            </div>
            """, unsafe_allow_html=True)
        else: # role == "assistant"
            if message.get("type") == "dataframe":
                st.dataframe(message["content"], use_container_width=True)
            else:
                st.markdown(f"""
                <div class="ai-message">
                    <div class="data-stream"></div>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input with enhanced styling
    if prompt := st.chat_input("🤑Ask me anything about crypto..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display the user's message
        st.markdown(f"""
        <div class="user-message">
            <strong style="color: #00ff88; font-family: 'Orbitron', monospace;">USER_INPUT:</strong> {prompt}
            <div class="terminal-cursor"></div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("🧠 Thinking about your question..."):
            # Pass the conversation history to process_query
            # Pass the language code from session state to the processing function
            response = st.session_state.chatbot.process_query(prompt, st.session_state.selected_lang_code, st.session_state.messages)
            
            # Handle special case for market overview
            if response == "market_overview_requested":
                message_text = "📊 Top 10 Biggest Cryptos Right Now:\n\n*These are ranked by how much they're worth in total! 💎*"
                translated_message = translate_text(message_text, st.session_state.selected_lang_code)
                
                df = st.session_state.chatbot.get_market_overview_df()
                
                if not df.empty:
                    st.session_state.messages.append({"role": "assistant", "content": translated_message, "type": "text"})
                    st.session_state.messages.append({"role": "assistant", "content": df, "type": "dataframe"})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": translate_text("Oops! Can't load the market data right now 📊 Give it another shot!", st.session_state.selected_lang_code), "type": "text"})
            else:
                # Regular response
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        st.rerun()

    # Back to welcome page button
    st.markdown("<div style='text-align: center; margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("Go back to Welcome Page", key="back_to_welcome"):
        st.session_state.page = "welcome"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function to run the Streamlit application."""
    
    # --- Session State Initialization ---
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'animations_enabled' not in st.session_state:
        st.session_state.animations_enabled = True
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'selected_lang_code' not in st.session_state:
        st.session_state.selected_lang_code = 'en'
    if 'page' not in st.session_state:
        st.session_state.page = "welcome"
    if 'show_animation_warning' not in st.session_state:
        st.session_state.show_animation_warning = True
    if 'modal_shown_time' not in st.session_state:
        st.session_state.modal_shown_time = None
    
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.dark_mode, st.session_state.animations_enabled), unsafe_allow_html=True)

    # --- Photosensitivity Modal Timing Logic ---
    # This block checks if the modal should be dismissed after 5 seconds
    if st.session_state.show_animation_warning and st.session_state.modal_shown_time is None:
        st.session_state.modal_shown_time = time.time()
        
    if st.session_state.show_animation_warning and st.session_state.modal_shown_time and time.time() - st.session_state.modal_shown_time > 5:
        st.session_state.show_animation_warning = False
        st.session_state.modal_shown_time = None # Reset the timer
        st.rerun() # Force a rerun to hide the modal

    # Initialize chatbot instance if needed and on chatbot page
    if st.session_state.page == "chatbot" and st.session_state.chatbot is None:
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

    # Page navigation logic
    if st.session_state.page == "welcome":
        welcome_page()
    elif st.session_state.page == "chatbot":
        chatbot_page()
    elif st.session_state.page == "login":
        st.info("Login page coming soon!")
        if st.button("Back to Welcome"):
            st.session_state.page = "welcome"
            st.rerun()
    elif st.session_state.page == "about":
        st.info("About page coming soon!")
        if st.button("Back to Welcome"):
            st.session_state.page = "welcome"
            st.rerun()
    elif st.session_state.page == "signup":
        st.info("Sign up page coming soon!")
        if st.button("Back to Welcome"):
            st.session_state.page = "welcome"
            st.rerun()

if __name__ == "__main__":
    main()
