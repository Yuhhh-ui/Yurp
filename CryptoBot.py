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
GEMINI_API_KEY = "AIzaSyDI-goqVqX2FpAhcK-WPS72UZ4ok2OhSFE"
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
        """Ask Gemini AI about cryptocurrency topics only"""
        
        # First check if the question is crypto-related
        if not self.is_crypto_related(user_question):
            return "🚫 Hey! I'm only here to chat about crypto stuff - Bitcoin, Ethereum, NFTs, all that good stuff. Hit me with a crypto question! 😄"
        
        try:
            # Get current market data for context
            market_context = self.get_current_market_data()
            
            # Create prompt for Gemini
            prompt = f"""You are a professional, teen-friendly cryptocurrency assistant. You're talking to young people (ages 17-30) who want to learn about crypto. Keep the statistics local like for the Caribbean

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
3. Explain things simply but accurately and professionally 
4. Use current market data when it helps
5. Keep responses under 100 words
6. Be encouraging but realistic about crypto investing
7. Always mention that crypto is risky
8. Answer in point form where neccessary.
9. **IMPORTANT: DO NOT include any HTML tags or markdown that creates HTML elements in your response, such as `<div>`, `<span>`, etc.**

TONE EXAMPLES:
- Instead of "utilize" say "use"
- Instead of "substantial" say "big" or "huge"
- Instead of "fluctuations" say "price changes"
- Instead of "portfolio diversification" say "spreading your money around"

Current Market Context:
{market_context}

Your Question: {user_question}

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
            
            response = f"""**{coin_id.replace('-', ' ').title()} Right Now** 💰

💵 **Price:** ${price:,.2f}
{change_emoji} **24h:** {change_24h:+.2f}% ({change_text})
📊 **Market Size:** ${market_cap:,.0f}
💹 **Daily Trading:** ${volume_24h:,.0f}

*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*

