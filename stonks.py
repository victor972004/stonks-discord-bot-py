import discord
import requests
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import os
import yfinance as yf

load_dotenv()  # Before accessing environment variables

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rest of your bot code...
# Configuration
INDEX_SYMBOL = "^GSPC"  # S&P 500 symbol

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def calculate_rsi(data, window):
    delta = data['Close'].diff().dropna()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    avg_gain = gains.rolling(window).mean()
    avg_loss = losses.rolling(window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_sp500_data():
    try:
        sp500 = yf.Ticker(INDEX_SYMBOL)
        hist = sp500.history(period="200d")
        
        if hist.empty:
            return None, None, None, None, "No data available"
            
        current_price = hist['Close'].iloc[-1]
        ma200 = hist['Close'].mean()
        
        # Calculate both RSI values
        rsi5 = calculate_rsi(hist, 5)
        rsi14 = calculate_rsi(hist, 14)
        
        return current_price, ma200, rsi5, rsi14, None
        
    except Exception as e:
        return None, None, None, None, f"Error: {str(e)}"

@bot.command(name='stonks')
async def stonks_command(ctx):
    current_price, ma200, rsi5, rsi14, error = get_sp500_data()
    
    if error:
        await ctx.send(f"🚨 {error}")
        return
        
    if current_price is None:
        await ctx.send("Could not fetch market data")
        return
    
    message = f"**📈 S&P 500 Current Price:** ${current_price:.2f}\n"
    
    # 200-Day MA Section
    if ma200 is not None:
        status = "ABOVE" if current_price > ma200 else "BELOW"
        difference = abs(current_price - ma200)
        percentage_diff = (difference / ma200) * 100
        message += (
            f"\n**📊 200-Day MA:** ${ma200:.2f}\n"
            f"**📉 Trend:** {status} by ${difference:.2f} ({percentage_diff:.2f}%)"
        )
    
    # RSI Section
    rsi_message = []
    if rsi5 is not None:
        rsi5_status = "🚨 Overbought" if rsi5 >= 70 else "🔔 Oversold" if rsi5 <= 30 else "⚖️ Neutral"
        rsi_message.append(f"5-Day: {rsi5:.1f} ({rsi5_status})")
        
    if rsi14 is not None:
        rsi14_status = "🚨 Overbought" if rsi14 >= 70 else "🔔 Oversold" if rsi14 <= 30 else "⚖️ Neutral"
        rsi_message.append(f"14-Day: {rsi14:.1f} ({rsi14_status})")
    
    if rsi_message:
        message += "\n\n**🔔 RSI Indicators:**\n" + "\n".join(rsi_message)
    
    await ctx.send(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)