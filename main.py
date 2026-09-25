import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import config
import re
from trends_tracker import ArchitecturalTrendsTracker
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

def start_telegram_bot(pipeline: ContentPipeline, gen_engine: GenerativeArchitectEngine):
    if not pipeline.telegram:
        print("❌ إعدادات تيليغرام غير مكتملة في .env.")
        sys.exit(1)
        
    print("🌐 تم تفعيل خادم التحقق السحابي (Health Server) لدعم الاستضافة 24/7.")
    trends_tracker = ArchitecturalTrendsTracker()
    cached_trends = []

    def handle_telegram_url(text: str, msg_id: int):
        nonlocal cached_trends
        clean_text = text.strip()
        lower_text = clean_text.lower()
        
        # 1. Trends & News command
        if any(k in lower_text for k in ["/trends", "تريند", "ترند", "/news", "أخبار", "اخبار"]):
            pipeline.telegram.send_message("🔍 جاري جلب أحدث تريندات وأخبار العمارة الموثوقة (ArchDaily و CNOA)...", reply_to_message_id=msg_id)
            cached_trends = trends_tracker.get_curated_topics(total=6)
            msg = trends_tracker.format_trends_message(cached_trends)
            pipeline.telegram.send_message(msg, reply_to_message_id=msg_id)
            return

        # 2. Number selection for trends (e.g. "1", "2", "توليد 1", "رقم 1", "/1")
        match = re.match(r"^(?:توليد|رقم|خيار|option)?\s*#?/?([1-9])\s*$", clean_text, re.IGNORECASE)
        if match:
            idx = int(match.group(1)) - 1
            if not cached_trends:
                cached_trends = trends_tracker.get_curated_topics(total=6)
            if 0 <= idx < len(cached_trends):
                selected = cached_trends[idx]
                title = selected.get("title", "")
                cat = selected.get("category", "عمارة")
                pipeline.telegram.send_message(
                    f"⏳ اختيار ممتاز! جاري إعداد وتصميم كاروسيل معماري احترافي كامل حول:\n📌 «{title}»\n🏷️ التصنيف: {cat}\n\nيتم الآن: صياغة المحتوى 🧠 ➔ توليد خلفية معمارية مخصصة 🏛️ ➔ تصميم الشرائح 🎨...",
                    reply_to_message_id=msg_id
                )
                topic_content = (
                    f"الموضوع المعماري: {title}\n"
                    f"التصنيف: {cat}\n"
                    f"المصدر: {selected.get('source', '')}\n"
                    f"الخلاصة: {selected.get('summary', '')}\n"
                )
                if selected.get("prompt_hint"):
                    topic_content += f"توجيه للخلفية المعمارية: {selected['prompt_hint']}\n"
                
                pipeline.process_content(text_content=topic_content)
                return

        # 3. Generate from scratch
        if any(k in lower_text for k in ["/generate", "توليد", "تصميم"]):
            pipeline.telegram.send_message("⏳ جاري توليد تصميم معماري جديد من الصفر (واجهة + لوحة مفاهيم + كود البرومبت)...", reply_to_message_id=msg_id)
            gen_engine.run_full_cycle()
            return

        # 4. Instagram URL
        if "http://" in clean_text or "https://" in clean_text:
            pipeline.telegram.send_message("⏳ جاري تحليل المنشور واستخراج النصائح وتصميم الكاروسيل المعماري...", reply_to_message_id=msg_id)
            pipeline.process_url(clean_text)
            return

        # 5. Precision Edit Request for the previous post
        edit_pattern = re.compile(
            r'^(?:/edit|edit)\b'
            r'|^(?:تعديل|تغيير)\s*[:：]'
            r'|^(?:غير|عدل|بدل|صلح|امسح|احذف|زيد|نحي|عاود|صحح)\b'
            r'|(?:أريد|اريد|ممكن|حاب|لازم)\s+(?:تغير|تعدل|تبدل|تصلح|تغيير|تعديل)'
            r'|(?:في الشريحة|في شريحة|شريحة \d|السليد|slide \d|الغلاف|الكابشن|بدل كلمة|اكتب بدلها|غير النص|عدل النص|غير الخلفية|بدل الخلفية)',
            re.IGNORECASE
        )
        if edit_pattern.search(clean_text):
            if pipeline.has_last_post():
                pipeline.telegram.send_message(
                    f"✏️ تم استلام طلب التعديل! جاري تدقيق المنشور وتحديثه بدقة متناهية:\n«{clean_text}»...",
                    reply_to_message_id=msg_id
                )
                pipeline.modify_last_post(clean_text)
                return
            else:
                pipeline.telegram.send_message(
                    "⚠️ لا يوجد منشور سابق محفوظ لتعديله حالياً. أرسل رابطاً أو فكرة لإنشاء منشور أولاً، ثم اطلب تعديل أي جزء فيه!",
                    reply_to_message_id=msg_id
                )
                return

        # 6. Free-form text idea
        pipeline.telegram.send_message(f"⏳ فكرة ممتازة! جاري كتابة وتصميم كاروسيل معماري احترافي حول:\n«{clean_text}»...", reply_to_message_id=msg_id)
        pipeline.process_content(text_content=clean_text)
            
    pipeline.telegram.run_polling_listener(handle_telegram_url)

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    
    parser = argparse.ArgumentParser(description="Architectural Content Automation Tool")
    parser.add_argument("--generate", action="store_true", help="توليد منشور معماري متكامل من الصفر (واجهة + لوحة مفاهيم + كود)")
    parser.add_argument("--trends", action="store_true", help="جلب أحدث تريندات وأخبار العمارة وتوليد كاروسيل منها")
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

    if args.trends:
        tracker = ArchitecturalTrendsTracker()
        topics = tracker.get_curated_topics(6)
        print(tracker.format_trends_message(topics))
        sel = input("\nأدخل رقم الموضوع للتوليد (أو اضغط Enter للإلغاء): ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(topics):
            t = topics[int(sel) - 1]
            topic_content = f"الموضوع المعماري: {t['title']}\nالتصنيف: {t.get('category','')}\nالمصدر: {t.get('source','')}\nالخلاصة: {t.get('summary','')}\n"
            pipeline.process_content(text_content=topic_content)
        return

    if args.url:
        pipeline.process_url(args.url)
        return

    if args.text:
        pipeline.process_content(args.text)
        return

    if args.bot:
        start_telegram_bot(pipeline, gen_engine)
        return

    # Interactive Menu
    print("اختر نمط العمل:")
    print("1) 🎨 توليد منشور معماري متكامل من الصفر (واجهة + لوحة مفاهيم + كود البرومبت) [جديد ⭐]")
    print("2) 📥 إدخال رابط منشور إنستغرام لإعادة إنتاجه بهويتك")
    print("3) 🔥 استعراض تريندات وأخبار العمارة وتوليد كاروسيل منها [جديد ⭐]")
    print("4) 🤖 تشغيل وضع البوت (أرسل /trends أو /generate أو أي رابط من هاتفك في تيليغرام)")
    print("0) خروج")
    
    choice = input("\nأدخل رقم الخيار [0-4]: ").strip()
    if choice == "1":
        gen_engine.run_full_cycle()
    elif choice == "2":
        url = input("ضع رابط إنستغرام هنا: ").strip()
        if url:
            pipeline.process_url(url)
    elif choice == "3":
        tracker = ArchitecturalTrendsTracker()
        topics = tracker.get_curated_topics(6)
        print(tracker.format_trends_message(topics))
        sel = input("\nأدخل رقم الموضوع للتوليد (أو اضغط Enter للإلغاء): ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(topics):
            t = topics[int(sel) - 1]
            topic_content = f"الموضوع المعماري: {t['title']}\nالتصنيف: {t.get('category','')}\nالمصدر: {t.get('source','')}\nالخلاصة: {t.get('summary','')}\n"
            pipeline.process_content(text_content=topic_content)
    elif choice == "4":
        start_telegram_bot(pipeline, gen_engine)
    else:
        print("مع السلامة!")

if __name__ == "__main__":
    main()
