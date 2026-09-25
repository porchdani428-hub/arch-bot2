import os
import json
import re
import time
from google import genai
from typing import Dict, Any, Optional, List
import config

class ArchitecturalRepurposer:
    """
    Intelligent architectural content engine tailored for Algerian & Arab architecture
    students and practicing architects, with deep knowledge of CNOA regulations,
    EPAU/university atelier workflows, BIM, site execution, and faithful slide-by-slide recreation.
    """
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing! Please provide it in .env or constructor.")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.6-flash"
        
    def repurpose(self, original_text: str, media_path: Optional[str] = None, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        import config

        # Collect images for Vision analysis
        target_imgs = []
        if image_paths:
            target_imgs = [p for p in image_paths if p and os.path.exists(p)]
        elif media_path and os.path.exists(media_path):
            target_imgs = [media_path]

        num_images = len(target_imgs)
        is_carousel = num_images > 1

        # Specific instructions based on whether we are replicating an Instagram carousel or processing a text topic
        if is_carousel:
            mode_instruction = f"""
أمامك منشور إنستغرام أصلي يتكون من {num_images} شرائح مصورة بالترتيب.
مهمتك المحورية الإلزامية:
1. اقرأ كل شريحة بدقة تامة: الشريحة الأولى هي الغلاف (Hook)، والشرائح اللاحقة هي شرائح المحتوى.
2. التزم بنفس تسلسل وبنفس عدد شرائح المنشور الأصلي تماماً (يجب أن تخرج بالضبط {min(num_images - 1, 10)} شرائح محتوى تمثل كل شريحة تم استخراجها بالترتيب)!
3. استخرج نوع التخطيط البصري الأنسب لكل شريحة (layout_type):
   - "definition_table": إذا كانت الشريحة جدول مصطلحات أو اختصارات وتعريفها (مثل VHS, TD, TP, CC, Examen, Coef).
   - "hero_spotlight": إذا كانت الشريحة تركز على مادة أو عنصر أساسي كبير مع إحصائيات ومعامل وملاحظة ختامية.
   - "cards_grid": إذا كانت الشريحة تعرض قائمة بطاقات أو مواد مجمعة.
   - "standard_bullets": للخطوات والنصائح المعمارية المباشرة.
4. ارتقِ بالمحتوى إلى أعلى المعايير المعمارية الحقيقية بنصائح هندسية تطبيقية تلمس واقع طلبة ومعماريي الجزائر.
"""
        else:
            mode_instruction = """
مهمتك المحورية الإلزامية:
صياغة كاروسيل معماري تحفة فنية بعدد شرائح ديناميكي حر (يتراوح بين 4 إلى 10 شرائح بحسب ما يتطلبه عمق ودسامة الموضوع - ممنوع الحصر في 5 شرائح فقط)!
- إذا كان الموضوع دليلاً شاملاً أو مرجعياً (مثل سنوات دراسة العمارة، دليل المواد، كواليس التربص CNOA، خطوات الـ BIM، قوانين الورشة): صمم دليلاً دقيقاً وغنياً من 6 إلى 9 شرائح محتوى + غلاف + شريحة ختامية.
- نوع في تخطيطات الشرائح (layout_type) بذكاء لتفادي الملل البصري:
  1. شريحة غلاف (Cover) باهرة ودافئة بهوية الأتيلييه.
  2. شريحة "definition_table" لشرح المصطلحات والاختصارات الهندسية.
  3. شريحة "hero_spotlight" لتسليط الضوء على المادة الأهم أو القاعدة المحورية.
  4. شريحة "cards_grid" لتجميع المواد أو العناصر الفرعية.
  5. شرائح "standard_bullets" للخطوات والنصائح المعمارية التطبيقية.
  6. شريحة ختامية "cta" جذابة للحفظ والمشاركة في الأتيلييه.
"""

        prompt = f"""
أنت المدير الإبداعي لاستوديو MK ARCHVIZ في الجزائر، مهندس معماري استشاري بارع وموجّه ملهم لطلبة العمارة والمعماريين في الجزائر والوطن العربي.

الهوية والأسلوب (Persona & Tone of Voice):
- نبرة راقية، ملهمة، دافئة وحميمية من قلب الأتيلييه، تشبه أسلوب أرقى استوديوهات العمارة الجزائرية (@atelier__nove).
- لغتك: مزيج راقٍ وطبيعي بين العربية الفصحى الأنيقة، اللهجة الجزائرية الدافئة المتداولة في الجامعات والورشات، والمصطلحات الهندسية الفرنسية/الإنجليزية الحقيقية:
  (طالب Architecture 👀، هذا الـ Guide راح يكون مرجعك من أول سنة حتى التخرج 🏛️📐، الأتيلييه، الشاريت، الروندو، الـ Project لازم تعطيه حقو، Sauvegarde le post 📌، ابعثو لصحابك في الأتيلييه).
- ممنوع منعاً باتاً: الكلام الإنشائي الركيك، المصطلحات المترجمة ترجمة حرفية سطحية، والعبارات الأكاديمية الباهتة مثل "نصائح ذهبية..." أو "مما لا شك فيه...".
- قواعد التنسيق والمصطلحات الأجنبية (Arabic + Latin Typography):
  1. عند ذكر مصطلح تقني بالفرنسية أو الإنجليزية، اجعله مدمجاً بسلاسة مع التعبير العربي أو ضعه داخل قوسين ملاصقاً له: مثل: مخطط الكتلة (Plan de masse)، رخصة البناء (Permis de construire)، برنامج ريفيت (Revit)، أوتوكاد (AutoCAD)، إعادة العمل (Rework)، مكتب المراقبة التقنية (CTC).
  2. ممنوع وضع كلمات إنجليزية منفردة مثل (The Why) في نهاية الأسئلة أو بعد علامة الاستفهام. اجعل السؤال أو العنوان عربياً خالصاً ومباشراً: مثلاً "لماذا لم يعد AutoCAD كافياً لسوق العمل المعماري؟" بدلاً من "لماذا لم يعد الـ CAD كافيا؟ (The Why)".
  3. التزم بوضع علامات الترقيم (النقطتان :، علامة الاستفهام ؟، الفاصلة ،) ملاصقة للكلمة التي تسبقها تماماً وفي موضعها المنطقي السليم.

- قاعدة توليد صور الخلفية (Dynamic Background Generation):
  * يجب أن تبتكر في حقل "background_image_prompt" برومبت باللغة الإنجليزية لتوليد صورة خلفية معمارية مخصصة ومبتكرة تتغير 100% حسب موضوع وفكرة المنشور:
    - إذا كان المنشور عن فيلا سكنية: ولد واجهة فيلا خرسانية/خشبية مودرن فاخرة مع طبيعة متوسطية وشمس دافئة.
    - إذا كان المنشور عن كواليس الأتيلييه أو أدوات الرسم أو برامج الـ CAD/BIM: ولد مشهد طاولة رسم معمارية مع مخططات وماكيت خشب ومساطر.
    - إذا كان المنشور عن مواد البناء أو الواجهات: ولد تفاصيل خامات معمارية حقيقية (حجر، خرسانة مكشوفة، زجاج، تفاصيل معدنية).
    - إذا كان المنشور عن مشاريع عامة أو أبراج: ولد مشهد كتل معمارية وساحات عامة بلمسة تحريرية راقية.
  * شرط إلزامي صارم في نهاية كل برومبت خلفية: "pure architecture, no human faces, no portraits, warm elegant sunlight, architectural digest photography, 8k photorealistic".

{mode_instruction}

المحتوى النصي أو الفكرة المرفقة:
\"\"\"
{original_text or 'لا يوجد نص كابشن تفصيلي - اعتمد بالكامل على قراءة وفهم النصوص والرسومات الموجودة في شرائح الصور المرفقة'}
\"\"\"

المطلوب: أخرج فقط كائن JSON صالح وبدون أي نصوص قبله أو بعده، بالهيكل التالي:
{{
  "theme": "atelier_prestige",
  "category": "دليل طالب العمارة",
  "background_image_prompt": "overhead flatlay aesthetic architectural desk, warm cream textured linen paper parchment, subtle blueprint sketch of classical building, small balsa wood architectural study model, vintage brass fountain pen, triangular architect scale ruler, delicate olive branch casting soft sunlight shadows, warm ivory beige tones, architectural digest luxury editorial, 8k photorealistic, pure architecture, no human faces",
  "cover": {{
    "super_title": "GUIDE DE L'ÉTUDIANT EN",
    "hero_title": "ARCHITECTURE",
    "hook_tag": "طالب Architecture 👀",
    "title": "هذا الـ Guide راح يكون مرجعك من أول سنة حتى التخرج 🏛️📐",
    "subtitle": "كل ما يحتاجه طالب ومعماري الجزائر في مكان واحد 🤍",
    "footer_tags": "Plans • Coupes • Façades • Échelles • Logiciels • Conseils"
  }},
  "content_slides": [
    {{
      "layout_type": "definition_table",
      "headline": "قبل ما تبدأ... لازم تفهم هاذ المصطلحات 👀",
      "table_items": [
        {{"term": "VHS", "explanation": "مجموع السوايع تاع المادة في السداسي"}},
        {{"term": "Cours", "explanation": "الكور / المحاضرة النظرية"}},
        {{"term": "TD", "explanation": "الأعمال الموجهة في الأتيلييه"}},
        {{"term": "TP", "explanation": "الأعمال التطبيقية والمخابر"}},
        {{"term": "CC", "explanation": "المراقبة المستمرة وتقييم الروندو"}},
        {{"term": "Examen", "explanation": "امتحان نهاية السداسي"}},
        {{"term": "Coefficient", "explanation": "المعامل: شحال تأثر المادة على المعدل"}}
      ]
    }},
    {{
      "layout_type": "hero_spotlight",
      "headline": "المادة لي عندها أكبر معامل",
      "hero_title": "ATELIER DE PROJET",
      "coef_text": "— COEF. 4 —",
      "stats": [
        {{"value": "180 ساعة في السداسي", "label": "الساعات الإجمالية للورشة"}},
        {{"value": "12 ساعة في الأسبوع", "label": "معدل الحصص الأسبوعية"}},
        {{"value": "100% مراقبة مستمرة", "label": "تقييم مستمر دون امتحان كتابي"}}
      ],
      "takeaway": "يعني Project لازم تعطيه حقو وتخدمو بانتظام!"
    }},
    {{
      "layout_type": "cards_grid",
      "headline": "وش هذا المواد لي معاملها 2 ؟",
      "cards": [
        {{"title": "Histoire de l'Architecture", "desc": "تاريخ النظريات وتطور الأنماط"}},
        {{"title": "Théorie de Projet", "desc": "مفاهيم التصميم وتحليل الموقع"}},
        {{"title": "Géométrie de l'espace", "desc": "الهندسة الوصفية والإسقاط الفضائي"}},
        {{"title": "TMC", "desc": "تكنولوجيا مواد البناء والإنشاء"}}
      ],
      "bottom_quote": "كل مادة فيهم معاملها = 2"
    }},
    {{
      "layout_type": "standard_bullets",
      "headline": "أسرار اجتياز ليلة الـ Rendu بنجاح",
      "bullets": [
        "نظم مخططات الـ Plan و Coupes قبل التفكير في الريندر المعقد",
        "احرص على قراءة المقياس (Échelle) بدقة على الورق قبل الطباعة",
        "الماكيت (Maquette) النظيفة تختصر نصف وقت الشرح أمام الـ Jury"
      ],
      "takeaway": "الـ Jury يهمه وضوح الفكرة والمساقط قبل بهرجة الألوان!"
    }}
  ],
  "cta_slide": {{
    "main_question": "درك فهمتي البرنامج تاعك أكثر؟ 🤍",
    "cta_badge": "Sauvegarde le post 📌",
    "cta_quote": "وابعثيه لصديقتك في الأتيلييه لي راهي ضايعة مع البرنامج!",
    "summary_points": ["نظم وقت الأتيلييه", "ركز على المواد الأساسية", "احتفظ بالدليل عندك"]
  }},
  "instagram_caption": "كابشن إنستغرام كامل مع هوك واقعي يشعل التفاعل، ونقاط مرتبة، وهاشتاغات جزائرية وعربية قوية (#architecture_algerie #cnoa #epau #algerian_architects #etudiant_architecture #mk_archviz)"
}}
"""

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
                        {"role": "system", "content": "أنت المدير الإبداعي لاستوديو MK ARCHVIZ في الجزائر. أنت مهندس معماري استشاري بارع وموجّه لطلبة ومعماريي الجزائر. اقرأ جميع نصوص ومخططات الشرائح بدقة، وأخرج دائماً كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": user_content if target_imgs else prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = self._extract_json(raw_text)
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
                        {"role": "system", "content": "أنت المدير الإبداعي لاستوديو MK ARCHVIZ في الجزائر. اقرأ جميع نصوص الشرائح وأخرج كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": user_content if target_imgs else prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = self._extract_json(raw_text)
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
                    json_str = self._extract_json(raw_text)
                    data = json.loads(json_str)
                    return {"success": True, "data": data}
                except Exception as e:
                    print(f"  ⚠️ تنبيه نموذج {m}: {e}")
                    time.sleep(1)

        return {"success": False, "error": "تعذر تحليل المحتوى بالذكاء الاصطناعي."}

    def _extract_json(self, raw_text: str) -> str:
        if "```json" in raw_text:
            return raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            return raw_text.split("```")[1].split("```")[0].strip()
        else:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1:
                return raw_text[start:end+1]
        return raw_text

    def modify_post(self, current_data: dict, edit_instruction: str) -> dict:
        """Modifies existing post JSON with surgical precision based on user instruction."""
        prompt = f"""
أنت المحرر الإبداعي والمدقق المعماري في استوديو MK ARCHVIZ.
أمامك هيكل JSON الكامل لمنشور الكاروسيل المعماري الحالي:
```json
{json.dumps(current_data, ensure_ascii=False, indent=2)}
```

طلب المستخدم للتعديل الدقيق:
"{edit_instruction}"

مهمتك الإلزامية:
1. نفّذ التعديل المطلوب من المستخدم بدقة جراحية متناهية (تعديل نص معين، عنوان، كبسولة، تبديل كلمة، حذف نقطة، تعديل كابشن، أو تعديل الخلفية).
2. حافظ بدقة 100% على كافة الحقول والنصوص والهيكل وشرائح المنشور الأخرى كما هي دون أي تغيير غير مطلوب.
3. إذا طلب المستخدم تغيير صورة الخلفية (مثلاً: "غير الخلفية لفيلا مودرن" أو "اجعل الخلفية طاولة رسم معمارية")، قم بتعديل حقل "background_image_prompt" فقط بالإنجليزية بما يطابق طلبه، مع إضافة: "pure architecture, no human faces, 8k".
4. إذا كان التعديل في شريحة معينة (الغلاف، شريحة 2، شريحة 3...)، عدل نصوص تلك الشريحة فقط.
5. أخرج فقط كائن JSON المحدّث كاملاً بدون أي كلام قبله أو بعده.
"""
        # 1. Try XKiro AI first
        if config.XKIRO_API_KEY:
            try:
                from openai import OpenAI
                ai_client = OpenAI(api_key=config.XKIRO_API_KEY, base_url=config.XKIRO_BASE_URL)
                resp = ai_client.chat.completions.create(
                    model=config.XKIRO_MODEL,
                    messages=[
                        {"role": "system", "content": "أنت المحرر الإبداعي لاستوديو MK ARCHVIZ. أخرج دائماً كائن JSON صالح فقط بدون أي مقدمات."},
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = self._extract_json(raw_text)
                data = json.loads(json_str)
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ تنبيه محرك XKiro في التعديل: {e}")

        # 2. Try CometAPI / GPT-4o-mini
        if config.IMAGE_API_KEY:
            try:
                from openai import OpenAI
                base_url = config.IMAGE_BASE_URL or "https://api.cometapi.com/v1"
                if not base_url.endswith("/v1"):
                    base_url = f"{base_url.rstrip('/')}/v1"
                ai_client = OpenAI(api_key=config.IMAGE_API_KEY, base_url=base_url)
                resp = ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "أنت المحرر الإبداعي لاستوديو MK ARCHVIZ. أخرج دائماً كائن JSON صالح فقط."},
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_text = resp.choices[0].message.content.strip()
                json_str = self._extract_json(raw_text)
                data = json.loads(json_str)
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ تنبيه GPT-4o-mini في التعديل: {e}")

        # 3. Fallback to Gemini
        models = [self.model, "gemini-3.5-flash", "gemini-flash-latest"]
        for m in models:
            try:
                response = self.client.models.generate_content(
                    model=m,
                    contents=[prompt]
                )
                raw_text = response.text.strip()
                json_str = self._extract_json(raw_text)
                data = json.loads(json_str)
                return {"success": True, "data": data}
            except Exception as e:
                print(f"  ⚠️ تنبيه Gemini في التعديل: {e}")

        return {"success": False, "error": "تعذر تطبيق التعديل بالذكاء الاصطناعي."}
