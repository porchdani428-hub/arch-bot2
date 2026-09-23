import os
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import json
import time
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

import config
from google import genai
from telegram_service import TelegramService

def find_arabic_font(bold: bool = False):
    font_name = 'arialbd.ttf' if bold else 'arial.ttf'
    candidates = [
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', font_name),
        f'/app/assets/fonts/{font_name}',
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        font_name
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return font_name

FONT_BOLD = find_arabic_font(True)
FONT_REGULAR = find_arabic_font(False)

def prep(text):
    if not text:
        return ""
    cleaned = text.replace("✔", "").replace("💡", "").replace("📌", "").replace("⬅", "").replace("➡", "")
    return get_display(arabic_reshaper.reshape(cleaned.strip()))

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = " ".join(current_line)
        reshaped_test = prep(test_line)
        bbox = draw.textbbox((0, 0), reshaped_test, font=font)
        line_w = bbox[2] - bbox[0]
        
        if line_w > max_width and len(current_line) > 1:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

class GenerativeArchitectEngine:
    def __init__(self):
        self.gemini = genai.Client(api_key=config.GEMINI_API_KEY)
        self.telegram = TelegramService(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
        os.makedirs("generative_output", exist_ok=True)
        
    def generate_image(self, prompt: str, width: int = 600, height: int = 750) -> str:
        """
        Generates an architectural image:
        - Uses GPT Image 2.5 Flare (OpenAI / Proxy) if IMAGE_API_KEY is provided in .env
        - Automatically falls back to Pollinations AI (100% free forever)
        """
        # 1. Try GPT Image 2.5 Flare if API key is provided
        if config.IMAGE_API_KEY:
            try:
                print(f"  ⚡ استخدام محرك GPT Image 2.5 Flare ({config.IMAGE_MODEL})...")
                from openai import OpenAI
                kwargs = {"api_key": config.IMAGE_API_KEY}
                if config.IMAGE_BASE_URL:
                    kwargs["base_url"] = config.IMAGE_BASE_URL
                ai_client = OpenAI(**kwargs)
                
                resp = ai_client.images.generate(
                    model=config.IMAGE_MODEL,
                    prompt=prompt,
                    size="1024x1024",
                    n=1
                )
                item = resp.data[0]
                img_bytes = None
                if getattr(item, "b64_json", None):
                    import base64
                    img_bytes = base64.b64decode(item.b64_json)
                elif getattr(item, "url", None):
                    img_res = requests.get(item.url, timeout=30)
                    if img_res.status_code == 200:
                        img_bytes = img_res.content
                
                if img_bytes:
                    filename = f"generative_output/gpt_flare_{int(time.time()*1000)}.jpg"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    print(f"  ✅ تم التوليد بنجاح عبر GPT Image 2.5 Flare!")
                    return filename
            except Exception as e:
                print(f"  ⚠️ تنبيه محرك GPT Image: {e}")
                print("  🔄 الانتقال التلقائي للمحرك المجاني الدائم (Pollinations)...")

        # 2. Fallback to free engine (Pollinations)
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={int(time.time())}"
        
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and len(r.content) > 1000:
                    filename = f"generative_output/img_{int(time.time()*1000)}.jpg"
                    with open(filename, "wb") as f:
                        f.write(r.content)
                    return filename
            except Exception as e:
                time.sleep(3)
        raise RuntimeError("Failed to generate image from AI generator")

    def run_full_cycle(self, custom_input_path: str = None, prompt_type: str = "conceptdiagram"):
        print("\n" + "="*60)
        print("🏛️ بدء دورة التوليد الكاملة من الصفر (100% Generated from Scratch)")
        print("="*60)
        
        # 1. Input Image
        if custom_input_path and (custom_input_path.startswith("http://") or custom_input_path.startswith("https://")):
            print(f"[1/4] 📥 جاري سحب صورة المبنى من رابط إنستغرام: {custom_input_path}...")
            from content_extractor import ContentExtractor
            extractor = ContentExtractor()
            ext_res = extractor.extract_from_url(custom_input_path)
            input_image_path = ext_res.get("primary_image")
            if not input_image_path or not os.path.exists(input_image_path):
                print("  ⚠️ تعذر سحب صورة من الرابط، جاري توليد واجهة جديدة تلقائياً...")
                facade_prompt = "ultra modern luxury villa facade, concrete cantilevers, timber slats, floor to ceiling glass, warm dusk illumination, photorealistic 8k architectural digest"
                input_image_path = self.generate_image(facade_prompt, width=600, height=750)
            else:
                print(f"  ✅ تم سحب الصورة بنجاح: {input_image_path}")
        elif custom_input_path and os.path.exists(custom_input_path):
            input_image_path = custom_input_path
        else:
            print("[1/4] 🎨 توليد صورة واجهة معمارية حديثة من الصفر (Input Facade)...")
            facade_prompt = "ultra modern luxury villa facade, concrete cantilevers, timber slats, floor to ceiling glass, warm dusk illumination, photorealistic 8k architectural digest"
            input_image_path = self.generate_image(facade_prompt, width=600, height=750)

        # 2. Gemini Vision
        print("[2/4] 🧠 تحليل المبنى بـ Gemini Vision واستخراج الأكواد والمفاهيم...")
        img_obj = Image.open(input_image_path)
        
        analysis_prompt = f"""
أنت مهندس معماري استشاري وخبير في أدوات الذكاء الاصطناعي (Midjourney & ChatGPT).
انظر إلى صورة هذا المبنى المعماري بدقة واستخرج ما يلي:
1. الطراز المعماري والمواد الأساسية والألوان.
2. اكتب برومبت باللغة الإنجليزية لتوليد "لوحة المفهوم المعمارية" (Concept Presentation Board أو Exploded Axonometric Diagram) تتطابق تماماً مع نفس هذا المبنى ومواده، على خلفية بيضاء نظيفة بأسلوب مجلات العمارة العالمية.
3. حدد كود الأمر مثل ({prompt_type}) مع شرحه.

المطلوب: أخرج فقط كائن JSON صالح وبدون أي مقدمات، بالهيكل التالي:
{{
  "concept_title_ar": "عنوان اللوحة باللغة العربية (مثال: التحليل المفاهيمي للكتل والواجهة)",
  "code_command": "/{prompt_type} --v 6.0 --ar 3:4",
  "board_generation_prompt": "detailed english prompt to generate the architectural presentation board of this exact building, exploded axonometric or concept diagrams, material palette callouts, clean light background, editorial architectural graphic",
  "function_ar": "شرح وظيفة الكود وماذا يفعل في سطر واحد موجز باللغة العربية",
  "usage_tip_ar": "طريقة استخدام الكود في برامج الذكاء الاصطناعي بنصيحة مهنية عملية",
  "portfolio_tip_ar": "نصيحة أين يُستخدم هذا المخطط (مثل: لوحات المنافسات المعمارية أو بورتفوليو التخرج)",
  "instagram_caption": "كابشن إنستغرام كامل مع هوك قوي ونقاط مرتبة وهاشتاغات معمارية عربية وهندسية"
}}
"""
        models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        response = None
        for m in models:
            try:
                response = self.gemini.models.generate_content(
                    model=m,
                    contents=[img_obj, analysis_prompt]
                )
                break
            except Exception as e:
                print(f"  🔄 تنبيه نموذج {m}: {e}, تجربة البديل...")
                time.sleep(2)

        if not response:
            raw_text = None
            if config.XKIRO_API_KEY:
                print(f"  🔄 تفعيل محرك XKiro AI ({config.XKIRO_MODEL}) كبديل ذكي...")
                try:
                    from openai import OpenAI
                    ai_client = OpenAI(api_key=config.XKIRO_API_KEY, base_url=config.XKIRO_BASE_URL)
                    resp = ai_client.chat.completions.create(
                        model=config.XKIRO_MODEL,
                        messages=[
                            {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. أخرج كائن JSON صالح فقط بدون أي مقدمات."},
                            {"role": "user", "content": analysis_prompt}
                        ]
                    )
                    raw_text = resp.choices[0].message.content.strip()
                except Exception as e:
                    print(f"  ⚠️ تنبيه محرك XKiro: {e}")

            if not raw_text and config.IMAGE_API_KEY:
                print("  🔄 تفعيل المحرك البديل (GPT-4o-mini) عبر CometAPI...")
                try:
                    from openai import OpenAI
                    base_url = config.IMAGE_BASE_URL or "https://api.cometapi.com/v1"
                    if not base_url.endswith("/v1"):
                        base_url = f"{base_url.rstrip('/')}/v1"
                    ai_client = OpenAI(api_key=config.IMAGE_API_KEY, base_url=base_url)
                    resp = ai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. أخرج كائن JSON صالح فقط بدون أي مقدمات."},
                            {"role": "user", "content": analysis_prompt}
                        ]
                    )
                    raw_text = resp.choices[0].message.content.strip()
                except Exception as e:
                    print(f"  ⚠️ فشل المحرك البديل: {e}")
                    raise RuntimeError("تعذر تحليل الصورة عبر نماذج الذكاء الاصطناعي")

            if not raw_text:
                raise RuntimeError("تعذر تحليل الصورة عبر نماذج الذكاء الاصطناعي")
        else:
            raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        else:
            s = raw_text.find("{")
            e = raw_text.rfind("}")
            if s != -1 and e != -1:
                raw_text = raw_text[s:e+1]
                
        analysis_data = json.loads(raw_text)

        # 3. Output Board
        print("[3/4] 🎨 رسم لوحة المفهوم المعمارية (Output Board) بالذكاء الاصطناعي...")
        board_prompt = analysis_data["board_generation_prompt"]
        output_board_path = self.generate_image(board_prompt, width=600, height=750)

        # 4. Composite with Pillow
        print("[4/4] 🖼️ تركيب الشريحة النهائية بهوية MK ARCHVIZ...")
        final_slide_path = self.composite_slide(input_image_path, output_board_path, analysis_data)

        # 5. Telegram Send
        print("🚀 إرسال الشريحة والكابشن إلى تيليغرام...")
        caption = analysis_data.get("instagram_caption", "")
        self.telegram.send_carousel([final_slide_path], caption)
        print("🎉 تم تسليم المنشور بالكامل إلى حسابك على تيليغرام بنجاح!")
        return final_slide_path

    def composite_slide(self, input_path: str, output_path: str, data: dict) -> str:
        W, H = 1080, 1350
        canvas = Image.new("RGB", (W, H), (18, 20, 24))
        draw = ImageDraw.Draw(canvas)

        font_badge = ImageFont.truetype(FONT_BOLD, 26)
        font_num = ImageFont.truetype(FONT_BOLD, 26)
        font_title = ImageFont.truetype(FONT_BOLD, 36)
        font_body = ImageFont.truetype(FONT_REGULAR, 23)
        font_tip = ImageFont.truetype(FONT_BOLD, 20)

        # Header
        draw.text((W - 100, 80), prep("• أكواد معمارية ذكية •"), font=font_badge, fill=(212, 163, 115), anchor="rt")
        draw.text((100, 80), "01 / 01", font=font_num, fill=(160, 165, 175), anchor="lt")
        draw.line([(100, 130), (W - 100, 130)], fill=(45, 50, 60), width=2)

        # Title
        title_ar = prep(data.get("concept_title_ar", "التحليل المفاهيمي للكتل والواجهة"))
        draw.text((W - 100, 165), title_ar, font=font_title, fill=(245, 245, 247), anchor="rt")

        # Load & Resize Images
        in_img = Image.open(input_path).convert("RGB")
        out_img = Image.open(output_path).convert("RGB")

        # Left: Input Image Card
        in_x, in_y = 90, 240
        in_w, in_h = 390, 520
        in_resized = in_img.resize((in_w, in_h), Image.Resampling.LANCZOS)
        draw.rounded_rectangle([(in_x - 8, in_y - 8), (in_x + in_w + 8, in_y + in_h + 8)], radius=16, fill=(28, 31, 38), outline=(60, 65, 75), width=2)
        canvas.paste(in_resized, (in_x, in_y))

        draw.rounded_rectangle([(in_x + 15, in_y + 15), (in_x + 170, in_y + 55)], radius=8, fill=(0, 0, 0, 220))
        draw.text((in_x + 92, in_y + 35), prep("الواجهة الأصلية"), font=ImageFont.truetype(FONT_BOLD, 18), fill=(255, 255, 255), anchor="mm")

        # Right: Output Board Card
        out_x, out_y = 530, 240
        out_w, out_h = 460, 550
        out_resized = out_img.resize((out_w, out_h), Image.Resampling.LANCZOS)
        draw.rounded_rectangle([(out_x - 8, out_y - 8), (out_x + out_w + 8, out_y + out_h + 8)], radius=16, fill=(28, 31, 38), outline=(212, 163, 115), width=2)
        canvas.paste(out_resized, (out_x, out_y))

        draw.rounded_rectangle([(out_x + 15, out_y + 15), (out_x + 220, out_y + 55)], radius=8, fill=(212, 163, 115))
        draw.text((out_x + 117, out_y + 35), prep("لوحة المفاهيم (AI)"), font=ImageFont.truetype(FONT_BOLD, 18), fill=(18, 20, 24), anchor="mm")

        # Bottom Card
        card_top = 835
        card_w = W - 160
        draw.rounded_rectangle([(80, card_top), (W - 80, H - 110)], radius=20, fill=(26, 29, 36), outline=(48, 52, 64), width=2)

        # Code Box
        draw.rounded_rectangle([(110, card_top + 25), (W - 110, card_top + 95)], radius=12, fill=(36, 41, 50), outline=(75, 82, 98), width=1)
        code_cmd = data.get("code_command", "/conceptdiagram --v 6.0")
        draw.text((135, card_top + 60), code_cmd, font=ImageFont.truetype(FONT_BOLD, 28), fill=(255, 255, 255), anchor="lm")
        draw.text((W - 135, card_top + 60), prep("كود البرومبت"), font=ImageFont.truetype(FONT_BOLD, 22), fill=(212, 163, 115), anchor="rm")

        # Wrapped Explanation
        exp_y = card_top + 115
        max_txt_w = card_w - 90
        
        # Function
        func_txt = f"الوظيفة: {data.get('function_ar', '')}"
        for line in wrap_text(func_txt, font_body, max_txt_w, draw):
            draw.text((W - 145, exp_y), prep(line), font=font_body, fill=(235, 235, 240), anchor="rt")
            exp_y += 36
            
        exp_y += 10
        # Usage
        usage_txt = f"طريقة الاستخدام: {data.get('usage_tip_ar', '')}"
        for line in wrap_text(usage_txt, font_body, max_txt_w, draw):
            draw.text((W - 145, exp_y), prep(line), font=font_body, fill=(210, 215, 225), anchor="rt")
            exp_y += 36

        # Tip Box at bottom
        tip_box_y = max(exp_y + 15, H - 220)
        draw.rounded_rectangle([(110, tip_box_y), (W - 110, tip_box_y + 70)], radius=12, fill=(35, 30, 24), outline=(160, 120, 70), width=1)
        port_txt = f"[ نصيحة معمارية: {data.get('portfolio_tip_ar', 'مناسب للمسابقات والبورتفوليو')} ]"
        draw.text((W // 2, tip_box_y + 35), prep(port_txt), font=font_tip, fill=(212, 163, 115), anchor="mm")

        # Footer
        draw.text((100, H - 65), "@MK.ARCHVIZ", font=ImageFont.truetype(FONT_BOLD, 26), fill=(212, 163, 115), anchor="lt")
        draw.text((W - 100, H - 65), prep("MK ARCHVIZ • استوديو الإظهار المعماري الذكي"), font=ImageFont.truetype(FONT_BOLD, 24), fill=(240, 240, 245), anchor="rt")

        out_path = f"generative_output/final_slide_{int(time.time())}.png"
        canvas.save(out_path)
        return out_path

if __name__ == "__main__":
    engine = GenerativeArchitectEngine()
    engine.run_full_cycle()
