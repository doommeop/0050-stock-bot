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
    drop_percent = (current_price - yesterday_close) / yesterday_close * 100
    timestamp = data.index[-1].strftime("%Y-%m-%d %H:%M:%S")

    return current_price, drop_percent, yesterday_close, timestamp

def send_bark_notification(current_price, drop_percent, yesterday_close, timestamp):
    bark_token = os.getenv("bark-key")
    if not bark_token:
        return "❌ 未設定 BARK_TOKEN"
    bark_url_base = f"https://api.day.app/{bark_token}"
    title = "0050 盤中報告"
    body = f"{timestamp}\n漲跌幅：{drop_percent:.2f}%\n現價：{current_price:.2f}\n昨日收：{yesterday_close:.2f}"
    url = f"{bark_url_base}/{title}/{body}?group=stock&sound=alarm"
    requests.get(url)

@app.route("/")
def index():
    # 這裡使用 redirect 跳轉到 /report
    return redirect(url_for("stock_report"))

@app.route("/health")
def health():
    return "OK", 200

@app.route("/report")
def stock_report():
    result = get_0050_price_and_change()
    if result:
        current_price, drop_percent, yesterday_close, timestamp = result
        send_bark_notification(current_price, drop_percent, yesterday_close, timestamp)
        return Response("傳送成功", mimetype="text/plain")
    else:
        return Response("❌ 資料不足或無法取得", mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