Remember: Crypto prices change super fast! ⚡"""
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
                response += f"    Market Rank: #{coin['item']['market_cap_rank']}\n\n"
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

def show_homepage():
    """Display the stunning homepage"""
    st.markdown("""
    <style>
        /* Import cyber fonts */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
        
        /* Hide Streamlit default elements for homepage */
        .main > div {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }
        
        /* Homepage Styles */
        .homepage-container {
            position: relative;
            min-height: 100vh;
            background: linear-gradient(135deg, 
                #0a0a0a 0%, 
                #1a1a2e 25%, 
                #16213e 50%, 
                #0f0f23 75%, 
                #000000 100%);
            color: #ffffff;
            font-family: 'Rajdhani', sans-serif;
            overflow: hidden;
            margin: -1rem -1rem 0 -1rem;
            padding: 0;
        }
        
        /* Navigation */
        .homepage-navbar {
            position: fixed;
            top: 0;
            width: 100%;
            padding: 1rem 2rem;
            background: rgba(10, 10, 10, 0.9);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(0, 255, 136, 0.2);
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .homepage-logo {
            display: flex;
            align-items: center;
            gap: 1rem;
            font-family: 'Orbitron', monospace;
            font-weight: 700;
            font-size: 1.2rem;
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        
        .homepage-logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        .homepage-nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .homepage-nav-link {
            color: #888;
            text-decoration: none;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: default;
        }
        
        .homepage-nav-link:hover {
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        
        .homepage-signup-btn {
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            color: #000;
            padding: 0.7rem 1.5rem;
            border: none;
            border-radius: 25px;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
        }
        
        .homepage-signup-btn:hover {
            background: linear-gradient(45deg, #ff0080, #00ff88);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 0, 128, 0.4);
        }
        
        /* Main Container */
        .homepage-main {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            padding: 2rem;
            margin-top: 80px;
        }
        
        /* Hero Section */
        .homepage-hero {
            text-align: center;
            max-width: 800px;
            z-index: 10;
            position: relative;
        }
        
        .homepage-hero-title {
            font-family: 'Orbitron', monospace;
            font-weight: 900;
            font-size: clamp(2.5rem, 8vw, 4.5rem);
            line-height: 1.2;
            margin-bottom: 2rem;
            background: linear-gradient(90deg, #ffffff, #00ff88, #00d4ff, #ffffff);
            background-size: 300% 300%;
            animation: gradientShift 4s ease infinite;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        }
        
        .homepage-hero-subtitle {
            font-size: clamp(1rem, 3vw, 1.3rem);
            color: #888;
            margin-bottom: 1rem;
            font-weight: 400;
            line-height: 1.6;
        }
        
        .homepage-hero-description {
            font-size: clamp(1.1rem, 3vw, 1.4rem);
            color: #00ff88;
            margin-bottom: 3rem;
            font-weight: 600;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        
        /* Floating 3D Elements */
        .homepage-floating-element {
            position: absolute;
            pointer-events: none;
        }
        
        .homepage-crystal-1 {
            top: 15%;
            left: 15%;
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #00d4ff, #0080ff);
            clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
            animation: float1 6s ease-in-out infinite;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.6);
        }
        
        .homepage-crystal-2 {
            top: 20%;
            right: 10%;
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, #ff0080, #ff4080);
            clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
            animation: float2 8s ease-in-out infinite;
            box-shadow: 0 0 25px rgba(255, 0, 128, 0.6);
        }
        
        .homepage-crystal-3 {
            bottom: 25%;
            left: 10%;
            width: 70px;
            height: 70px;
            background: linear-gradient(45deg, #00ff88, #80ff88);
            clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
            animation: float3 7s ease-in-out infinite;
            box-shadow: 0 0 28px rgba(0, 255, 136, 0.6);
        }
        
        .homepage-crystal-4 {
            bottom: 15%;
            right: 20%;
            width: 50px;
            height: 50px;
            background: linear-gradient(45deg, #8000ff, #c080ff);
            border-radius: 50%;
            animation: float4 5s ease-in-out infinite;
            box-shadow: 0 0 20px rgba(128, 0, 255, 0.6);
        }
        
        .homepage-orb-1 {
            top: 30%;
            left: 5%;
            width: 40px;
            height: 40px;
            background: radial-gradient(circle, #00ff88, transparent);
            border-radius: 50%;
            animation: pulse1 3s ease-in-out infinite;
            opacity: 0.7;
        }
        
        .homepage-orb-2 {
            top: 60%;
            right: 15%;
            width: 35px;
            height: 35px;
            background: radial-gradient(circle, #00d4ff, transparent);
            border-radius: 50%;
            animation: pulse2 4s ease-in-out infinite;
            opacity: 0.6;
        }
        
        .homepage-ring-1 {
            top: 40%;
            right: 5%;
            width: 100px;
            height: 100px;
            border: 3px solid rgba(0, 255, 136, 0.3);
            border-radius: 50%;
            animation: rotate1 10s linear infinite;
        }
        
        .homepage-ring-2 {
            bottom: 30%;
            left: 20%;
            width: 80px;
            height: 80px;
            border: 2px solid rgba(0, 212, 255, 0.4);
            border-radius: 50%;
            animation: rotate2 8s linear infinite reverse;
        }
        
        /* Particle Background */
        .homepage-particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }
        
        .homepage-particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: #00ff88;
            border-radius: 50%;
            animation: twinkle 3s ease-in-out infinite;
        }
        
        .homepage-particle:nth-child(2n) { background: #00d4ff; animation-delay: 1s; }
        .homepage-particle:nth-child(3n) { background: #ff0080; animation-delay: 2s; }
        
        /* Animations */
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes float1 {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(120deg); }
            66% { transform: translateY(10px) rotate(240deg); }
        }
        
        @keyframes float2 {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(180deg); }
        }
        
        @keyframes float3 {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            25% { transform: translateY(-15px) rotate(90deg); }
            75% { transform: translateY(15px) rotate(270deg); }
        }
        
        @keyframes float4 {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-25px) scale(1.1); }
        }
        
        @keyframes pulse1 {
            0%, 100% { transform: scale(1); opacity: 0.7; }
            50% { transform: scale(1.5); opacity: 0.3; }
        }
        
        @keyframes pulse2 {
            0%, 100% { transform: scale(1); opacity: 0.6; }
            50% { transform: scale(1.3); opacity: 0.2; }
        }
        
        @keyframes rotate1 {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes rotate2 {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }
        
        @keyframes twinkle {
            0%, 100% { opacity: 0; transform: scale(0); }
            50% { opacity: 1; transform: scale(1); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .homepage-navbar {
                padding: 1rem;
            }
            
            .homepage-nav-links {
                gap: 1rem;
            }
            
            .homepage-nav-link {
                font-size: 0.9rem;
            }
            
            .homepage-signup-btn {
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
            }
            
            .homepage-main {
                padding: 1rem;
                margin-top: 60px;
            }
            
            .homepage-hero-description {
                margin-bottom: 2rem;
            }
            
            .homepage-crystal-1, .homepage-crystal-2, .homepage-crystal-3, .homepage-crystal-4 {
                transform: scale(0.7);
            }
            
            .homepage-ring-1, .homepage-ring-2 {
                transform: scale(0.6);
            }
        }
        
        @media (max-width: 480px) {
            .homepage-nav-links .homepage-nav-link:not(:last-child) {
                display: none;
            }
        }
    </style>
    
    <div class="homepage-container">
        <!-- Particle Background -->
        <div class="homepage-particles">
            <div class="homepage-particle" style="top: 10%; left: 20%; animation-delay: 0s;"></div>
            <div class="homepage-particle" style="top: 30%; left: 80%; animation-delay: 1s;"></div>
            <div class="homepage-particle" style="top: 60%; left: 10%; animation-delay: 2s;"></div>
            <div class="homepage-particle" style="top: 80%; left: 70%; animation-delay: 0.5s;"></div>
            <div class="homepage-particle" style="top: 20%; left: 50%; animation-delay: 1.5s;"></div>
            <div class="homepage-particle" style="top: 70%; left: 30%; animation-delay: 2.5s;"></div>
            <div class="homepage-particle" style="top: 40%; left: 90%; animation-delay: 0.8s;"></div>
            <div class="homepage-particle" style="top: 90%; left: 20%; animation-delay: 1.8s;"></div>
        </div>

        <!-- Navigation -->
        <nav class="homepage-navbar">
            <div class="homepage-logo">
                <div class="homepage-logo-icon">🛡️</div>
                <span>KRYPTONIC AI</span>
            </div>
            <div class="homepage-nav-links">
                <span class="homepage-nav-link">LOG IN</span>
                <span class="homepage-nav-link">★★★★★</span>
                <span class="homepage-nav-link">ABOUT</span>
                <span class="homepage-signup-btn">Sign up →</span>
            </div>
        </nav>

        <!-- Main Container -->
        <div class="homepage-main">
            <!-- Floating 3D Elements -->
            <div class="homepage-floating-element homepage-crystal-1"></div>
            <div class="homepage-floating-element homepage-crystal-2"></div>
            <div class="homepage-floating-element homepage-crystal-3"></div>
            <div class="homepage-floating-element homepage-crystal-4"></div>
            <div class="homepage-floating-element homepage-orb-1"></div>
            <div class="homepage-floating-element homepage-orb-2"></div>
            <div class="homepage-floating-element homepage-ring-1"></div>
            <div class="homepage-floating-element homepage-ring-2"></div>

            <!-- Hero Section -->
            <div class="homepage-hero">
                <h1 class="homepage-hero-title">
                    Welcome to Kryptonic AI,<br>
                    Your crypto guide, where<br>
                    futures collide
                </h1>
                <p class="homepage-hero-subtitle">
                    ⚡ Your Crypto Buddy That Actually Gets It ⚡
                </p>
                <p class="homepage-hero-description">
                    🔮 Smart AI • Live Prices • Easy Explanations 🔮
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for the start chat button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Fixed button implementation
        start_chat_button = st.button("🚀 START A CHAT 🚀", key="start_chat_btn", help="Begin your crypto journey!", use_container_width=True)
        
        # Handle button click using session state
        if start_chat_button:
            st.session_state.show_homepage = False
            st.session_state.start_chat = True
            st.rerun()

def show_chat():
    """Display the chat interface"""
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
        animation-play-state: running; 
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
        animation-play-state: running;
    }
    
    .ai-message::after {
        content: "◇ KRYPTONIC AI";
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
    
    /* Data stream effect for AI messages */
    .ai-message .data-stream {
        position: absolute;
        right: 10px;
        top: 10px;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        box-shadow: 0 0 10px #00ff88;
        animation-play-state: running;
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
        animation-play-state: running;
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
        animation-play-state: running;
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
        animation-play-state: running;
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
    
    /* Back to homepage button */
    .back-to-home {
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 1000;
        background: linear-gradient(45deg, #ff0080, #00ff88);
        color: #000;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1rem;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(255, 0, 128, 0.3);
        transition: all 0.3s ease;
    }
    
    .back-to-home:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 128, 0.5);
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Back to homepage button
    back_home_button = st.button("🏠 ← BACK TO HOME", key="back_home_btn")
    if back_home_button:
        st.session_state.show_homepage = True
        st.session_state.start_chat = False
        st.session_state.messages = []  # Clear chat history
        st.rerun()
    
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
            trending_btn = st.button("🔥 TRENDING", key="trending_btn")
            if trending_btn:
                response = st.session_state.chatbot.handle_trending_query()
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
            btc_price_btn = st.button("💰 BTC PRICE", key="btc_price_btn")
            if btc_price_btn:
                response = st.session_state.chatbot.handle_price_query("bitcoin")
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col2:
            top_coins_btn = st.button("📊 TOP COINS", key="top_coins_btn")
            if top_coins_btn:
                response = st.session_state.chatbot.handle_market_query()
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
            clear_chat_btn = st.button("🔄 CLEAR CHAT", key="clear_chat_btn")
            if clear_chat_btn:
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
    prompt = st.chat_input("🤑Ask me anything about crypto...")
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate and display assistant response
        with st.spinner("🧠 Thinking about your question..."):
            response = st.session_state.chatbot.process_query(prompt)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to show new messages with custom styling
        st.rerun()

def main():
    # Initialize session state
    if 'show_homepage' not in st.session_state:
        st.session_state.show_homepage = True
    if 'start_chat' not in st.session_state:
        st.session_state.start_chat = False
    
    # Show homepage or chat based on state
    if st.session_state.show_homepage:
        show_homepage()
    else:
        show_chat()

if __name__ == "__main__":
    main()
