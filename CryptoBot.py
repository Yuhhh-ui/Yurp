import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import google.generativeai as genai
import re

# Page configuration
st.set_page_config(
    page_title="CryptoMind AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - ADD YOUR GEMINI API KEY HERE
GEMINI_API_KEY = "AIzaSyB8gVz_X5Uo36pBWaLKZqYjSGD0WMy5pO8"  
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

class CryptoChatbot:
    def __init__(self, gemini_api_key):
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
        
        # Crypto-related keywords for filtering
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto', 'blockchain',
            'altcoin', 'defi', 'nft', 'token', 'coin', 'mining', 'wallet', 'exchange',
            'trading', 'hodl', 'market cap', 'volume', 'price', 'bullish', 'bearish',
            'satoshi', 'wei', 'gas', 'fees', 'staking', 'yield', 'liquidity', 'dapp',
            'smart contract', 'consensus', 'proof of work', 'proof of stake', 'fork',
            'halving', 'airdrop', 'ico', 'ido', 'dao', 'web3', 'metaverse',
            'cardano', 'ada', 'solana', 'sol', 'polkadot', 'dot', 'chainlink', 'link',
            'polygon', 'matic', 'avalanche', 'avax', 'dogecoin', 'doge', 'shiba',
            'usdt', 'usdc', 'busd', 'stable', 'tether', 'binance', 'coinbase',
            'bull market', 'bear market', 'moon', 'lambo', 'diamond hands', 'paper hands'
        ]
    
    def is_crypto_related(self, text):
        """Check if the text is cryptocurrency related"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.crypto_keywords)
    
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
    
    def get_current_market_data(self):
        """Get current market data to provide context to AI"""
        market_data = self.get_market_overview()
        trending_data = self.get_trending_coins()
        
        context = "Current Crypto Market Data:\n"
        
        if market_data:
            context += "Top 5 Cryptocurrencies by Market Cap:\n"
            for i, coin in enumerate(market_data[:5], 1):
                price = coin['current_price']
                change = coin['price_change_percentage_24h']
                context += f"{i}. {coin['name']} ({coin['symbol'].upper()}): ${price:,.2f} ({change:+.2f}%)\n"
        
        if trending_data and 'coins' in trending_data:
            context += "\nTrending Coins:\n"
            for i, coin in enumerate(trending_data['coins'][:3], 1):
                context += f"{i}. {coin['item']['name']} ({coin['item']['symbol']})\n"
        
        return context
    
    def ask_ai(self, user_question):
        """Ask Gemini AI about cryptocurrency topics only"""
        
        # First check if the question is crypto-related
        if not self.is_crypto_related(user_question):
            return "🚫 Hey! I'm only here to chat about crypto stuff - Bitcoin, Ethereum, NFTs, all that good stuff. Hit me with a crypto question! 😄"
        
        try:
            # Get current market data for context
            market_context = self.get_current_market_data()
            
            # Create prompt for Gemini
            prompt = f"""You are a cool, teen-friendly cryptocurrency assistant. You're talking to young people (ages 15-30) who want to learn about crypto.

PERSONALITY:
- Be friendly, enthusiastic, and relatable
- Use simple, everyday language (no fancy financial jargon)
- Be like a knowledgeable friend explaining crypto
- Use emojis but don't overdo it
- Keep it real and honest about risks
- Make complex topics easy to understand

RULES:
1. ONLY answer crypto-related questions
2. If it's not about crypto, redirect nicely to crypto topics
3. Explain things simply but accurately
4. Use current market data when it helps
5. Keep responses under 250 words
6. Be encouraging but realistic about crypto investing
7. Always mention that crypto is risky

TONE EXAMPLES:
- Instead of "utilize" say "use"
- Instead of "substantial" say "big" or "huge"
- Instead of "fluctuations" say "price changes"
- Instead of "portfolio diversification" say "spreading your money around"

Current Market Context:
{market_context}

User Question: {user_question}

