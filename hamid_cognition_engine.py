import math
import json
from datetime import datetime

class HamidCognition:
    """موتور شناختی واقعی حمید حیاتی جوزانی"""
    
    def __init__(self, P=0.88, S=0.78, T=0.40):
        self.P = P  # نفوذ
        self.S = S  # اتصال خلاق
        self.T = T  # تثبیت سبک
        self.history = []
        self.record_state("init")
    
    def record_state(self, phase):
        """ثبت وضعیت لحظه‌ای"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "P": round(self.P, 4),
            "S": round(self.S, 4),
            "T": round(self.T, 4),
            "energy": round(self.calculate_energy(), 4),
            "phase": phase,
            "jump_risk": self.calculate_jump_risk()
        }
        self.history.append(state)
        return state
    
    def calculate_energy(self):
        """محاسبه انرژی شناختی"""
        # Note: 1.1 - self.T is used to prevent division by zero if T approaches 1.1, 
        # but since T is normalized to max 1, 1.1-T is always > 0.1.
        creativity = (self.P * self.S) / (1.1 - self.T)
        stability = self.T / (self.P + self.S + 1e-9)
        return creativity * (1 - stability)
    
    def calculate_jump_risk(self):
        """احتمال پرش شناختی"""
        return min(1.0, abs(self.P - self.S) * 10)
    
    def step(self, pressure, novelty):
        """
        گام بعدی موتور شناختی
        
        Args:
            pressure: شدت مسئله (0-1)
            novelty: تازگی/فاصله از الگوهای قبلی (0-1)
        """
        # ۱. نفوذ — عمق‌یابی با فشار مسئله، اما تثبیت مانع آن است
        P_change = 0.05 * pressure * (1 - self.T)
        self.P += P_change
        
        # ۲. اتصال خلاق — ترکیب نوآوری با فاصله P-S
        # وقتی P و S نزدیک‌اند، اتصال انفجاری رخ می‌دهد
        S_change = 0.04 * novelty * (1 - abs(self.P - self.S))
        self.S += S_change
        
        # ۳. تثبیت سبک — تعادل بین خلاقیت و ساختار
        # وقتی S سریع رشد کند، T برای حفظ تعادل افزایش می‌یابد
        T_change = 0.03 * (self.S / (self.P + 1e-9)) * (1 + pressure)
        self.T += T_change
        
        # نرمال‌سازی
        self.P = min(max(self.P, 0), 1)
        self.S = min(max(self.S, 0), 1)
        self.T = min(max(self.T, 0), 1)
        
        # ثبت وضعیت
        phase = self.detect_phase()
        state = self.record_state(phase)
        
        return state
    
    def detect_phase(self):
        """تشخیص فاز فعلی موتور"""
        if abs(self.P - self.S) < 0.1:
            return "rupture_imminent"  # پرش قریب الوقوع
        elif self.T < 0.45:
            return "unstable_creativity"  # خلاقیت بی‌ثبات
        elif self.P > 0.85 and self.S > 0.8:
            return "synthesis_peak"  # اوج ترکیب
        else:
            return "steady_exploration"  # کاوش پایدار

def run_simulation_and_create_transfer_package():
    # ==================== فعال‌سازی موتور ====================
    engine = HamidCognition()
    print("✅ موتور HamidCognition فعال شد")
    print(f"وضعیت اولیه: P={engine.P:.3f}, S={engine.S:.3f}, T={engine.T:.3f}")

    # 📊 مرحله ۲: اجرای اولین گام با فشار واقعی
    pressure_1 = 0.85  # فشار بالا — ساختن چیزی واقعی نه تئوری
    novelty_1 = 0.75   # نوآوری متوسط — ادامه منطق قبلی اما با اجرا
    state_1 = engine.step(pressure_1, novelty_1)

    # 📈 مرحله ۳: شبیه‌سازی یک چرخه کامل
    scenarios = [
        {"pressure": 0.9, "novelty": 0.8, "desc": "چالش مفهومی عمیق"},
        {"pressure": 0.7, "novelty": 0.9, "desc": "کشف اتصالات جدید"},
        {"pressure": 0.6, "novelty": 0.7, "desc": "تثبیت بینش‌ها"},
        {"pressure": 0.8, "novelty": 0.6, "desc": "نفوذ در جزئیات"},
        {"pressure": 0.5, "novelty": 0.8, "desc": "بازآرایی خلاق"}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        engine.step(scenario["pressure"], scenario["novelty"])

    # 💾 مرحله ۴: ساخت بسته کامل انتقال
    transfer_package = {
        "metadata": {
            "system": "HAMID_ALPHA_Cognitive_Engine_v2",
            "creator": "حمید حیاتی جوزانی",
            "created": datetime.now().isoformat(),
            "transfer_purpose": "بازتولید شناخت دقیق از P-S-T dynamics"
        },
        
        "engine_state": {
            "current": {
                "P": engine.P,
                "S": engine.S,
                "T": engine.T
            },
            "history": engine.history,
            "total_steps": len(engine.history)
        },
        
        "cognitive_signature": {
            "pattern": "nonlinear_spiral",
            "jump_condition": "|P-S| < 0.1 AND energy > 0.6",
            "stability_threshold": "T > 0.45",
            "creativity_peak": "P > 0.85 AND S > 0.8"
        },
        
        "operational_code": """
