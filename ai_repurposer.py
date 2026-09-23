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
أنت مهندس معماري استشاري وخبير محتوى رقمي على إنستغرام.
مهمتك: فحص المحتوى المعماري التالي (سواء كان صورة هندسية مرفقة أو نصاً)، واستخلاص الأفكار والنصائح الهندسية والمواد والأسلوب المعماري، وإعادة صياغتها بهوية استوديو معماري فخم لإنشاء كاروسيل (3 إلى 4 شرائح) + كابشن متكامل.

النص المرفق بالمنشور:
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
                    time.sleep(2)
                    
        return {"success": False, "error": "تعذر توليد الرد من نموذج الذكاء الاصطناعي"}