Give a helpful, friendly response:"""

            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Oops! Something went wrong on my end 😅 Try asking again in a sec: {str(e)}"
    
    def process_query(self, user_input):
        """Process user query and return appropriate response"""
        user_input_lower = user_input.lower()
        
        # Check for specific data requests first
        if "price" in user_input_lower and any(coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', '') for coin in self.supported_coins):
            for coin in self.supported_coins:
                if coin.replace('-', '').replace('2', '') in user_input_lower.replace(' ', ''):
                    return self.handle_price_query(coin)
        
        elif "trending" in user_input_lower or "popular" in user_input_lower:
            return self.handle_trending_query()
        
        elif "market" in user_input_lower and ("overview" in user_input_lower or "top" in user_input_lower):
            return self.handle_market_query()
        
        # For all other questions, use AI
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
**{coin_id.replace('-', ' ').title()} Right Now** 💰

💵 **Price:** ${price:,.2f}
{change_emoji} **24h:** <span style='color:{change_color}'>{change_24h:+.2f}%</span> ({change_text})
📊 **Market Size:** ${market_cap:,.0f}
💹 **Daily Trading:** ${volume_24h:,.0f}

*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*

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
            response = "**🔥 What's Hot Right Now:**\n\n"
            for i, coin in enumerate(trending_coins, 1):
                response += f"{i}. **{coin['item']['name']}** ({coin['item']['symbol'].upper()})\n"
                response += f"   Market Rank: #{coin['item']['market_cap_rank']}\n\n"
            response += "*These are the coins everyone's talking about today! 🚀*"
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
            return "**📊 Top 10 Biggest Cryptos Right Now:**\n\n*These are ranked by how much they're worth in total! 💎*"
        else:
            return "Oops! Can't load the market data right now 📊 Give it another shot!"

def main():
    # Load the crypto theme CSS
    st.markdown("""
    <style>
    /* Import cyber fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, 
            #0a0a0a 0%, 
            #1a1a2e 25%, 
            #16213e 50%, 
            #0f0f23 75%, 
            #000000 100%);
        color: #00ff88;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #00ff88, #00d4ff, #ff0080, #00ff88);
        background-size: 300% 300%;
        animation: gradientShift 3s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'Orbitron', monospace;
        font-weight: 900;
        font-size: 3.5rem;
        text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        margin-bottom: 1rem;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .sub-header {
        text-align: center;
        color: #888;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        padding: 0 2rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #00ff88, #00d4ff);
        color: #000;
        border: none;
        border-radius: 8px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.7rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #ff0080, #00ff88);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 128, 0.4);
    }
    
    /* Sidebar headers */
    .sidebar-header {
        color: #00ff88;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    /* Feature list styling */
    .feature-list {
        background: rgba(0, 255, 136, 0.05);
        border-left: 3px solid #00ff88;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Status indicators */
    .status-success {
        color: #00ff88;
        background: rgba(0, 255, 136, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border-left: 4px solid #00ff88;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
    }
    
    .status-error {
        color: #ff0080;
        background: rgba(255, 0, 128, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border-left: 4px solid #ff0080;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
    }
    
    /* Glowing effects */
    .glow-text {
        text-shadow: 0 0 10px currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Welcome message styling */
    .welcome-container {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
        backdrop-filter: blur(10px);
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Custom Chat Styling */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 1rem 0 !important;
    }
    
    /* Hide default chat avatars */
    .stChatMessage > div:first-child {
        display: none !important;
    }
    
    /* User Message Styling - Terminal Input Style */
    .user-message {
        background: linear-gradient(90deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.05));
        border-left: 4px solid #00ff88;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        position: relative;
        font-family: 'Rajdhani', monospace;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        backdrop-filter: blur(5px);
    }
    
    .user-message::before {
        content: ">";
        position: absolute;
        left: -2px;
        top: 50%;
        transform: translateY(-50%);
        background: #00ff88;
        color: #000;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .user-message::after {
        content: "";
        position: absolute;
        right: -1px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #00ff88, transparent);
    }
    
    /* AI Message Styling - Holographic Panel */
    .ai-message {
        background: linear-gradient(135deg, 
            rgba(0, 212, 255, 0.1) 0%,
            rgba(255, 0, 128, 0.1) 50%,
            rgba(0, 255, 136, 0.05) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
        overflow: hidden;
    }
    
    .ai-message::before {
        content: "";
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00d4ff, #ff0080, #00ff88, #00d4ff);
        background-size: 300% 300%;
        border-radius: 15px;
        z-index: -1;
        opacity: 0.5;
    }
    
    .ai-message::after {
        content: "◇ CRYPTOMIND AI";
        position: absolute;
        top: -8px;
        left: 20px;
        background: linear-gradient(90deg, #00d4ff, #ff0080);
        color: #000;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: bold;
        border-radius: 4px;
        font-family: 'Orbitron', monospace;
        letter-spacing: 1px;
    }
    
    /* Data stream effect for AI messages - conditional animation */
    .ai-message .data-stream {
        position: absolute;
        right: 10px;
        top: 10px;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        box-shadow: 0 0 10px #00ff88;
    }
    
    .ai-message .data-stream::before {
        content: "";
        position: absolute;
        right: 15px;
        top: 0;
        width: 6px;
        height: 6px;
        background: #00d4ff;
        border-radius: 50%;
        box-shadow: 0 0 8px #00d4ff;
    }
    
    .ai-message .data-stream::after {
        content: "";
        position: absolute;
        right: 25px;
        top: 1px;
        width: 4px;
        height: 4px;
        background: #ff0080;
        border-radius: 50%;
        box-shadow: 0 0 6px #ff0080;
    }
    
    /* Animated versions - only when toggle is on */
    .animations-on .ai-message .data-stream {
        animation: dataPulse 1.5s infinite;
    }
    
    .animations-on .ai-message .data-stream::before {
        animation: dataPulse 1.5s infinite 0.3s;
    }
    
    .animations-on .ai-message .data-stream::after {
        animation: dataPulse 1.5s infinite 0.6s;
    }
    
    .animations-on .user-message::after {
        animation: dataPulse 2s infinite;
    }
    
    .animations-on .user-message .terminal-cursor {
        animation: cursorBlink 1s infinite;
    }
    
    .animations-on .ai-message::before {
        animation: borderGlow 3s ease infinite;
    }
    
    /* Animations */
    @keyframes borderGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes dataPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(0.8); }
    }
    
    /* Terminal cursor effect for user input */
    .user-message .terminal-cursor {
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background: #00ff88;
        margin-left: 2px;
    }
    
    @keyframes cursorBlink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    /* Glitch effect for user messages on hover */
    .user-message:hover {
        animation: glitchEffect 0.3s ease-in-out;
    }
    
    @keyframes glitchEffect {
        0% { transform: translateX(0); }
        20% { transform: translateX(-2px); }
        40% { transform: translateX(2px); }
        60% { transform: translateX(-1px); }
        80% { transform: translateX(1px); }
        100% { transform: translateX(0); }
    }
    
    /* Hologram effect for AI messages */
    .ai-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Custom header with crypto styling and toggle
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Animation toggle in top corner
        if 'animation_enabled' not in st.session_state:
            st.session_state.animation_enabled = True
        animation_enabled = st.toggle("🌟 Effects", value=st.session_state.animation_enabled, help="Toggle blinking animations")
        st.session_state.animation_enabled = animation_enabled
    
    with col2:
        st.markdown("""
        <div class="main-header">
            🚀 CRYPTOMIND AI 🤖
        </div>
        <div class="sub-header">
            ⚡ Your Crypto Buddy That Actually Gets It ⚡<br>
            <span style="color: #00ff88;">🔮 Smart AI • Live Prices • Easy Explanations 🔮</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.write("")  # Empty column for spacing
    
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
    
    # Sidebar with quick actions
    with st.sidebar:
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
        <div class="sidebar-header">🛡️ WHAT I CAN DO</div>
        
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
    
    # Initialize chat history without the welcome message
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages with custom styling and conditional animations
    animation_class = "animations-on" if st.session_state.get('animation_enabled', True) else ""
    
    # Add CSS class to body based on toggle state
    if st.session_state.get('animation_enabled', True):
        st.markdown('<div class="animations-on">', unsafe_allow_html=True)
    
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
    
    # Close the animation wrapper div
    if st.session_state.get('animation_enabled', True):
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input with enhanced styling
    if prompt := st.chat_input("🔮 Ask me anything about crypto..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate and display assistant response
        with st.spinner("🧠 Thinking about your crypto question..."):
            response = st.session_state.chatbot.process_query(prompt)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to show new messages with custom styling
        st.rerun()

if __name__ == "__main__":
    main()
