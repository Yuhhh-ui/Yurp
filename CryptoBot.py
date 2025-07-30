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
    """Display the stunning homepage inspired by the reference design"""
    
    # Enhanced CSS with 3D elements and animations
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        .stApp {
            background: radial-gradient(ellipse at center, #1a1a2e 0%, #16213e 35%, #0f0f23 100%);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Animated background gradient */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
            animation: gradientShift 10s ease infinite;
            z-index: -1;
        }
        
        @keyframes gradientShift {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 0.6; }
        }
        
        /* Navigation Bar */
        .nav-container {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 1rem 2rem;
            background: rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .nav-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .logo-text {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            color: white;
            letter-spacing: -0.5px;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
            padding: 0.5rem 1rem;
            border-radius: 8px;
        }
        
        .nav-link:hover {
            color: white;
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-1px);
        }
        
        .nav-rating {
            display: flex;
            gap: 2px;
            padding: 0.5rem;
        }
        
        .star {
            color: #ffd700;
            font-size: 0.9rem;
            text-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
        }
        
        /* About Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }
        
        .modal-content {
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.95), rgba(22, 33, 62, 0.95));
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2.5rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            position: relative;
            backdrop-filter: blur(20px);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .modal-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            color: white;
            margin: 0;
        }
        
        .close-btn {
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 50%;
            transition: all 0.3s ease;
        }
        
        .close-btn:hover {
            color: white;
            background: rgba(255, 255, 255, 0.1);
            transform: rotate(90deg);
        }
        
        .modal-body {
            color: rgba(255, 255, 255, 0.9);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
        }
        
        .modal-body h3 {
            color: #667eea;
            margin: 1.5rem 0 1rem 0;
            font-weight: 600;
        }
        
        .modal-body p {
            margin-bottom: 1rem;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .feature-card {
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            padding: 1rem;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            background: rgba(102, 126, 234, 0.15);
        }
        
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        
        /* 3D Floating Crypto Elements */
        .floating-element {
            position: absolute;
            opacity: 0.9;
            animation: float3d 8s ease-in-out infinite;
            font-size: 3rem;
            user-select: none;
            pointer-events: none;
        }
        
        /* Bitcoin Coin */
        .crypto-bitcoin {
            top: 15%;
            left: 10%;
            color: #f7931a;
            text-shadow: 0 0 20px rgba(247, 147, 26, 0.6);
            animation-delay: 0s;
            filter: drop-shadow(0 10px 20px rgba(247, 147, 26, 0.3));
        }
        
        /* Ethereum */
        .crypto-ethereum {
            top: 25%;
            right: 15%;
            color: #627eea;
            text-shadow: 0 0 20px rgba(98, 126, 234, 0.6);
            animation-delay: 2s;
            filter: drop-shadow(0 8px 16px rgba(98, 126, 234, 0.3));
        }
        
        /* Circuit/Tech Element */
        .crypto-circuit {
            bottom: 30%;
            left: 20%;
            color: #00ff88;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.6);
            animation-delay: 4s;
            filter: drop-shadow(0 12px 24px rgba(0, 255, 136, 0.3));
        }
        
        /* Dollar/Money */
        .crypto-money {
            bottom: 20%;
            right: 10%;
            color: #50c878;
            text-shadow: 0 0 20px rgba(80, 200, 120, 0.6);
            animation-delay: 6s;
            filter: drop-shadow(0 6px 12px rgba(80, 200, 120, 0.3));
        }
        
        /* Rocket/Growth */
        .crypto-rocket {
            top: 60%;
            right: 25%;
            color: #ff6b6b;
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.6);
            animation-delay: 1s;
            filter: drop-shadow(0 8px 16px rgba(255, 107, 107, 0.3));
        }
        
        /* Shield/Security */
        .crypto-shield {
            top: 45%;
            left: 8%;
            color: #4ecdc4;
            text-shadow: 0 0 20px rgba(78, 205, 196, 0.6);
            animation-delay: 3s;
            filter: drop-shadow(0 10px 20px rgba(78, 205, 196, 0.3));
        }
        
        /* Chart/Analytics */
        .crypto-chart {
            top: 70%;
            left: 15%;
            color: #ffd93d;
            text-shadow: 0 0 20px rgba(255, 217, 61, 0.6);
            animation-delay: 5s;
            filter: drop-shadow(0 7px 14px rgba(255, 217, 61, 0.3));
        }
        
        /* Diamond/Value */
        .crypto-diamond {
            bottom: 40%;
            right: 20%;
            color: #b19cd9;
            text-shadow: 0 0 20px rgba(177, 156, 217, 0.6);
            animation-delay: 7s;
            filter: drop-shadow(0 9px 18px rgba(177, 156, 217, 0.3));
        }
        
        @keyframes float3d {
            0%, 100% { 
                transform: translateY(0px) rotate(0deg) scale(1);
            }
            33% { 
                transform: translateY(-25px) rotate(10deg) scale(1.1);
            }
            66% { 
                transform: translateY(15px) rotate(-5deg) scale(0.9);
            }
        }
        
        /* Special pulse animation for crypto elements */
        @keyframes cryptoPulse {
            0%, 100% { 
                opacity: 0.9;
                transform: scale(1);
            }
            50% { 
                opacity: 1;
                transform: scale(1.05);
            }
        }
        
        /* Apply pulse to certain elements */
        .crypto-bitcoin, .crypto-ethereum {
            animation: float3d 8s ease-in-out infinite, cryptoPulse 3s ease-in-out infinite;
        }
        
        /* Hero Section */
        .hero-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
            padding: 2rem;
            position: relative;
            z-index: 10;
        }
        
        .hero-title {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: clamp(2.5rem, 8vw, 5.5rem);
            line-height: 1.1;
            color: white;
            margin-bottom: 1.5rem;
            max-width: 900px;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        }
        
        .hero-subtitle {
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            font-size: clamp(1rem, 3vw, 1.3rem);
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 3rem;
            max-width: 600px;
            line-height: 1.6;
        }
        
        .start-chat-btn {
            background: white;
            color: #1a1a2e;
            padding: 1rem 2.5rem;
            border-radius: 50px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 1.1rem;
            border: none;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
        }
        
        .start-chat-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.6s;
        }
        
        .start-chat-btn:hover::before {
            left: 100%;
        }
        
        .start-chat-btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 15px 40px rgba(255, 255, 255, 0.3);
        }
        
        .start-chat-btn:active {
            transform: translateY(-1px) scale(1.02);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .nav-content {
                padding: 0 1rem;
            }
            
            .nav-links {
                gap: 1rem;
            }
            
            .nav-link {
                font-size: 0.8rem;
            }
            
            .signup-btn {
                padding: 0.5rem 1rem;
                font-size: 0.8rem;
            }
            
            .crypto-bitcoin, .crypto-ethereum, .crypto-circuit, .crypto-money, 
            .crypto-rocket, .crypto-shield, .crypto-chart, .crypto-diamond {
                font-size: 2rem !important;
            }
            
            .hero-container {
                padding: 1rem;
            }
        }
        
        /* Hide Streamlit elements */
        .stDeployButton {
            display: none;
        }
        
        #MainMenu {
            visibility: hidden;
        }
        
        .stAppHeader {
            display: none;
        }
        
        footer {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation Bar with About Modal
    st.markdown("""
    <div class="nav-container">
        <div class="nav-content">
            <div class="logo-section">
                <div class="logo-icon">🛡️</div>
                <div class="logo-text">CRYPTO KNIGHT</div>
            </div>
            <div class="nav-links">
                <div class="nav-rating">
                    <span class="star">★</span>
                    <span class="star">★</span>
                    <span class="star">★</span>
                    <span class="star">★</span>
                    <span class="star">★</span>
                </div>
                <span class="nav-link" onclick="showAboutModal()">ABOUT</span>
            </div>
        </div>
    </div>
    
    <!-- About Modal -->
    <div id="aboutModal" class="modal-overlay" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">🛡️ About Crypto Knight</h2>
                <button class="close-btn" onclick="hideAboutModal()">×</button>
            </div>
            <div class="modal-body">
                <p><strong>Welcome to the future of crypto education!</strong></p>
                
                <h3>🎯 Our Purpose</h3>
                <p>Crypto Knight is your personal AI-powered crypto companion, designed to make cryptocurrency accessible, understandable, and exciting for everyone. We bridge the gap between complex crypto concepts and everyday understanding.</p>
                
                <h3>🤖 How It Works</h3>
                <p>Our advanced AI chatbot combines real-time market data with intelligent conversation to provide you with:</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">💬</div>
                        <strong>Smart Conversations</strong><br>
                        Ask anything about crypto in plain English and get clear, friendly explanations
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <strong>Live Market Data</strong><br>
                        Real-time prices, trending coins, and market insights powered by CoinGecko API
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎓</div>
                        <strong>Educational Focus</strong><br>
                        Learn about blockchain, DeFi, NFTs, and more with beginner-friendly explanations
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔒</div>
                        <strong>Safe & Focused</strong><br>
                        Crypto-only conversations with honest risk assessments and responsible advice
                    </div>
                </div>
                
                <h3>💡 What Makes Us Different</h3>
                <p>• <strong>Teen-Friendly:</strong> We speak your language, no confusing jargon<br>
                • <strong>Real-Time Data:</strong> Always current with live market information<br>
                • <strong>Caribbean Focus:</strong> Localized insights for our regional users<br>
                • <strong>Honest & Transparent:</strong> We always mention risks and promote responsible investing</p>
                
                <h3>🚀 Get Started</h3>
                <p>Ready to explore the crypto universe? Click "Start a chat" and ask me anything - from basic questions like "What is Bitcoin?" to complex topics like DeFi protocols. I'm here to guide you on your crypto journey!</p>
            </div>
        </div>
    </div>
    
    <script>
        function showAboutModal() {
            document.getElementById('aboutModal').style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
        
        function hideAboutModal() {
            document.getElementById('aboutModal').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        // Close modal when clicking outside
        document.getElementById('aboutModal').addEventListener('click', function(e) {
            if (e.target === this) {
                hideAboutModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideAboutModal();
            }
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Floating 3D Crypto Elements
    st.markdown("""
    <div class="floating-element crypto-bitcoin">₿</div>
    <div class="floating-element crypto-ethereum">⟠</div>
    <div class="floating-element crypto-circuit">⚡</div>
    <div class="floating-element crypto-money">💰</div>
    <div class="floating-element crypto-rocket">🚀</div>
    <div class="floating-element crypto-shield">🛡️</div>
    <div class="floating-element crypto-chart">📈</div>
    <div class="floating-element crypto-diamond">💎</div>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">
            Welcome to Crypto Knight,<br>
            Your crypto guide, where<br>
            futures collide
        </h1>
        <p class="hero-subtitle">
            Navigate the crypto universe with AI-powered insights, real-time data, and expert guidance tailored for the next generation of digital investors.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create invisible columns for button positioning
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # Custom button with enhanced styling
        if st.button("Start a chat →", key="start_chat_btn", help="Begin your crypto journey!"):
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
