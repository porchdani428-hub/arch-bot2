import os
import time
from typing import List, Dict, Any, Optional

import config
from content_extractor import ContentExtractor
from ai_repurposer import ArchitecturalRepurposer
from slide_designer import ArchitecturalSlideDesigner
from telegram_service import TelegramService

class ContentPipeline:
    def __init__(self):
        self.extractor = ContentExtractor(download_dir="downloads")
        self.repurposer = ArchitecturalRepurposer(api_key=config.GEMINI_API_KEY) if config.GEMINI_API_KEY else None
        self.designer = ArchitecturalSlideDesigner(
            brand_name=config.ARCHITECT_NAME,
            brand_handle=config.ARCHITECT_HANDLE
        )
        self.telegram = TelegramService(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID
        ) if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID else None

    def process_url(self, url: str) -> bool:
        """Runs the entire pipeline from URL to Telegram."""
        print(f"\n[1/5] 📥 جاري سحب محتوى المنشور والشرائح من: {url}")
        extract_res = self.extractor.extract_from_url(url)
        
        caption = extract_res.get("caption", "")
        media_path = extract_res.get("primary_image")
        image_paths = extract_res.get("image_paths", [])
        if media_path and media_path not in image_paths:
            image_paths.insert(0, media_path)
        
        if not caption and not image_paths:
            print("[خطأ] تعذر استخراج المحتوى من الرابط. قد يكون المنشور خاصاً أو يتطلب تسجيل الدخول.")
            if self.telegram:
                self.telegram.send_message("❌ تعذر استخراج المحتوى من هذا الرابط. تأكد أن المنشور من حساب عام وليس خاصاً.")
            return False

        return self.process_content(text_content=caption, input_images=image_paths)

    def process_content(self, text_content: str, input_images: Optional[List[str]] = None, media_path: Optional[str] = None) -> bool:
        """Processes content (text + optional media) and sends to Telegram."""
        if not self.repurposer:
            print("[خطأ] يرجى تعيين GEMINI_API_KEY أو XKIRO_API_KEY في ملف .env أولاً.")
            return False

        imgs = input_images or ([media_path] if media_path else None)
        print("\n[2/5] 🧠 جاري تحليل المحتوى وقراءة الشرائح بالذكاء الاصطناعي...")
        repurpose_res = self.repurposer.repurpose(text_content, image_paths=imgs)
        
        if not repurpose_res.get("success"):
            print(f"[خطأ في التحليل]: {repurpose_res.get('error')}")
            if self.telegram:
                self.telegram.send_message(f"❌ حدث خطأ أثناء تحليل المنشور: {repurpose_res.get('error')}")
            return False

        post_data = repurpose_res["data"]
        
        # Dynamically generate a creative background prompt matching the specific topic
        bg_prompt = post_data.get("background_image_prompt", "").strip()
        if not bg_prompt or len(bg_prompt) < 15:
            import random
            category = post_data.get("category", "Architecture")
            title = post_data.get("cover", {}).get("title", "")
            styles = [
                "ultra modern luxury villa facade, concrete cantilevers, timber slats, floor-to-ceiling glass, dusk twilight sunset, reflection pool",
                "contemporary architectural university studio, sleek drafting tables, physical models, high ceilings, natural skylight, architectural digest",
                "minimalist Mediterranean cliff villa with warm stone masonry, olive trees, minimalist infinity pool, golden hour sun",
                "brutalist concrete cultural pavilion, geometric water features, warm recessed LED lighting, twilight sky, architectural photography",
                "high-end contemporary architectural firm office, glass partitions, large scale physical models, moody warm lighting, 8k",
                "Japanese modern minimalist house, gravel courtyard, bonsai, black cedar wood and smooth concrete, diffused morning light",
                "futuristic parametric architectural pavilion, organic curves, glass facade, dusk reflections, 8k architectural digest"
            ]
            chosen_style = random.choice(styles)
            bg_prompt = f"cinematic architectural photography of {title}, {chosen_style}, shot on 35mm Hasselblad lens, photorealistic 8k, architectural digest"

        if "no faces" not in bg_prompt.lower() and "no human faces" not in bg_prompt.lower():
            bg_prompt += ", pure architecture, no human faces, no portraits, architectural space and materials, cinematic lighting, 8k"

        print(f"\n[3/5] 🏛️ جاري توليد خلفية معمارية إبداعية مخصصة للموضوع:\n  \"{bg_prompt[:120]}...\"")
        from generative_architect_pipeline import GenerativeArchitectEngine
        try:
            gen_engine = GenerativeArchitectEngine()
            bg_image_path = gen_engine.generate_image(bg_prompt, width=1080, height=1350)
            print(f"  ✅ تم توليد خلفية معمارية فريدة بنجاح: {bg_image_path}")
        except Exception as e:
            print(f"  ⚠️ تعذر توليد صورة الخلفية: {e}")
            bg_image_path = None
        
        print("\n[4/5] 🎨 جاري تصميم شرائح الكاروسيل المعمارية بخلفيات الفيلات الفاخرة...")
        image_paths = self.render_slides(post_data, bg_image_path=bg_image_path)
        
        caption = post_data.get("instagram_caption", "")
        
        print(f"\n[5/5] 🚀 جاري إرسال {len(image_paths)} شرائح مع الكابشن إلى تيليغرام...")
        if self.telegram:
            success = self.telegram.send_carousel(image_paths, caption)
            if success:
                print("✅ تم تسليم المنشور بالكامل إلى حسابك في تيليغرام بنجاح!")
                return True
            else:
                print("❌ فشل إرسال الصور إلى تيليغرام. راجع التوكن والمعرف في ملف .env")
                return False
        else:
            print("⚠️ تم حفظ الصور محلياً في مجلد output/ ولكن لم يتم الإرسال لأن إعدادات تيليغرام غير مكتملة في .env.")
            print(f"الكابشن المقترح:\n{caption}")
            return True

    def render_slides(self, post_data: Dict[str, Any], bg_image_path: Optional[str] = None) -> List[str]:
        timestamp = int(time.time())
        out_dir = os.path.join("output", f"post_{timestamp}")
        os.makedirs(out_dir, exist_ok=True)
        
        category = post_data.get("category", "نصائح معمارية")
        cover_data = post_data.get("cover", {})
        content_slides_data = post_data.get("content_slides", [])
        cta_data = post_data.get("cta_slide", {})
        
        total_slides = 1 + len(content_slides_data) + (1 if cta_data else 0)
        image_paths = []
        current_slide = 1
        
        # 1. Cover Slide
        cover_img = self.designer.create_cover_slide(
            title=cover_data.get("title", "نصيحة معمارية هامة"),
            subtitle=cover_data.get("subtitle", "تفاصيل هندسية ترفع من جودة العمل"),
            category=category,
            total_slides=total_slides,
            bg_image_path=bg_image_path
        )
        cover_path = os.path.join(out_dir, f"slide_{current_slide:02d}.png")
        cover_img.save(cover_path)
        image_paths.append(cover_path)
        current_slide += 1
        
        # 2. Content Slides
        for c_slide in content_slides_data:
            headline = c_slide.get("headline", "تفاصيل هندسية")
            bullets = c_slide.get("bullets", [])
            tip = c_slide.get("tip")
            
            c_img = self.designer.create_content_slide(
                slide_num=current_slide,
                total_slides=total_slides,
                category=category,
                headline=headline,
                bullets=bullets,
                tip=tip,
                bg_image_path=bg_image_path
            )
            c_path = os.path.join(out_dir, f"slide_{current_slide:02d}.png")
            c_img.save(c_path)
            image_paths.append(c_path)
            current_slide += 1
            
        # 3. CTA Slide
        if cta_data:
            summary = cta_data.get("summary_points", [])
            cta_txt = cta_data.get("cta_text", "احفظ المنشور وشاركه مع زملائك")
            cta_img = self.designer.create_cta_slide(
                slide_num=current_slide,
                total_slides=total_slides,
                category=category,
                summary_points=summary,
                cta_text=cta_txt,
                bg_image_path=bg_image_path
            )
            cta_path = os.path.join(out_dir, f"slide_{current_slide:02d}.png")
            cta_img.save(cta_path)
            image_paths.append(cta_path)
            
        return image_paths
