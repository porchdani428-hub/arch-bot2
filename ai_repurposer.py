import os
import json
import re
import time
from google import genai
from typing import Dict, Any, Optional

class ArchitecturalRepurposer:
    """Uses Gemini 3.6 Flash to repurpose architectural posts into carousels."""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing! Please provide it in .env or constructor.")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.6-flash"
        
    def repurpose(self, original_text: str, media_path: Optional[str] = None) -> Dict[str, Any]:
        prompt = f"""
أنت مهندس معماري استشاري وخبير محتوى رقمي ومعماري متخصص.
تمتلك دراية تامة بمصطلحات ومسار الممارسة المهنية المعمارية في الوطن العربي والمغرب العربي/الجزائر (مثل: تربص الـ 18 شهراً الإلزامي لنيل الاعتماد والختم الرسمي تحت إشراف هيئة المهندسين المعماريين CNOA، دفتر التربص Carnet de stage، مكاتب الدراسات، رخص البناء والتنفيذ، إدارة الورشات والمقاولات، وتقنيات BIM).

مهمتك: فحص الموضوع المعماري التالي بدقة متناهية، وتقديم معلومات قانونية وتقنية وهندسية صحيحة 100% وواقعية جداً، وصياغتها بهوية استوديو معماري راقٍ لإنشاء كاروسيل احترافي (3 إلى 4 شرائح) + كابشن إنستغرام متكامل.

المحتوى أو الفكرة المطلوبة:
\"\"\"
{original_text or 'لا يوجد كابشن - اعتمد بالكامل على التحليل البصري للصورة المرفقة'}
\"\"\"

المطلوب: أخرج فقط كائن JSON صالح وبدون أي نصوص قبله أو بعده، بالهيكل التالي:
{{
  "category": "أدوات وذكاء اصطناعي",
  "cover": {{
    "title": "عنوان جذاب وقصير جداً كغلاف للكاروسيل (Hook قوي لا يتجاوز 7 كلمات)",
    "subtitle": "سطر توضيحي موجز يبين كيف نوظف هذه الأداة أو النصيحة بذكاء"
  }},
  "content_slides": [
    {{
      "headline": "عنوان شريحة المحتوى (موجز ومباشر)",
      "bullets": [
        "نصيحة أو خطوة هندسية دقيقة 1",
        "نصيحة أو معلومة عملية محددة 2"
      ],
      "tip": "إضاءة هندسية مركزة أو نصيحة احترافية (سطر واحد)"
    }}
  ],
  "cta_slide": {{
    "summary_points": [
      "خلاصة سريعة للنقطة الأولى",
      "خلاصة سريعة للنقطة الثانية",
      "خلاصة سريعة للنقطة الثالثة"
    ],
    "cta_text": "احفظ هذا الدليل لتجده في مشروعك القادم"
  }},
  "instagram_caption": "النص الكامل للمنشور على إنستغرام مع مسافات وهيكلية أنيقة وهاشتاغات هندسية عربية قوية"
}}
"""
        import config

        # 1. Try XKiro AI (5 Million Free Tokens / Day - Qwen 3.8 Omni)
        if config.XKIRO_API_KEY and not media_path:
            try:
                print(f"  ⚡ استخدام محرك XKiro AI المجاني ({config.XKIRO_MODEL})...")
                from openai import OpenAI
                ai_client = OpenAI(api_key=config.XKIRO_API_KEY, base_url=config.XKIRO_BASE_URL)
                resp = ai_client.chat.completions.create(
                    model=config.XKIRO_MODEL,
                    messages=[
                        {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. أخرج دائماً كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = raw_text
                if "```json" in raw_text:
                    json_str = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    json_str = raw_text.split("```")[1].split("```")[0].strip()
                else:
                    start = raw_text.find("{")
                    end = raw_text.rfind("}")
                    if start != -1 and end != -1:
                        json_str = raw_text[start:end+1]
                        
                data = json.loads(json_str)
                print("  ✅ تم التحليل والصياغة عبر محرك XKiro AI بنجاح!")
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ تنبيه محرك XKiro: {e}, جاري الانتقال للمحركات الأخرى...")

        from PIL import Image
        contents = [prompt]
        if media_path and os.path.exists(media_path):
            try:
                img = Image.open(media_path)
                contents = [img, prompt]
                print(f"  👁️ تم تفعيل Gemini Vision لتحليل بكسلات الصورة: {os.path.basename(media_path)}")
            except Exception as e:
                print(f"  ⚠️ تعذر فتح الصورة للتحليل البصري: {e}")

        models = [self.model, "gemini-3.5-flash", "gemini-flash-latest"]
        for m in models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=m,
                        contents=contents
                    )
                    raw_text = response.text.strip()
                    # Extract JSON string
                    json_str = raw_text
                    if "```json" in raw_text:
                        json_str = raw_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_text:
                        json_str = raw_text.split("```")[1].split("```")[0].strip()
                    else:
                        start = raw_text.find("{")
                        end = raw_text.rfind("}")
                        if start != -1 and end != -1:
                            json_str = raw_text[start:end+1]
                            
                    data = json.loads(json_str)
                    return {"success": True, "data": data}
                except Exception as e:
                    print(f"  ⚠️ تنبيه نموذج {m}: {e}")
                    time.sleep(1)

        # Fallback to CometAPI / OpenAI (GPT-4o-mini)
        import config
        if config.IMAGE_API_KEY:
            try:
                print("  🔄 تفعيل المحرك البديل الفائق (GPT-4o-mini) عبر CometAPI...")
                from openai import OpenAI
                base_url = config.IMAGE_BASE_URL or "https://api.cometapi.com/v1"
                if not base_url.endswith("/v1"):
                    base_url = f"{base_url.rstrip('/')}/v1"
                ai_client = OpenAI(api_key=config.IMAGE_API_KEY, base_url=base_url)
                
                resp = ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. أخرج كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = raw_text
                if "```json" in raw_text:
                    json_str = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    json_str = raw_text.split("```")[1].split("```")[0].strip()
                else:
                    start = raw_text.find("{")
                    end = raw_text.rfind("}")
                    if start != -1 and end != -1:
                        json_str = raw_text[start:end+1]
                        
                data = json.loads(json_str)
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ فشل المحرك البديل: {e}")
                    
        return {"success": False, "error": "تم استنفاد كوتا طلبات Gemini المجانية لليوم. تم تفعيل البديل التلقائي أو يرجى إضافة مفتاح جديد من aistudio.google.com"}
