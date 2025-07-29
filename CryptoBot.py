import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import google.generativeai as genai
import re

# Page configuration
st.set_page_config(
    page_title="Crypto Assistant",
    page_icon="₿",
    layout="wide"
)

# API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

class CryptoChatbot:
    def __init__(self, gemini_api_key):
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
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
            return "🚫 I'm sorry, but I can only answer questions related to cryptocurrency, blockchain, and digital assets. Please ask me something about crypto!"
        
        try:
            # Get current market data for context
            market_context = self.get_current_market_data()
            
            # Create prompt for Gemini
            prompt = f"""You are a cryptocurrency expert assistant. You ONLY answer questions related to cryptocurrency, blockchain, digital assets, DeFi, NFTs, and related topics.

STRICT RULES:
1. ONLY respond to cryptocurrency-related questions
2. If asked about non-crypto topics, politely decline and redirect to crypto topics
3. Provide accurate, helpful information about cryptocurrencies
4. Use current market data when relevant
5. Be conversational but informative
6. Use emojis occasionally to make responses engaging
7. Keep responses concise but informative (under 300 words)

Current Market Context:
{market_context}

User Question: {user_question}

Please provide a helpful response about this cryptocurrency topic:"""

            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
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
            change_color = "green" if change_24h > 0 else "red"
            
            response = f"""
**{coin_id.replace('-', ' ').title()} Price Information** ₿

💰 **Current Price:** ${price:,.2f}
{change_emoji} **24h Change:** <span style='color:{change_color}'>{change_24h:+.2f}%</span>
📊 **Market Cap:** ${market_cap:,.0f}
💹 **24h Volume:** ${volume_24h:,.0f}

*Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
            """
            return response
        else:
            return f"Sorry, I couldn't fetch the price data for {coin_id}. Please try again later."
    
    def handle_trending_query(self):
        """Handle trending coins query"""
        trending_data = self.get_trending_coins()
        if trending_data:
            trending_coins = trending_data['coins'][:5]
            response = "**🔥 Trending Cryptocurrencies:**\n\n"
            for i, coin in enumerate(trending_coins, 1):
                response += f"{i}. **{coin['item']['name']}** ({coin['item']['symbol'].upper()})\n"
                response += f"   Rank: #{coin['item']['market_cap_rank']}\n\n"
            return response
        else:
            return "Sorry, I couldn't fetch trending data right now."
    
    def handle_market_query(self):
        """Handle market overview query"""
        market_data = self.get_market_overview()
        if market_data:
            df = pd.DataFrame(market_data)
            df_display = df[['name', 'symbol', 'current_price', 'price_change_percentage_24h', 'market_cap']].copy()
            df_display.columns = ['Name', 'Symbol', 'Price (USD)', '24h Change (%)', 'Market Cap']
            df_display['Price (USD)'] = df_display['Price (USD)'].apply(lambda x: f"${x:,.2f}")
            df_display['24h Change (%)'] = df_display['24h Change (%)'].apply(lambda x: f"{x:+.2f}%")
            df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(df_display, use_container_width=True)
            return "**📊 Top 10 Cryptocurrencies by Market Cap:**"
        else:
            return "Sorry, I couldn't fetch market data right now."

def main():
    st.title("🚀 Cryptocurrency Assistant")
    st.markdown("Your AI-powered crypto companion that ONLY talks about cryptocurrency!")
    
    # API Key input
    with st.sidebar:
        st.header("🔑 API Configuration")
        gemini_api_key = st.text_input(
            "Enter your Gemini API Key:",
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        
        if not gemini_api_key:
            st.warning("⚠️ Please enter your Gemini API key to use the chatbot!")
            st.markdown("---")
            st.markdown("**How to get a Gemini API key:**")
            st.markdown("1. Go to https://makersuite.google.com/app/apikey")
            st.markdown("2. Sign in with your Google account")
            st.markdown("3. Click 'Create API Key'")
            st.markdown("4. Copy and paste it above")
            st.markdown("5. Gemini API is FREE to use!")
            return
        
        st.success("✅ Gemini API Key configured!")
        st.markdown("---")
        
        st.header("Quick Actions")
        
        # Initialize chatbot
        if 'chatbot' not in st.session_state:
            st.session_state.chatbot = CryptoChatbot(gemini_api_key)
        
        if st.button("🔥 Show Trending"):
            response = st.session_state.chatbot.handle_trending_query()
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("📊 Market Overview"):
            response = st.session_state.chatbot.handle_market_query()
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("💰 Bitcoin Price"):
            response = st.session_state.chatbot.handle_price_query("bitcoin")
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("🔄 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Features:**")
        st.markdown("• Gemini AI answers crypto questions")
        st.markdown("• Real-time price data")
        st.markdown("• Market trends & analysis")
        st.markdown("• ONLY crypto topics allowed")
        st.markdown("• FREE Gemini API usage!")
    
    # Initialize chatbot with API key
    if gemini_api_key:
        if 'chatbot' not in st.session_state:
            st.session_state.chatbot = CryptoChatbot(gemini_api_key)
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            welcome_msg = """
🤖 **Welcome to your Crypto Assistant!** 

I'm here to answer ANY cryptocurrency-related questions you have! I can help you with:

💡 **General Crypto Knowledge:** Blockchain basics, how cryptocurrencies work, DeFi, NFTs
📊 **Market Analysis:** Price predictions, market trends, trading strategies  
🔍 **Specific Coins:** Information about Bitcoin, Ethereum, altcoins, new projects
⚡ **Real-time Data:** Current prices, trending coins, market overview
🎓 **Learning:** Crypto terminology, investment tips, security best practices

**Try asking me:**
- "What is Bitcoin and how does it work?"
- "Should I invest in Ethereum right now?"
- "What's the difference between DeFi and traditional finance?"
- "Bitcoin price" (for real-time data)
- "Show trending coins"

❌ **Note:** I ONLY discuss cryptocurrency topics. I won't answer questions about other subjects!

What would you like to know about crypto? 🚀
            """
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about cryptocurrency..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking about crypto..."):
                    response = st.session_state.chatbot.process_query(prompt)
                    st.markdown(response, unsafe_allow_html=True)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
