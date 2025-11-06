#!/usr/bin/env python3
"""
簡単なAPIテストスクリプト
"""

import yfinance as yf

def test_yfinance():
    """yfinanceライブラリのテスト"""
    print("=" * 60)
    print("Yahoo! Finance API テスト")
    print("=" * 60)

    # トヨタ自動車のデータを取得
    ticker = "7203.T"
    print(f"\n銘柄: {ticker} (トヨタ自動車)")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")

        print(f"✓ 企業名: {info.get('longName', 'N/A')}")
        print(f"✓ 現在価格: {info.get('currentPrice', 'N/A')}")
        print(f"✓ 通貨: {info.get('currency', 'N/A')}")
        print(f"✓ 時価総額: {info.get('marketCap', 'N/A')}")

        if not hist.empty:
            latest = hist.iloc[-1]
            print(f"✓ 最新終値: {latest['Close']:.2f}")
            print(f"✓ 出来高: {int(latest['Volume'])}")
            print(f"✓ 取得データ日数: {len(hist)}")

        print("\n✅ テスト成功: Yahoo! Finance APIからデータを取得できました")
        return True

    except Exception as e:
        print(f"\n❌ テスト失敗: {str(e)}")
        return False

if __name__ == "__main__":
    test_yfinance()
