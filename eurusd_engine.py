import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import random

# ==============================================================================
# MOCK/SIMULATION INTERFACE (Replaces MT5 and yfinance for sandbox execution)
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
        # Generate mock historical data
        data = []
        base_price = 1.09000
        for i in range(count):
            price = base_price + (i / count) * 0.01 + random.uniform(-0.001, 0.001)
            data.append({
                'time': int((datetime.now() - timedelta(minutes=count - i)).timestamp()),
                'open': price - 0.0001,
                'high': price + 0.0002,
                'low': price - 0.0002,
                'close': price,
                'tick_volume': random.randint(100, 500)
            })
        return data

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
# HAMID FOREX ENGINE (Refactored to use MockMT5)
# ==============================================================================

class HamidForexEngine:
    """موتور عملیاتی معاملات EUR/USD با منطق P-S-T"""
    
    def __init__(self, P=0.88, S=0.78, T=0.40):
        # پارامترهای شناختی YOU
        self.P = P  # نفوذ در اخبار
        self.S = S  # ترکیب تکنیکال  
        self.T = T  # تثبیت نوسانات
        
        # اتصال به MT5 (Mock)
        self.connected = False
        self.connect_mt5()
        
        # وضعیت معاملاتی
        self.positions = []
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
    
    def get_market_data(self, timeframe=mt5.TIMEFRAME_M5, bars=100):
        """دریافت داده‌های بازار از MT5 (Mock)"""
        if not self.connected:
            return None
            
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, bars)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
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
        last_close = df['close'].iloc[-1]
        sma_20_last = df['sma_20'].iloc[-1]
        sma_50_last = df['sma_50'].iloc[-1]
        rsi_last = df['rsi'].iloc[-1]
        
        # اطمینان از وجود داده کافی
        if pd.isna(sma_20_last) or pd.isna(sma_50_last) or pd.isna(rsi_last):
            return "HOLD", 0.0, "Not enough data for technical analysis."

        # منطق S: ترکیب تکنیکال
        if sma_20_last > sma_50_last:
            tech_signal += 0.3 * self.S  # روند صعودی
        else:
            tech_signal -= 0.3 * self.S  # روند نزولی
        
        if rsi_last < 30:
            tech_signal += 0.2 * self.S  # اشباع فروش
        elif rsi_last > 70:
            tech_signal -= 0.2 * self.S  # اشباع خرید
        
        # سیگنال نوسانات (T)
        volatility = df['close'].pct_change().std() * 100
        if volatility < 0.05: # Adjusted threshold for mock data
            stability_signal = 0.2 * self.T  # بازار آرام
        elif volatility > 0.15: # Adjusted threshold for mock data
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
            rationale = f"Strong BUY signal based on S ({tech_signal:.2f}) and T ({stability_signal:.2f}) with P ({news_signal:.2f}) reinforcement."
        elif total_signal < -0.15:
            action = "SELL"
            rationale = f"Strong SELL signal based on S ({tech_signal:.2f}) and T ({stability_signal:.2f}) with P ({news_signal:.2f}) reinforcement."
        else:
            action = "HOLD"
            rationale = f"Neutral signal. Total signal ({total_signal:.2f}) is within the HOLD range."

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
        
        # 1. دریافت داده
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
    print("🚀 فعال‌سازی موتور عملیاتی EUR/USD (شبیه‌سازی)")
    print("=" * 50)
    
    # ایجاد موتور با پارامترهای شناختی حمید
    engine = HamidForexEngine(P=0.88, S=0.78, T=0.40)
    
    # اجرای تحلیل و معامله
    trade_run_1 = engine.run_analysis_and_trade()
    
    print("\n--- اجرای اول ---")
    print(f"تصمیم: {trade_run_1['analysis']['action']} (قدرت سیگنال: {trade_run_1['analysis']['signal_strength']:.3f})")
    print(f"منطق: {trade_run_1['analysis']['rationale']}")
    print(f"وضعیت معامله: {trade_run_1['trade']['status']}")
    if trade_run_1['trade']['status'] == 'success':
        print(f"تیکت: {trade_run_1['trade']['ticket']}, قیمت ورود: {trade_run_1['trade']['price']:.5f}")
    
    # اجرای دوم برای شبیه‌سازی ادامه کار
    trade_run_2 = engine.run_analysis_and_trade()
    
    print("\n--- اجرای دوم ---")
    print(f"تصمیم: {trade_run_2['analysis']['action']} (قدرت سیگنال: {trade_run_2['analysis']['signal_strength']:.3f})")
    print(f"وضعیت معامله: {trade_run_2['trade']['status']}")
    
    # گزارش نهایی
    summary = engine.get_account_summary()
    print("\n--- گزارش نهایی حساب (شبیه‌سازی) ---")
    print(f"بالانس: ${summary['balance']:.2f}")
    print(f"اکوئیتی: ${summary['equity']:.2f}")
    print(f"سود/ضرر باز: ${summary['profit']:.2f}")
    print(f"تعداد معاملات باز: {summary['positions_count']}")
    print(f"تعداد معاملات روزانه: {summary['daily_trades']}")
    
    # ذخیره گزارش نهایی
    with open('eurusd_trade_report.json', 'w', encoding='utf-8') as f:
        json.dump(trade_run_1, f, ensure_ascii=False, indent=2, default=str)
    print("\n✅ گزارش معامله در eurusd_trade_report.json ذخیره شد.")

if __name__ == "__main__":
    main()