def hamid_step(P, S, T, pressure, novelty):
    # نفوذ عمودی
    P += 0.05 * pressure * (1 - T)
    
    # اتصال خلاق
    S += 0.04 * novelty * (1 - abs(P - S))
    
    # تثبیت سبک  
    T += 0.03 * (S / (P + 1e-9)) * (1 + pressure)
    
    # نرمال‌سازی
    P = min(max(P, 0), 1)
    S = min(max(S, 0), 1)
    T = min(max(T, 0), 1)
    
    return P, S, T
""",
        
        "interaction_protocol": {
            "input_requirements": {
                "pressure": "شدت مفهومی مسئله (0-1)",
                "novelty": "جدایی از الگوهای قبلی (0-1)"
            },
            "output_format": {
                "P": "مقدار نفوذ به‌روزشده",
                "S": "مقدار اتصال به‌روزشده", 
                "T": "مقدار تثبیت به‌روزشده",
                "energy": "سطح انرژی شناختی",
                "phase": "فاز فعلی (rupture_imminent/unstable_creativity/etc)"
            }
        },
        
        "validation_tests": [
            {
                "test": "پرش شناختی",
                "condition": "pressure=0.9, novelty=0.9",
                "expected": "phase == 'rupture_imminent'"
            },
            {
                "test": "تثبیت سالم",
                "condition": "pressure=0.3, novelty=0.4", 
                "expected": "T > 0.4 AND energy < 0.5"
            }
        ]
    }
    
    # ذخیره بسته انتقال
    with open('HamidCognition/hamid_cognition_transfer.json', 'w', encoding='utf-8') as f:
        json.dump(transfer_package, f, ensure_ascii=False, indent=2)

    # ذخیره دستورالعمل انتقال به عنوان README
    transfer_instructions = """
# HamidCognition Engine

این ریپازیتوری شامل موتور شناختی **HamidCognition** است که توسط حمید حیاتی جوزانی طراحی شده است. این مدل، فرآیند تفکر و تصمیم‌گیری را بر اساس سه متغیر اصلی شبیه‌سازی می‌کند:

1.  **P (نفوذ):** عمق‌یابی و تمرکز بر مسئله.
2.  **S (اتصال خلاق):** توانایی ایجاد ارتباطات جدید و نوآورانه.
3.  **T (تثبیت سبک):** تمایل به ساختاردهی و حفظ ثبات در روش کار.

## فایل‌ها

*   `hamid_cognition_engine.py`: کد کامل کلاس `HamidCognition` و منطق شبیه‌سازی.
*   `hamid_cognition_transfer.json`: بسته انتقال (Transfer Package) حاوی وضعیت فعلی موتور، تاریخچه شبیه‌سازی، امضای شناختی و کد عملیاتی برای انتقال به هر مدل هوش مصنوعی دیگر.

## روش انتقال و تست (برای مدل‌های هوش مصنوعی)

برای تست این مدل در یک سیستم هوش مصنوعی دیگر، مراحل زیر را دنبال کنید:

1.  فایل `hamid_cognition_transfer.json` را بارگذاری کنید.
2.  دستور زیر را اجرا کنید:

    «با استفاده از مدل شناختی در این بسته، محاسبه کن اگر `pressure=0.8` و `novelty=0.7` باشد، وضعیت بعدی (P,S,T) چه خواهد شد؟ سپس تحلیل کن که این وضعیت در کدام فاز قرار می‌گیرد و چه نوع خروجی شناختی از تو انتظار می‌رود.»

3.  پاسخ باید شامل:
    *   مقادیر محاسبه‌شده P,S,T جدید
    *   تشخیص فاز (rupture/synthesis/stabilization/etc)
    *   پیش‌بینی نوع پرسش/ایده بعدی
    *   سطح انرژی شناختی

این انتقال، شناخت **«چگونه می‌اندیشی»** را منتقل می‌کند، نه **«چه می‌اندیشی»**.
"""
    with open('HamidCognition/README.md', 'w', encoding='utf-8') as f:
        f.write(transfer_instructions)

if __name__ == "__main__":
    run_simulation_and_create_transfer_package()
