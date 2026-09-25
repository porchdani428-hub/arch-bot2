import os
import re
import html
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

class ArchitecturalTrendsTracker:
    """
    Tracks and curates trending architectural news, projects, and discussions
    from reliable global sources (ArchDaily, Dezeen) and Algerian/Arab professional
    architectural contexts (CNOA, EPAU/universities, construction regulations, AI tools).
    """

    ARCHDAILY_RSS = "https://www.archdaily.com/feed"
    
    # Curated bank of perennial and trending Algerian & Arab architectural topics
    # tailored specifically for students (EPAU/Universities) and practicing architects (CNOA/Chantiers)
    ALGERIAN_PRACTICE_TRENDS = [
        {
            "title": "كواليس تربص الـ 18 شهراً CNOA: كيف تملأ دفتر التربص (Carnet de Stage) وتحمي حقوقك في مكاتب الدراسات؟",
            "category": "الممارسة المهنية والاعتماد",
            "source": "CNOA Algeria / الممارسة الميدانية",
            "summary": "دليل واقعي للمهندس المعماري المتربص في الجزائر: شروط إيداع الملف، اختيار المعماري المشرف، صياغة تقارير الورشة الأسبوعية، والتحضير لمناقشة نيل الاعتماد والختم الرسمي.",
            "prompt_hint": "architectural blueprints, legal stamping seal, drafting table with detailed building plans, soft warm lamp lighting, 8k architectural digest"
        },
        {
            "title": "رخصة البناء في الجزائر (Permis de Construire): أسرار إعداد الملف التقني والمطابقة مع المرسوم التنفيذي 15-19",
            "category": "التشريع والصفقات المعمارية",
            "source": "قانون العمران والتهيئة 15-19",
            "summary": "كل ما يحتاجه المعماري الشاب: من مخطط الكتلة (Plan de masse) وشبكات الصرف إلى تقرير التقديم وعلاقة الملف مع الحماية المدنية ومهندسي الهندسة المدنية (Génie Civil).",
            "prompt_hint": "modern architectural site plan and structural blueprints laid out on dark marble table, high precision drafting instruments, 8k"
        },
        {
            "title": "سهرات الشاريت (La Charrette) في كليات العمارة الجزائرية (EPAU والجامعات): كيف تنجو من ليلة الروندو وتُبهر الـ Jury؟",
            "category": "حياة طالب العمارة",
            "source": "استوديوهات التصميم والـ Ateliers",
            "summary": "نصائح عملية من قلب الأتيلييه لتنظيم وقت الإسبيس (Esquisse) والماكيت (Maquette) والإخراج النهائي، وتجنب الانهيار قبل تسليم مشروع السنة أو مذكرة التخرج (PFE).",
            "prompt_hint": "contemporary architecture design atelier studio, glowing architectural physical models, drafting boards, timber beams, dramatic evening lighting, 8k"
        },
        {
            "title": "من AutoCAD إلى Revit و BIM: خارطة طريق الانتقال لبرامج النمذجة الحديثة التي يطلبها سوق العمل المعماري",
            "category": "البرمجيات والـ BIM",
            "source": "سوق العمل وتقنيات النمذجة",
            "summary": "لماذا لم يعد الرسم ثنائي الأبعاد كافياً؟ كيف تبدأ في نمذجة الـ BIM، تنسيق المخططات مع مهندسي الإنشاء، وربط المشروع مع محركات الريندر الواقعية (Corona, D5 Render, Lumion).",
            "prompt_hint": "high-tech modern architectural firm workspace, large dual monitors displaying complex BIM wireframe and 3D villa render, sleek studio, 8k"
        },
        {
            "title": "متابعة الورشة (Suivi de Chantier): كيف يفرض المعماري هيبته أمام المقاول ويراقب صب الخرسانة والتسليح؟",
            "category": "إدارة الورشات والتنفيذ",
            "source": "الواقع الميداني الجزائري",
            "summary": "الميدان لا يرحم: كيف تقرأ مخططات الـ Ferraillage، تتعامل مع مكتب المراقبة CTC، وتدوّن محاضر الورشة (PV de chantier) بطريقة قانونية لا تدع مجالاً للتلاعب.",
            "prompt_hint": "dramatic wide angle of a modern concrete building construction site at twilight, exposed structural columns, raw board-formed concrete, cinematic lighting, 8k"
        },
        {
            "title": "العمارة البيومناخية (Architecture Bioclimatique) في الجزائر: دروس من العمارة التقليدية الصحراوية والساحلية",
            "category": "الاستدامة والتصميم المناخي",
            "source": "العمارة المحلية والمناخية",
            "summary": "توظيف الفناء الداخلي (Patio)، التهوية المتقاطعة، العزل الحراري، ومصدات الشمس (Brise-soleil) لتحقيق راحة حرارية بأقل استهلاك للطاقة.",
            "prompt_hint": "contemporary bioclimatic modern residence with internal courtyard patio, geometric brise-soleil timber louvers, natural water reflection, dusk light, 8k"
        }
    ]

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_global_trends(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches latest real architectural news from ArchDaily RSS."""
        trends = []
        try:
            resp = requests.get(self.ARCHDAILY_RSS, headers=self.headers, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for item in items[:limit]:
                    raw_title = item.find("title").text if item.find("title") is not None else ""
                    clean_title = html.unescape(raw_title).strip()
                    link = item.find("link").text if item.find("link") is not None else ""
                    raw_desc = item.find("description").text if item.find("description") is not None else ""
                    clean_desc = re.sub(r"<[^>]+>", "", html.unescape(raw_desc)).strip()
                    
                    trends.append({
                        "title": clean_title,
                        "source": "ArchDaily",
                        "link": link,
                        "summary": clean_desc[:220] + "..." if len(clean_desc) > 220 else clean_desc,
                        "category": "مشاريع عالمية وتريندات"
                    })
        except Exception as e:
            print(f"[Trends Notice] ArchDaily fetch error: {e}")
        return trends

    def get_curated_topics(self, total: int = 6) -> List[Dict[str, Any]]:
        """
        Combines live global news from ArchDaily with tailored Algerian
        architectural practice topics, prioritizing what matters most to students & practitioners.
        """
        results = []
        
        # 1. Add 3 curated Algerian practice & student topics (cyclically based on day)
        day_seed = int(time.strftime("%j")) # day of year
        algerian_count = len(self.ALGERIAN_PRACTICE_TRENDS)
        for i in range(3):
            idx = (day_seed + i) % algerian_count
            results.append(self.ALGERIAN_PRACTICE_TRENDS[idx])
            
        # 2. Add 3 live ArchDaily global news
        global_news = self.fetch_global_trends(limit=3)
        results.extend(global_news)
        
        return results[:total]

    def format_trends_message(self, topics: List[Dict[str, Any]]) -> str:
        """Formats the list of trends into an engaging Arabic Telegram menu."""
        msg = "🔥 **أبرز تريندات وأخبار العمارة اليوم (مختارة خصيصاً لـ MK ARCHVIZ):**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "اختر أي رقم لتوليد كاروسيل هندسي متكامل فوراً بهويتك المعمارية:\n\n"
        
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        for idx, t in enumerate(topics):
            emoji = number_emojis[idx] if idx < len(number_emojis) else f"[{idx+1}]"
            title = t.get("title", "")
            source = t.get("source", "عالمي")
            category = t.get("category", "عمارة")
            summary = t.get("summary", "")
            
            msg += f"{emoji} **{title}**\n"
            msg += f"   🏷️ *التصنيف:* {category} | 📌 *المصدر:* {source}\n"
            if summary:
                # brief one liner
                first_line = summary.split(".")[0].strip()
                if first_line:
                    msg += f"   💡 _{first_line}_\n"
            msg += "\n"
            
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💬 **للتوليد الفوري:** أرسل رقم الخبر فقط (مثلاً: `1` أو `توليد 1`) وسيقوم البوت بصياغة وتصميم الكاروسيل كاملاً وتسليمه لك!"
        return msg
