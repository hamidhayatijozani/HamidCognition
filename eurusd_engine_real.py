import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import random
try:
    import yfinance as yf # Real-world dependency
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance not installed. Using simulated data fallback.")

# ==============================================================================
# MOCK/SIMULATION INTERFACE (Replaces MT5 for sandbox execution)
# ==============================================================================

class MockMT5:
    """شبیه‌ساز MetaTrader 5 برای اجرای کد در محیط بدون اتصال واقعی"""
    
    TIMEFRAME_M5 = 5
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    TRADE_RETCODE_DONE = 10009
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    
    def __init__(self):
        self.is_initialized = False
        self.account_balance = 10000.0
        self.account_equity = 10000.0
        self.open_positions = {}
        self.next_ticket = 100000
        self.current_price = 1.09500
        
    def initialize(self):
        self.is_initialized = True
        return True
        
    def login(self, account_id, password, server):
        return True # Always succeed in mock
        
    def last_error(self):
        return 0
        
    def account_info(self):
        class AccountInfo:
            def __init__(self, balance, equity):
                self.balance = balance
                self.equity = equity
                self.margin = 500.0
                self.margin_free = self.equity - self.margin
                self.leverage = 500
        return AccountInfo(self.account_balance, self.account_equity)

    def symbol_info(self, symbol):
        class SymbolInfo:
            def __init__(self):
                self.spread = random.uniform(1.0, 2.0) # Mock spread
                self.point = 0.00001
        return SymbolInfo()

    def symbol_info_tick(self, symbol):
        # Simulate a small price movement
        self.current_price += random.uniform(-0.0001, 0.0001)
        
        class TickInfo:
            def __init__(self, price):
                self.ask = price + 0.00002 # Ask is slightly higher than bid
                self.bid = price
        return TickInfo(self.current_price)

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        # This is now handled by YFinanceData class in the real version
        return []

    def order_send(self, request):
        class OrderResult:
            def __init__(self, retcode, comment, order=None):
                self.retcode = retcode
                self.comment = comment
                self.order = order
        
        if request['type'] == self.ORDER_TYPE_BUY or request['type'] == self.ORDER_TYPE_SELL:
            # Simulate successful order placement
            ticket = self.next_ticket
            self.next_ticket += 1
            
            # Record position
            self.open_positions[ticket] = {
                'ticket': ticket,
                'type': request['type'],
                'volume': request['volume'],
                'price_open': request['price'],
                'profit': 0.0,
                'time': int(datetime.now().timestamp()),
                'symbol': request['symbol']
            }
            return OrderResult(self.TRADE_RETCODE_DONE, "Order executed", order=ticket)
        
        return OrderResult(99999, "Mock order failed")

    def positions_get(self, ticket=None, symbol=None):
        # Update mock profit
        for pos in self.open_positions.values():
            current_tick = self.symbol_info_tick(pos['symbol'])
            current_price = current_tick.bid if pos['type'] == self.ORDER_TYPE_SELL else current_tick.ask
            
            if pos['type'] == self.ORDER_TYPE_BUY:
                pos['profit'] = (current_price - pos['price_open']) * 100000 * pos['volume']
            else: # SELL
                pos['profit'] = (pos['price_open'] - current_price) * 100000 * pos['volume']
        
        # Return positions
        class Position:
            def __init__(self, data):
                self.__dict__.update(data)
        
        if ticket:
            return [Position(self.open_positions[ticket])] if ticket in self.open_positions else []
        
        return [Position(data) for data in self.open_positions.values()]

# Use the mock MT5
mt5 = MockMT5()

# ==============================================================================
# REAL-WORLD DATA SOURCE (YFinance)
# ==============================================================================

