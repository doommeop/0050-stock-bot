from flask import Flask, redirect, url_for, Response
import yfinance as yf
import os
import requests

app = Flask(__name__)

def get_0050_price_and_change():
    stock = yf.Ticker("0050.TW")
    data = stock.history(period="2d", interval="1m")
    if data.empty or len(data) < 2:
        return None

    data_by_day = data.groupby(data.index.date)
    if len(data_by_day) < 2:
        return None

    yesterday = sorted(list(data_by_day.groups.keys()))[-2]
    yesterday_close = data_by_day.get_group(yesterday).iloc[-1]['Close']
    latest_row = data.iloc[-1]
    current_price = latest_row['Close']
    drop_percent = (current_price - yesterday_close) / yesterday_close
    timestamp = data.index[-1].strftime("%Y-%m-%d %H:%M:%S")

    return current_price, drop_percent, yesterday_close, timestamp

def get_vix_if_high():
    vix = yf.Ticker("^VIX")
    vix_data = vix.history(period="1d")
    if vix_data.empty:
        return None
    vix_value = vix_data['Close'].iloc[-1]
    if vix_value > 32:
        return vix_value
    return None

def send_bark_notification(title, body):
    bark_token = os.getenv("bark-key")
    if not bark_token:
        return "❌ 未設定 BARK_TOKEN"
    bark_url = f"https://api.day.app/{bark_token}/{title}/{body}?group=stock&sound=alarm"
    requests.get(bark_url)

@app.route("/")
def index():
    return redirect(url_for("stock_report"))

@app.route("/health")
def health():
    return "OK", 200

@app.route("/report")
def stock_report():
    messages = []

    # 0050 判斷與通知
    result = get_0050_price_and_change()
    if result:
        current_price, drop_percent, yesterday_close, timestamp = result
        if drop_percent <= -0.015:
            body = f"{timestamp}\n漲跌幅：{drop_percent*100:.2f}%\n現價：{current_price:.2f}\n昨日收：{yesterday_close:.2f}"
            send_bark_notification("0050 跌幅警告", body)
            messages.append("✅ 傳送 0050 通知")

    # VIX 判斷與通知
    vix_value = get_vix_if_high()
    if vix_value:
        body = f"VIX 指數過高：{vix_value:.2f}"
        send_bark_notification("⚠️ VIX 警告", body)
        messages.append("✅ 傳送 VIX 通知")

    return Response("\n".join(messages) if messages else "✅ 無需通知", mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

