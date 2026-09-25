import os
import time
import json
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
        
        self.state_file = os.path.join("output", "last_post_state.json")
        self.last_post_data = None
        self.last_bg_image_path = None
        self._load_last_post_state()

    def _load_last_post_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.last_post_data = data.get("post_data")
                    self.last_bg_image_path = data.get("bg_image_path")
            except Exception:
                pass

    def _save_last_post_state(self, post_data: dict, bg_image_path: Optional[str]):
        self.last_post_data = post_data
        self.last_bg_image_path = bg_image_path
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({"post_data": post_data, "bg_image_path": bg_image_path}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ تعذر حفظ حالة المنشور: {e}")

    def has_last_post(self) -> bool:
        if not self.last_post_data:
            self._load_last_post_state()
        return self.last_post_data is not None

    def modify_last_post(self, edit_instruction: str) -> bool:
        """Applies precision modifications to the last post and re-renders."""
        if not self.has_last_post():
            if self.telegram:
                self.telegram.send_message("⚠️ لا يوجد منشور سابق محفوظ لتعديله.")
            return False

        print(f"\n[تعديل دقيق] ✏️ جاري تنفيذ التعديل: {edit_instruction}")
        res = self.repurposer.modify_post(self.last_post_data, edit_instruction)
        if not res.get("success"):
            err = res.get("error", "فشل التعديل")
            print(f"[خطأ في التعديل]: {err}")
            if self.telegram:
                self.telegram.send_message(f"❌ تعذر تطبيق التعديل: {err}")
            return False

        updated_data = res["data"]
        
        # Check if background prompt changed or user asked to change background
        bg_image_path = self.last_bg_image_path
        old_bg_prompt = self.last_post_data.get("background_image_prompt", "")
        new_bg_prompt = updated_data.get("background_image_prompt", "")
        
        bg_keywords = ["خلفية", "خلفيه", "غير الخلفية", "بدل الخلفية", "background", "بدل الصورة", "غير الصورة"]
        asked_bg_change = any(k in edit_instruction.lower() for k in bg_keywords)
        
        if asked_bg_change and new_bg_prompt:
            print("  🏛️ توليد خلفية معمارية جديدة بناءً على طلب التعديل...")
            from generative_architect_pipeline import GenerativeArchitectEngine
            try:
                gen_engine = GenerativeArchitectEngine()
                bg_image_path = gen_engine.generate_image(new_bg_prompt, width=1080, height=1350)
            except Exception as e:
                print(f"  ⚠️ تعذر توليد الخلفية الجديدة: {e}")
        
        print("  🎨 إعادة تصميم وتصدير الشرائح المعدلة...")
        image_paths = self.render_slides(updated_data, bg_image_path=bg_image_path)
        caption = updated_data.get("instagram_caption", "")
        
        if self.telegram:
            msg = f"✅ تم تطبيق التعديل بدقة جراحية على المنشور!\n📌 الطلب: «{edit_instruction}»"
            self.telegram.send_message(msg)
            self.telegram.send_carousel(image_paths, caption)
            return True
        return True

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
        
        theme = post_data.get("theme", "atelier_prestige")
        bg_prompt = post_data.get("background_image_prompt", "").strip()
        
        # Default warm atelier canvas path
        default_atelier_bg = os.path.join(os.path.dirname(__file__), "assets", "backgrounds", "warm_atelier_01.jpg")
        
        if theme == "atelier_prestige" and not bg_prompt:
            bg_prompt = "overhead flatlay aesthetic architectural desk, warm cream textured linen paper parchment, subtle blueprint sketch of classical building, small balsa wood architectural study model, vintage brass fountain pen, triangular architect scale ruler, delicate olive branch casting soft sunlight shadows, warm ivory beige tones, architectural digest luxury editorial, 8k photorealistic, pure architecture, no human faces"
        elif not bg_prompt or len(bg_prompt) < 15:
            import random
            title = post_data.get("cover", {}).get("title", "")
            styles = [
                "overhead flatlay aesthetic architectural desk, warm cream linen paper, blueprints, scale ruler, olive branches, 8k",
                "contemporary architectural university studio, sleek drafting tables, physical models, high ceilings, natural skylight, architectural digest",
                "minimalist Mediterranean cliff villa with warm stone masonry, olive trees, minimalist infinity pool, golden hour sun",
                "brutalist concrete cultural pavilion, geometric water features, warm recessed LED lighting, twilight sky, architectural photography"
            ]
            bg_prompt = f"cinematic architectural photography of {title}, {random.choice(styles)}, photorealistic 8k, pure architecture, no human faces"

        if "no faces" not in bg_prompt.lower() and "no human faces" not in bg_prompt.lower():
            bg_prompt += ", pure architecture, no human faces, no portraits, architectural space and materials, cinematic lighting, 8k"

        print(f"\n[3/5] 🏛️ تجهيز الخلفية المعمارية الفاخرة للنمط ({theme})...")
        bg_image_path = None
        from generative_architect_pipeline import GenerativeArchitectEngine
        try:
            gen_engine = GenerativeArchitectEngine()
            bg_image_path = gen_engine.generate_image(bg_prompt, width=1080, height=1350)
            print(f"  ✅ تم توليد خلفية معمارية مخصصة بنجاح: {bg_image_path}")
        except Exception as e:
            print(f"  ⚠️ تعذر توليد صورة الخلفية: {e}")
            if os.path.exists(default_atelier_bg):
                bg_image_path = default_atelier_bg
                print(f"  🔄 استخدام خلفية الأتيلييه المعتمدة: {bg_image_path}")
        
        print("\n[4/5] 🎨 جاري تصميم شرائح الكاروسيل المعمارية بالهيكل التفاعلي الإبداعي...")
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
        # Persist post state for precision editing
        self._save_last_post_state(post_data, bg_image_path)
        
        timestamp = int(time.time())
        out_dir = os.path.join("output", f"post_{timestamp}")
        os.makedirs(out_dir, exist_ok=True)
        
        category = post_data.get("category", "دليل طالب العمارة")
        cover_data = post_data.get("cover", {})
        content_slides_data = post_data.get("content_slides", [])
        cta_data = post_data.get("cta_slide", {})
        theme = post_data.get("theme", "atelier_prestige")
        
        total_slides = 1 + len(content_slides_data) + (1 if cta_data else 0)
        image_paths = []
        current_slide = 1
        
        # 1. Cover Slide
        if theme == "atelier_prestige":
            cover_img = self.designer.create_atelier_cover(
                super_title=cover_data.get("super_title", "GUIDE DE L'ÉTUDIANT EN"),
                hero_title=cover_data.get("hero_title", "ARCHITECTURE"),
                hook_tag=cover_data.get("hook_tag", "طالب Architecture"),
                main_title=cover_data.get("title", cover_data.get("main_title", "دليل طالب ومعماري الجزائر")),
                subtitle=cover_data.get("subtitle", "كل ما يحتاجه طالب العمارة في مكان واحد"),
                footer_tags=cover_data.get("footer_tags", "Plans • Coupes • Façades • Échelles • Logiciels • Conseils"),
                bg_image_path=bg_image_path
            )
        else:
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
            layout_type = c_slide.get("layout_type", "standard_bullets")
            headline = c_slide.get("headline", "تفاصيل هندسية")
            
            if theme == "atelier_prestige":
                if layout_type == "definition_table" and c_slide.get("table_items"):
                    c_img = self.designer.create_atelier_definition_table(
                        slide_num=current_slide,
                        total_slides=total_slides,
                        headline=headline,
                        items=c_slide.get("table_items", []),
                        bg_image_path=bg_image_path
                    )
                elif layout_type == "hero_spotlight":
                    c_img = self.designer.create_atelier_hero_spotlight(
                        slide_num=current_slide,
                        total_slides=total_slides,
                        headline=headline,
                        hero_title=c_slide.get("hero_title", "ATELIER DE PROJET"),
                        coef_text=c_slide.get("coef_text", "— COEF. 4 —"),
                        stats=c_slide.get("stats", []),
                        takeaway=c_slide.get("takeaway"),
                        bg_image_path=bg_image_path
                    )
                elif layout_type == "cards_grid" and c_slide.get("cards"):
                    c_img = self.designer.create_atelier_cards_grid(
                        slide_num=current_slide,
                        total_slides=total_slides,
                        headline=headline,
                        cards=c_slide.get("cards", []),
                        bottom_quote=c_slide.get("bottom_quote"),
                        bg_image_path=bg_image_path
                    )
                else:
                    bullets = c_slide.get("bullets", [])
                    takeaway = c_slide.get("takeaway", c_slide.get("tip"))
                    c_img = self.designer.create_atelier_content_slide(
                        slide_num=current_slide,
                        total_slides=total_slides,
                        headline=headline,
                        bullets=bullets,
                        takeaway=takeaway,
                        bg_image_path=bg_image_path
                    )
            else:
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
            if theme == "atelier_prestige":
                main_q = cta_data.get("main_question", "درك فهمت البرنامج تاعك أكثر؟")
                badge = cta_data.get("cta_badge", "Sauvegarde le post 📌")
                quote = cta_data.get("cta_quote", cta_data.get("cta_text", "وابعثو لصحابك في الأتيلييه لي راهم ضايعين مع البرنامج!"))
                cta_img = self.designer.create_atelier_cta_slide(
                    slide_num=current_slide,
                    total_slides=total_slides,
                    main_question=main_q,
                    cta_badge=badge,
                    cta_quote=quote,
                    bg_image_path=bg_image_path
                )
            else:
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