class YFinanceData:
    """دریافت داده‌های EUR/USD از yfinance"""
    
    def __init__(self, symbol="EURUSD=X"):
        self.symbol = symbol
        
    def get_historical_data(self, interval="5m", period="5d"):
        """دریافت داده‌های تاریخی"""
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(interval=interval, period=period)
            df.columns = [col.lower() for col in df.columns]
            df = df.rename(columns={'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low'})
            return df
        except Exception as e:
            print(f"❌ خطای دریافت داده از yfinance: {e}")
            # Fallback to simulated data if yfinance fails (e.g., in sandbox)
            return self._simulate_data()

    def _simulate_data(self):
        """شبیه‌سازی داده‌های تاریخی برای اجرای کد در محیط محدود"""
        print("⚠️ استفاده از داده‌های شبیه‌سازی شده برای تحلیل (yfinance نصب نیست یا خطا داد).")
        data = []
        base_price = 1.09000
        for i in range(100):
            price = base_price + (i / 100) * 0.01 + random.uniform(-0.001, 0.001)
            data.append({
                'time': datetime.now() - timedelta(minutes=100 - i),
                'open': price - 0.0001,
                'high': price + 0.0002,
                'low': price - 0.0002,
                'close': price,
            })
        df = pd.DataFrame(data)
        df = df.set_index('time')
        return df

# ==============================================================================
# HAMID FOREX ENGINE (Refactored for Real-World Data)
# ==============================================================================

