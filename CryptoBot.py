import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Crypto Assistant",
    page_icon="₿",
    layout="wide"
)

# API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

class CryptoChatbot:
    def __init__(self):
        self.supported_coins = [
            'bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana',
            'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'polygon'
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
            st.error(f"Error fetching price data: {e}")
            return None
    
    def get_crypto_history(self, coin_id, days=7):
        """Get historical price data"""
        try:
            url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"Error fetching historical data: {e}")
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
            st.error(f"Error fetching trending data: {e}")
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
            st.error(f"Error fetching market data: {e}")
            return None
    
    def process_query(self, user_input):
        """Process user query and return appropriate response"""
        user_input = user_input.lower()
        
        # Price queries
        if "price" in user_input:
            for coin in self.supported_coins:
                if coin.replace('-', '').replace('2', '') in user_input.replace(' ', ''):
                    return self.handle_price_query(coin)
            return "I can get prices for Bitcoin, Ethereum, BNB, Cardano, Solana, Polkadot, Dogecoin, Avalanche, Chainlink, and Polygon. Which one would you like?"
        
        # Chart queries
        elif "chart" in user_input or "graph" in user_input:
            for coin in self.supported_coins:
                if coin.replace('-', '').replace('2', '') in user_input.replace(' ', ''):
                    return self.handle_chart_query(coin)
            return "Which cryptocurrency would you like to see a chart for?"
        
        # Trending queries
        elif "trending" in user_input or "popular" in user_input:
            return self.handle_trending_query()
        
        # Market overview
        elif "market" in user_input or "overview" in user_input or "top" in user_input:
            return self.handle_market_query()
        
        # General help
        else:
            return self.get_help_response()
    
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
    
    def handle_chart_query(self, coin_id):
        """Handle chart-related queries"""
        history_data = self.get_crypto_history(coin_id, days=30)
        if history_data:
            prices = history_data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['price'],
                mode='lines',
                name=coin_id.replace('-', ' ').title(),
                line=dict(color='#00D4AA', width=2)
            ))
            
            fig.update_layout(
                title=f"{coin_id.replace('-', ' ').title()} Price Chart (30 Days)",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            return f"Here's the 30-day price chart for {coin_id.replace('-', ' ').title()}!"
        else:
            return f"Sorry, I couldn't fetch the chart data for {coin_id}."
    
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
    
    def get_help_response(self):
        """Provide help information"""
        return """
        **🤖 Crypto Assistant Help**
        
        I can help you with:
        
        📈 **Price Queries:** Ask about prices like "What's the price of Bitcoin?" or "ETH price"
        
        📊 **Charts:** Request charts like "Show me Bitcoin chart" or "Ethereum graph"
        
        🔥 **Trending:** Ask "What's trending?" or "Show popular coins"
        
        💹 **Market Overview:** Ask "Market overview" or "Top cryptocurrencies"
        
        **Supported Cryptocurrencies:**
        Bitcoin, Ethereum, BNB, Cardano, Solana, Polkadot, Dogecoin, Avalanche, Chainlink, Polygon
        
        Just type your question naturally - I'll understand! 🚀
        """

# Initialize the chatbot
@st.cache_resource
def load_chatbot():
    return CryptoChatbot()

def main():
    st.title("🚀 Cryptocurrency Assistant")
    st.markdown("Your AI-powered crypto companion for real-time market data and insights!")
    
    # Initialize chatbot
    chatbot = load_chatbot()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = chatbot.get_help_response()
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about cryptocurrency prices, charts, or market trends..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Fetching crypto data..."):
                response = chatbot.process_query(prompt)
                st.markdown(response, unsafe_allow_html=True)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Sidebar with quick actions
    with st.sidebar:
        st.header("Quick Actions")
        
        if st.button("🔥 Show Trending"):
            response = chatbot.handle_trending_query()
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("📊 Market Overview"):
            response = chatbot.handle_market_query()
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("💰 Bitcoin Price"):
            response = chatbot.handle_price_query("bitcoin")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("🔄 Clear Chat"):
            st.session_state.messages = []
            welcome_msg = chatbot.get_help_response()
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Data Source:** CoinGecko API")
        st.markdown("**Update Frequency:** Real-time")

if __name__ == "__main__":
    main()
