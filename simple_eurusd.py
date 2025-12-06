import numpy as np
import json
from datetime import datetime

class Simple_EURUSD_Engine:
    """نسخه ساده‌شده موتور شناختی EUR/USD"""
    
    def __init__(self, P=0.8, S=0.7, T=0.6):
        # Since numpy is not guaranteed to be installed, we use standard math functions
        # and simple min/max for clipping, which is equivalent to np.clip for this simple case.
        self.P = max(0, min(P, 1))  # نفوذ اخبار
        self.S = max(0, min(S, 1))  # سنتز تکنیکال
        self.T = max(0, min(T, 1))  # تثبیت نوسانات
        
    def analyze(self, current_price, trend="neutral"):
        """
        تحلیل ساده EUR/USD
        current_price: قیمت فعلی (مثلاً 1.0950)
        trend: روند بازار (up/down/neutral)
        """
        
        # محاسبه امتیاز
        score = 0
        
        # تأثیر پارامتر P (اخبار)
        score += self.P * 0.3
        
        # تأثیر پارامتر S (تکنیکال)
        if trend == "up":
            score += self.S * 0.4
        elif trend == "down":
            score -= self.S * 0.4
            
        # تأثیر پارامتر T (ثبات)
        score += self.T * 0.3
        
        # تصمیم‌گیری
        if score > 0.2:
            action = "BUY"
            confidence = min(score, 0.95)
        elif score < -0.2:
            action = "SELL"
            confidence = min(abs(score), 0.95)
        else:
            action = "HOLD"
            confidence = 0.5
            
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "parameters": {"P": self.P, "S": self.S, "T": self.T},
            "timestamp": datetime.now().isoformat()
        }
    
    def save_state(self, filename="eurusd_state.json"):
        """ذخیره وضعیت"""
        state = {
            "P": self.P,
            "S": self.S,
            "T": self.T,
            "last_analysis": datetime.now().isoformat()
        }
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)

# تست سریع
if __name__ == "__main__":
    print("🧠 تست موتور شناختی ساده EUR/USD")
    print("=" * 40)
    
    # ایجاد موتور با پارامترهای حمید
    engine = Simple_EURUSD_Engine(P=0.88, S=0.78, T=0.40)
    
    # تحلیل نمونه
    result = engine.analyze(current_price=1.0950, trend="up")
    
    print(f"💰 قیمت: 1.0950")
    print(f"📈 تصمیم: {result['action']}")
    print(f"🔒 اطمینان: {result['confidence']:.1%}")
    print(f"📊 امتیاز: {result['score']:.3f}")
    print(f"⚙️ پارامترها: P={result['parameters']['P']}, S={result['parameters']['S']}, T={result['parameters']['T']}")
    
    # ذخیره وضعیت
    engine.save_state()
    print("💾 وضعیت ذخیره شد در eurusd_state.json")