class HamidForexEngine:
    """موتور عملیاتی معاملات EUR/USD با منطق P-S-T و داده واقعی"""
    
    def __init__(self, P=0.88, S=0.78, T=0.40):
        # پارامترهای شناختی YOU
        self.P = P  # نفوذ در اخبار
        self.S = S  # ترکیب تکنیکال  
        self.T = T  # تثبیت نوسانات
        
        # اتصال به MT5 (Mock)
        self.connected = False
        self.connect_mt5()
        
        # منبع داده واقعی
        self.data_source = YFinanceData()
        
        # وضعیت معاملاتی
        self.daily_trades = 0
        self.max_daily_trades = 5
        
        # تنظیمات EUR/USD
        self.symbol = "EURUSD"
        self.lot_size = 0.01  # حداقل لات
        self.spread_limit = 2.5  # حداکثر اسپرد (پوینت)
        
    def connect_mt5(self):
        """اتصال به MetaTrader 5 (Mock)"""
        if not mt5.initialize():
            print("❌ Failed to initialize MT5 Mock")
            return False
            
        # Mock login is always successful
        mt5.login(123456, "mock_pass", "Mock-Server")
        print(f"✅ Connected to MT5 Mock Account")
        self.connected = True
        self.account_info = mt5.account_info()
        return True
    
    def get_market_data(self, interval="5m", period="5d"):
        """دریافت داده‌های بازار از YFinance"""
        # Note: EURUSD=X is the Yahoo Finance symbol for EUR/USD
        df = self.data_source.get_historical_data(interval=interval, period=period)
        return df
    
    def calculate_rsi(self, prices, period=14):
        """محاسبه RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_pst_signal(self, df):
        """محاسبه سیگنال بر اساس پارامترهای P-S-T"""
        
        # محاسبه اندیکاتورها
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['rsi'] = self.calculate_rsi(df['close'])
        
        # سیگنال تکنیکال (S)
        tech_signal = 0
        
        # اطمینان از وجود داده کافی
        if df.empty or df['close'].isnull().all() or len(df) < 50:
            return "HOLD", 0.0, "Not enough data for technical analysis."

        last_close = df['close'].iloc[-1]
        sma_20_last = df['sma_20'].iloc[-1]
        sma_50_last = df['sma_50'].iloc[-1]
        rsi_last = df['rsi'].iloc[-1]
        
        # منطق S: ترکیب تکنیکال
        if pd.notna(sma_20_last) and pd.notna(sma_50_last):
            if sma_20_last > sma_50_last:
                tech_signal += 0.3 * self.S  # روند صعودی
            else:
                tech_signal -= 0.3 * self.S  # روند نزولی
        
        if pd.notna(rsi_last):
            if rsi_last < 30:
                tech_signal += 0.2 * self.S  # اشباع فروش
            elif rsi_last > 70:
                tech_signal -= 0.2 * self.S  # اشباع خرید
        
        # سیگنال نوسانات (T)
        volatility = df['close'].pct_change().std() * 100
        # Adjusted threshold for real-world data
        if volatility < 0.05: 
            stability_signal = 0.2 * self.T  # بازار آرام
        elif volatility > 0.15: 
            stability_signal = -0.2 * self.T  # بازار پرنوسان
        else:
            stability_signal = 0
        
        # سیگنال اخبار (P) - شبیه‌سازی
        # P (نفوذ) به عنوان یک ضریب تقویت‌کننده برای سیگنال تکنیکال عمل می‌کند
        news_signal = random.uniform(-0.1, 0.1) * self.P
        
        # ترکیب سیگنال‌ها
        total_signal = tech_signal + stability_signal + news_signal
        
        # تصمیم‌گیری
        if total_signal > 0.15:
            action = "BUY"
            rationale = f"Strong BUY signal based on S ({tech_signal:.3f}) and T ({stability_signal:.3f}) with P ({news_signal:.3f}) reinforcement. Last Close: {last_close:.5f}"
        elif total_signal < -0.15:
            action = "SELL"
            rationale = f"Strong SELL signal based on S ({tech_signal:.3f}) and T ({stability_signal:.3f}) with P ({news_signal:.3f}) reinforcement. Last Close: {last_close:.5f}"
        else:
            action = "HOLD"
            rationale = f"Neutral signal. Total signal ({total_signal:.3f}) is within the HOLD range. Last Close: {last_close:.5f}"

        return action, total_signal, rationale
    
    def check_trading_conditions(self):
        """بررسی شرایط معامله (Mock)"""
        if not self.connected:
            return False, "Not connected to MT5 Mock"
        
        if self.daily_trades >= self.max_daily_trades:
            return False, "Daily trade limit reached"
        
        # بررسی اسپرد (Mock)
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info:
            spread = symbol_info.spread
            if spread > self.spread_limit:
                return False, f"Spread too high: {spread}"
        
        return True, "OK"
    
    def place_order(self, action, lot_size=None, stop_loss=50, take_profit=100):
        """ارسال سفارش به MT5 (Mock)"""
        
        can_trade, reason = self.check_trading_conditions()
        if not can_trade:
            return {"status": "rejected", "reason": reason}
        
        symbol_info = mt5.symbol_info(self.symbol)
        tick = mt5.symbol_info_tick(self.symbol)
        price = tick.ask if action == "BUY" else tick.bid
        
        if lot_size is None:
            lot_size = self.lot_size
        
        # محاسبه حد ضرر و سود
        point = symbol_info.point
        if action == "BUY":
            sl = price - stop_loss * point
            tp = price + take_profit * point
            order_type = mt5.ORDER_TYPE_BUY
        else:  # SELL
            sl = price + stop_loss * point
            tp = price - take_profit * point
            order_type = mt5.ORDER_TYPE_SELL
        
        # ارسال سفارش (Mock)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "magic": 234000,
            "comment": f"HAMID-PST-{action}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                "status": "error",
                "retcode": result.retcode,
                "reason": f"Order failed: {result.comment}"
            }
        
        self.daily_trades += 1
        
        return {
            "status": "success",
            "ticket": result.order,
            "price": price,
            "action": action,
            "lots": lot_size,
            "sl": sl,
            "tp": tp
        }
    
    def monitor_positions(self):
        """مانیتورینگ معاملات باز (Mock)"""
        if not self.connected:
            return []
        
        positions = mt5.positions_get(symbol=self.symbol)
        status = []
        
        for pos in positions:
            current_tick = mt5.symbol_info_tick(self.symbol)
            current_price = current_tick.bid if pos.type == mt5.ORDER_TYPE_SELL else current_tick.ask
            
            # Mock profit calculation is handled inside MockMT5.positions_get
            profit = pos.profit
            
            pips = (current_price - pos.price_open) * 10000 if pos.type == mt5.ORDER_TYPE_BUY else (pos.price_open - current_price) * 10000
            
            status.append({
                "ticket": pos.ticket,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "lots": pos.volume,
                "entry": pos.price_open,
                "current": current_price,
                "profit": profit,
                "pips": pips,
                "time": datetime.fromtimestamp(pos.time)
            })
        
        return status
    
    def get_account_summary(self):
        """گزارش حساب (Mock)"""
        if not self.connected:
            return None
        
        account = mt5.account_info()
        positions = self.monitor_positions()
        total_profit = sum(p['profit'] for p in positions)
        
        return {
            "balance": account.balance,
            "equity": account.equity,
            "profit": total_profit,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "leverage": account.leverage,
            "positions_count": len(positions),
            "daily_trades": self.daily_trades
        }

    def run_analysis_and_trade(self):
        """اجرای کامل تحلیل و معامله"""
        
        # 1. دریافت داده واقعی
        df = self.get_market_data()
        if df is None or df.empty:
            return {"status": "error", "message": "Failed to get market data."}
        
        # 2. محاسبه سیگنال P-S-T
        action, signal_strength, rationale = self.calculate_pst_signal(df)
        
        result = {
            "analysis": {
                "action": action,
                "signal_strength": signal_strength,
                "rationale": rationale,
                "P": self.P, "S": self.S, "T": self.T
            },
            "trade": None,
            "account": self.get_account_summary()
        }
        
        # 3. تصمیم به معامله
        if action in ["BUY", "SELL"]:
            # 4. بررسی شرایط و ارسال سفارش
            trade_result = self.place_order(action)
            result["trade"] = trade_result
        else:
            result["trade"] = {"status": "skipped", "reason": "HOLD signal."}
            
        return result

# ==============================================================================
# MAIN EXECUTION SCRIPT
# ==============================================================================

def main():
    print("🚀 فعال‌سازی موتور عملیاتی EUR/USD (داده واقعی + شبیه‌سازی معامله)")
    print("=" * 60)
    
    # ایجاد موتور با پارامترهای شناختی حمید
    engine = HamidForexEngine(P=0.88, S=0.78, T=0.40)
    
    # اجرای تحلیل و معامله
    trade_run_1 = engine.run_analysis_and_trade()
    
    print("\n--- گزارش تحلیل و معامله ---")
    print(f"تصمیم: {trade_run_1['analysis']['action']} (قدرت سیگنال: {trade_run_1['analysis']['signal_strength']:.3f})")
    print(f"منطق: {trade_run_1['analysis']['rationale']}")
    print(f"وضعیت معامله: {trade_run_1['trade']['status']}")
    if trade_run_1['trade']['status'] == 'success':
        print(f"تیکت: {trade_run_1['trade']['ticket']}, قیمت ورود: {trade_run_1['trade']['price']:.5f}")
    
    # گزارش نهایی
    summary = engine.get_account_summary()
    print("\n--- گزارش نهایی حساب (شبیه‌سازی) ---")
    print(f"بالانس: ${summary['balance']:.2f}")
    print(f"اکوئیتی: ${summary['equity']:.2f}")
    print(f"سود/ضرر باز: ${summary['profit']:.2f}")
    print(f"تعداد معاملات باز: {summary['positions_count']}")
    print(f"تعداد معاملات روزانه: {summary['daily_trades']}")
    
    # ذخیره گزارش نهایی
    with open('real_world_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(trade_run_1, f, ensure_ascii=False, indent=2, default=str)
    print("\n✅ گزارش تحلیل در real_world_analysis_report.json ذخیره شد.")

if __name__ == "__main__":
    main()
