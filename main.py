import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import config
from pipeline import ContentPipeline
from generative_architect_pipeline import GenerativeArchitectEngine

class CloudHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = "<h2>🏛️ MK ARCHVIZ Telegram Bot is Live &amp; Running 24/7!</h2><p>Send messages or commands to @archimouradbot</p>"
        self.wfile.write(html.encode("utf-8"))
        
    def log_message(self, format, *args):
        pass # Keep console clean

def run_health_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), CloudHealthHandler)
        print(f"🌐 خادم الفحص السحابي نشط على المنفذ: {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server notice: {e}")

def print_banner():
    print("""
=============================================================
🏛️  مساعد صناعة المحتوى المعماري الذكي (MK ARCHVIZ AI Studio)
    توليد منشورات الأكواد واللوحات المعمارية من الصفر 100%
=============================================================
    """)

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    
    parser = argparse.ArgumentParser(description="Architectural Content Automation Tool")
    parser.add_argument("--generate", action="store_true", help="توليد منشور معماري متكامل من الصفر (واجهة + لوحة مفاهيم + كود)")
    parser.add_argument("--url", type=str, help="رابط منشور أو ريلز إنستغرام لتحليله")
    parser.add_argument("--text", type=str, help="نص فكرة أو نصيحة معمارية مباشرة")
    parser.add_argument("--bot", action="store_true", help="تشغيل وضع الاستماع عبر تيليغرام (من هاتفك مباشرة)")
    
    args = parser.parse_args()
    print_banner()

    gen_engine = GenerativeArchitectEngine()
    pipeline = ContentPipeline()

    if args.generate:
        gen_engine.run_full_cycle()
        return

    if args.url:
        pipeline.process_url(args.url)
        return

    if args.text:
        pipeline.process_content(args.text)
        return

    if args.bot:
        if not pipeline.telegram:
            print("❌ إعدادات تيليغرام غير مكتملة في .env.")
            sys.exit(1)
            
        print("🌐 تم تفعيل خادم التحقق السحابي (Health Server) لدعم الاستضافة 24/7.")

        def handle_telegram_url(text: str, msg_id: int):
            if "/generate" in text or "توليد" in text or "تصميم" in text:
                pipeline.telegram.send_message("⏳ جاري توليد تصميم معماري جديد من الصفر (واجهة + لوحة مفاهيم + كود البرومبت)...", reply_to_message_id=msg_id)
                gen_engine.run_full_cycle()
            elif "http://" in text or "https://" in text:
                pipeline.telegram.send_message("⏳ جاري تحليل المنشور واستخراج النصائح وتصميم الكاروسيل المعماري...", reply_to_message_id=msg_id)
                pipeline.process_url(text)
            else:
                pipeline.telegram.send_message(f"⏳ فكرة ممتازة! جاري كتابة وتصميم كاروسيل معماري احترافي حول:\n«{text}»...", reply_to_message_id=msg_id)
                pipeline.process_content(text_content=text)
                
        pipeline.telegram.run_polling_listener(handle_telegram_url)
        return

    # Interactive Menu
    print("اختر نمط العمل:")
    print("1) 🎨 توليد منشور معماري متكامل من الصفر (واجهة + لوحة مفاهيم + كود البرومبت) [جديد ⭐]")
    print("2) 📥 إدخال رابط منشور إنستغرام لإعادة إنتاجه بهويتك")
    print("3) 🤖 تشغيل وضع البوت (أرسل /generate أو أي رابط من هاتفك في تيليغرام)")
    print("0) خروج")
    
    choice = input("\nأدخل رقم الخيار [0-3]: ").strip()
    if choice == "1":
        gen_engine.run_full_cycle()
    elif choice == "2":
        url = input("ضع رابط إنستغرام هنا: ").strip()
        if url:
            pipeline.process_url(url)
    elif choice == "3":
        def handle_telegram_url(text: str, msg_id: int):
            if "/generate" in text or "توليد" in text:
                pipeline.telegram.send_message("⏳ جاري توليد تصميم معماري جديد من الصفر...", reply_to_message_id=msg_id)
                gen_engine.run_full_cycle()
            else:
                pipeline.process_url(text)
        pipeline.telegram.run_polling_listener(handle_telegram_url)
    else:
        print("مع السلامة!")

if __name__ == "__main__":
    main()
