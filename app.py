from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import traceback

app = Flask(__name__, static_folder='static')
CORS(app)

def format_ticker(ticker):
    """日本の株式コードをYahoo! Finance形式に変換"""
    if not ticker.endswith('.T'):
        return f"{ticker}.T"
    return ticker

@app.route('/')
def index():
    """メインページを表示"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/favicon.ico')
def favicon():
    """favicon.icoのリクエストを処理（404エラー回避）"""
    return '', 204

@app.route('/api/stock/<ticker>')
def get_stock_info(ticker):
    """株価情報を取得"""
    try:
        # 日本の株式コード形式に変換
        formatted_ticker = format_ticker(ticker)
        stock = yf.Ticker(formatted_ticker)

        # 株価情報を取得
        info = stock.info
        hist = stock.history(period="1mo")

        if hist.empty:
            return jsonify({'error': '株価データが見つかりません'}), 404

        latest = hist.iloc[-1]

        # レスポンスデータを構築
        response = {
            'ticker': ticker,
            'name': info.get('longName', info.get('shortName', ticker)),
            'current_price': float(latest['Close']),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'volume': int(latest['Volume']),
            'previous_close': float(info.get('previousClose', latest['Close'])),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'week_52_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'week_52_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'currency': info.get('currency', 'JPY'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'history': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                }
                for date, row in hist.iterrows()
            ]
        }

        # 変化率を計算
        if response['previous_close'] and response['previous_close'] != 'N/A':
            change = response['current_price'] - response['previous_close']
            change_percent = (change / response['previous_close']) * 100
            response['change'] = float(change)
            response['change_percent'] = float(change_percent)

        return jsonify(response)

    except Exception as e:
        print(f"Error getting stock info: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'株価情報の取得に失敗しました: {str(e)}'}), 500

@app.route('/api/news/<ticker>')
def get_news(ticker):
    """株式に関するニュースを取得"""
    try:
        formatted_ticker = format_ticker(ticker)
        stock = yf.Ticker(formatted_ticker)

        # Yahoo! Financeからニュースを取得
        news_data = stock.news

        if not news_data:
            # ニュースがない場合はダミーのニュースを返す
            return jsonify({
                'ticker': ticker,
                'news': [
                    {
                        'title': '最新ニュースは現在取得できません',
                        'publisher': 'システム',
                        'link': '#',
                        'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'summary': 'Yahoo! Financeからのニュースフィードが利用できません。後ほど再度お試しください。'
                    }
                ]
            })

        # ニュースを最大5件に制限
        news_list = []
        for item in news_data[:5]:
            news_list.append({
                'title': item.get('title', 'タイトルなし'),
                'publisher': item.get('publisher', '不明'),
                'link': item.get('link', '#'),
                'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'summary': item.get('summary', item.get('title', ''))[:200] + '...'
            })

        return jsonify({
            'ticker': ticker,
            'news': news_list
        })

    except Exception as e:
        print(f"Error getting news: {str(e)}")
        traceback.print_exc()
        # エラーの場合もダミーデータを返す
        return jsonify({
            'ticker': ticker,
            'news': [
                {
                    'title': f'{ticker}に関する最新情報',
                    'publisher': 'システム通知',
                    'link': '#',
                    'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'summary': 'ニュースの取得中にエラーが発生しました。Yahoo! Financeのニュースフィードが一時的に利用できない可能性があります。'
                }
            ]
        }), 200

@app.route('/api/predict/<ticker>')
def predict_stock(ticker):
    """3ヶ月先の株価を予測"""
    try:
        formatted_ticker = format_ticker(ticker)
        stock = yf.Ticker(formatted_ticker)

        # 過去1年のデータを取得
        hist = stock.history(period="1y")

        if hist.empty or len(hist) < 30:
            return jsonify({'error': '予測に十分なデータがありません'}), 404

        # データの準備
        hist = hist.reset_index()
        hist['Days'] = (hist['Date'] - hist['Date'].min()).dt.days

        # 線形回帰モデルで予測
        X = hist['Days'].values.reshape(-1, 1)
        y = hist['Close'].values

        model = LinearRegression()
        model.fit(X, y)

        # 現在の日数
        current_days = hist['Days'].max()

        # 3ヶ月先（約90日）の予測
        future_days = current_days + 90
        predicted_price = model.predict([[future_days]])[0]

        # 移動平均を計算
        ma_20 = hist['Close'].tail(20).mean()
        ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else hist['Close'].mean()

        # トレンド分析
        recent_trend = hist['Close'].tail(30).values
        trend_direction = "上昇" if recent_trend[-1] > recent_trend[0] else "下降"

        # ボラティリティ計算
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年率ボラティリティ

        # 信頼区間の計算（簡易版）
        prediction_std = returns.std() * predicted_price * np.sqrt(90)
        confidence_upper = predicted_price + (1.96 * prediction_std)
        confidence_lower = predicted_price - (1.96 * prediction_std)

        # 現在の価格
        current_price = hist['Close'].iloc[-1]

        # 予測変化率
        predicted_change = ((predicted_price - current_price) / current_price) * 100

        response = {
            'ticker': ticker,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_change_percent': float(predicted_change),
            'prediction_date': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'confidence_interval': {
                'upper': float(confidence_upper),
                'lower': float(confidence_lower)
            },
            'indicators': {
                'ma_20': float(ma_20),
                'ma_50': float(ma_50),
                'volatility': float(volatility * 100),
                'trend': trend_direction
            },
            'analysis': self_generate_analysis(
                current_price, predicted_price, predicted_change,
                trend_direction, volatility, ma_20, ma_50
            ),
            'disclaimer': 'この予測は過去のデータに基づく統計的な推定であり、投資助言ではありません。実際の投資判断は自己責任で行ってください。'
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error predicting stock: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'株価予測に失敗しました: {str(e)}'}), 500

def self_generate_analysis(current_price, predicted_price, change_percent, trend, volatility, ma_20, ma_50):
    """株価分析テキストを生成"""
    analysis = []

    # 価格トレンド分析
    if change_percent > 10:
        analysis.append(f"3ヶ月後の予測価格は現在より{change_percent:.1f}%上昇し、{predicted_price:.0f}円になると予測されます。強い上昇トレンドが見られます。")
    elif change_percent > 0:
        analysis.append(f"3ヶ月後の予測価格は現在より{change_percent:.1f}%上昇し、{predicted_price:.0f}円になると予測されます。緩やかな上昇傾向です。")
    elif change_percent > -10:
        analysis.append(f"3ヶ月後の予測価格は現在より{abs(change_percent):.1f}%下降し、{predicted_price:.0f}円になると予測されます。緩やかな下降傾向です。")
    else:
        analysis.append(f"3ヶ月後の予測価格は現在より{abs(change_percent):.1f}%下降し、{predicted_price:.0f}円になると予測されます。下降トレンドが見られます。")

    # 移動平均分析
    if current_price > ma_20 and current_price > ma_50:
        analysis.append("現在価格は20日・50日移動平均を上回っており、強気のシグナルです。")
    elif current_price < ma_20 and current_price < ma_50:
        analysis.append("現在価格は20日・50日移動平均を下回っており、弱気のシグナルです。")
    else:
        analysis.append("移動平均線と価格が交錯しており、トレンド転換の可能性があります。")

    # ボラティリティ分析
    if volatility > 0.3:
        analysis.append(f"ボラティリティが{volatility*100:.1f}%と高く、価格変動が大きい銘柄です。リスクが高いことに注意してください。")
    elif volatility > 0.15:
        analysis.append(f"ボラティリティは{volatility*100:.1f}%で、標準的な価格変動範囲内です。")
    else:
        analysis.append(f"ボラティリティが{volatility*100:.1f}%と低く、比較的安定した値動きの銘柄です。")

    # 総合評価
    if change_percent > 5 and current_price > ma_20:
        analysis.append("総合的に見て、上昇トレンドが継続する可能性があります。")
    elif change_percent < -5 and current_price < ma_20:
        analysis.append("総合的に見て、下降トレンドが継続する可能性があります。")
    else:
        analysis.append("総合的に見て、横ばいまたは方向感の定まらない相場が予想されます。")

    return " ".join(analysis)

if __name__ == '__main__':
    print("=" * 60)
    print("日本株価分析・予測アプリ")
    print("=" * 60)
    print("サーバーを起動しています...")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
