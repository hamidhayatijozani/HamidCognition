# HamidCognition Engine

> **Repository status:** Foundational historical P/S/T and EUR/USD implementation lineage.
>
> The current canonical research and provenance record is **[HamidCognition-Unified](https://github.com/hamidhayatijozani/HamidCognition-Unified)**. This repository remains citable as the source artifact for the implementation and transfer package preserved here.
>
> For current epistemic status, repository roles and citation rules, see `RESEARCH/REPOSITORY_GOVERNANCE.md` in the Unified repository.

## جایگاه پژوهشی

این repository شامل موتور شناختی **HamidCognition** است که توسط حمید حیاتی جوزانی طراحی شده است. محتویات آن باید به‌عنوان artifact تاریخی/اجرایی همین نسخه خوانده شود؛ وجود implementation به‌تنهایی اعتبار تجربی یا production readiness را اثبات نمی‌کند.

برای استناد دقیق به رفتار یا خروجی یک فایل، repository و commit/path همان artifact را مشخص کنید.

## فایل‌ها

* `hamid_cognition_engine.py`: کد کلاس `HamidCognition` و منطق شبیه‌سازی.
* `hamid_cognition_transfer.json`: بسته انتقال وضعیت و منطق ثبت‌شده.
* `simple_eurusd.py`: نسخه ساده‌شده موتور تحلیل EUR/USD برای تست سریع.
* `eurusd_state.json`: فایل وضعیت خروجی ثبت‌شده.
* `eurusd_engine.py`: موتور `HamidForexEngine` با منطق P-S-T و شبیه‌ساز معاملات.
* `run_eurusd.py`: اسکریپت اجرای موتور و تولید گزارش.

## موتور عملیاتی EUR/USD (شبیه‌سازی)

این بخش یک محیط معاملاتی شبیه‌سازی‌شده (Mock MT5) را ثبت می‌کند. خروجی‌های آن را نباید به‌عنوان نتیجهٔ live trading یا سودآوری اثبات‌شده تفسیر کرد.

## روش انتقال و تست

برای تست مدل ثبت‌شده در این repository، فایل `hamid_cognition_transfer.json` را همراه با commit دقیق همین repository ارجاع دهید. نتیجهٔ بازتولید باید با evidence و نسخهٔ دقیق کد ثبت شود.

## Canonical research record

**HamidCognition-Unified:** https://github.com/hamidhayatijozani/HamidCognition-Unified

**Originator:** Hamid Hayati Jozani
