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
        
    def repurpose(self, original_text: str, media_path: Optional[str] = None, image_paths: Optional[list] = None) -> Dict[str, Any]:
        prompt = f"""
أنت مهندس معماري استشاري وخبير محتوى رقمي ومعماري متخصص.
تمتلك دراية تامة بمصطلحات ومسار الممارسة المهنية المعمارية في الوطن العربي والمغرب العربي/الجزائر (مثل: سنوات الدراسة المعمارية والتكوين، تربص الـ 18 شهراً الإلزامي لنيل الاعتماد CNOA، دفتر التربص Carnet de stage، مكاتب الدراسات، رخص البناء، إدارة الورشات والمقاولات، تقنيات BIM ونمذجة 3D).

مهمتك: 
1. فحص وقراءة جميع النصوص والشروحات والرسومات التخطيطية الموجودة داخل الشرائح المرفقة والكابشن بدقة تامة.
2. استخراج الأفكار والنصائح الهندسية الحقيقية الموجودة في كل شريحة من المنشور الأصلي وتطويرها هندسياً بأسلوب راقٍ يليق باستوديو معماري فخم.
3. صياغة كاروسيل متكامل (3 إلى 5 شرائح) + كابشن إنستغرام متكامل مع الهاشتاغات.

المحتوى النصي أو الفكرة المرفقة:
\"\"\"
{original_text or 'لا يوجد نص كابشن تفصيلي - اعتمد بالكامل على قراءة وفهم النصوص والرسومات الموجودة في شرائح الصور المرفقة'}
\"\"\"

المطلوب: أخرج فقط كائن JSON صالح وبدون أي نصوص قبله أو بعده، بالهيكل التالي:
{{
  "category": "تصنيف المنشور (مثال: سنوات الدراسة والتكوين)",
  "background_image_prompt": "creative Midjourney/DALL-E prompt in English for an ultra-realistic architectural background image specifically reflecting this topic. STRICT RULES: NO human faces, NO portraits, NO recognizable people. Focus purely on architectural spaces, facades, structural concrete/timber volumes, glass reflections, materials, physical models, and dramatic lighting. Pure architecture, no faces, architectural digest style, Hasselblad 8k, photorealistic",
  "cover": {{
    "title": "عنوان جذاب وقوي كغلاف للكاروسيل (Hook لا يتجاوز 7 كلمات)",
    "subtitle": "سطر توضيحي موجز يبين زبدة الموضوع"
  }},
  "content_slides": [
    {{
      "headline": "عنوان شريحة المحتوى (موجز ومباشر ومستوحى من الشريحة)",
      "bullets": [
        "نصيحة أو خطوة هندسية دقيقة ومستخرجة من الشريحة 1",
        "نصيحة أو معلومة عملية محددة 2",
        "إضاءة أو نصيحة احترافية مكملة 3"
      ]
    }}
  ],
  "cta_slide": {{
    "summary_points": [
      "خلاصة سريعة للنقطة الأولى",
      "خلاصة سريعة للنقطة الثانية",
      "خلاصة سريعة للنقطة الثالثة"
    ],
    "cta_text": "احفظ هذا الدليل وشاركه مع زملائك المعماريين"
  }},
  "instagram_caption": "النص الكامل للمنشور على إنستغرام مع مسافات وهيكلية أنيقة وهاشتاغات هندسية عربية قوية"
}}
"""
        import config

        # Collect images for Vision analysis
        target_imgs = []
        if image_paths:
            target_imgs = [p for p in image_paths if p and os.path.exists(p)]
        elif media_path and os.path.exists(media_path):
            target_imgs = [media_path]

        # Prepare messages payload
        user_content = [{"type": "text", "text": prompt}]
        if target_imgs:
            import base64
            print(f"  👁️ تفعيل الرؤية الحاسوبية وقراءة {len(target_imgs[:6])} شرائح من المنشور الأصلي بالذكاء الاصطناعي...")
            for p in target_imgs[:6]:
                try:
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
                except Exception as e:
                    print(f"  ⚠️ تعذر تجهيز شريحة للتحليل البصري: {e}")

        # 1. Try XKiro AI (5 Million Free Tokens / Day - Qwen 3.8 Omni with Vision)
        if config.XKIRO_API_KEY:
            try:
                print(f"  ⚡ استخدام محرك XKiro AI الرؤيوي ({config.XKIRO_MODEL})...")
                from openai import OpenAI
                ai_client = OpenAI(api_key=config.XKIRO_API_KEY, base_url=config.XKIRO_BASE_URL)
                resp = ai_client.chat.completions.create(
                    model=config.XKIRO_MODEL,
                    messages=[
                        {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. اقرأ جميع نصوص ومخططات الشرائح بدقة، وأخرج دائماً كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": user_content if target_imgs else prompt}
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
                print("  ✅ تم التحليل وقراءة الشرائح بنجاح عبر محرك XKiro AI!")
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ تنبيه محرك XKiro: {e}, جاري الانتقال للمحركات الأخرى...")

        # 2. Try CometAPI / OpenAI (GPT-4o-mini with Vision)
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
                        {"role": "system", "content": "أنت مهندس معماري استشاري وخبير محتوى رقمي. اقرأ جميع نصوص الشرائح وأخرج كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": user_content if target_imgs else prompt}
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
                print("  ✅ تم التحليل بنجاح عبر GPT-4o-mini!")
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ فشل المحرك البديل GPT-4o-mini: {e}")

        # 3. Fallback to Gemini
        from PIL import Image
        contents = [prompt]
        if target_imgs:
            for p in target_imgs[:4]:
                try:
                    contents.insert(0, Image.open(p))
                except Exception:
                    pass

        models = [self.model, "gemini-3.5-flash", "gemini-flash-latest"]
        for m in models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=m,
                        contents=contents
                    )
                    raw_text = response.text.strip()
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

        return {"success": False, "error": "تعذر تحليل المحتوى بالذكاء الاصطناعي."}
