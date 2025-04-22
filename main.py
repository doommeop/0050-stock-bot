# main.py
from flask import Flask
import yfinance as yf
import datetime

app = Flask(__name__)

@app.route("/")
def stock_report():
    stock = yf.Ticker("0050.TW")
    data = stock.history(period="2d", interval="1m")
    if data.empty or len(data) < 2:
        return "❌ 無法取得0050資料"

    data_by_day = data.groupby(data.index.date)
    if len(data_by_day) < 2:
        return "❌ 資料不足"

    yesterday = sorted(list(data_by_day.groups.keys()))[-2]
    yesterday_close = data_by_day.get_group(yesterday).iloc[-1]['Close']
    latest_row = data.iloc[-1]
    current_price = latest_row['Close']
    drop_percent = (current_price - yesterday_close) / yesterday_close * 100
    timestamp = data.index[-1].strftime("%Y-%m-%d %H:%M:%S")

    return f"0050 即時報告\n時間：{timestamp}\n現價：{current_price:.2f}\n昨日收：{yesterday_close:.2f}\n漲跌：{drop_percent:.2f}%"

if __name__ == "__main__":
    app.run()
