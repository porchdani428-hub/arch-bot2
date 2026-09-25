import os
import time
import json
import requests
from typing import List, Optional, Callable

class TelegramService:
    """Handles sending carousel media groups and captions to Telegram, plus optional interactive bot listener."""
    
    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in .env!")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_message(self, text: str, reply_to_message_id: Optional[int] = None) -> bool:
        """Sends a text message to the configured chat."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
            
        try:
            resp = requests.post(url, json=payload, timeout=15)
            return resp.status_code == 200
        except Exception as e:
            print(f"[Telegram Error] send_message failed: {e}")
            return False

    def send_carousel(self, image_paths: List[str], caption_text: str) -> bool:
        """
        Sends the slides as a photo album (MediaGroup) and follows up with the complete Instagram caption.
        """
        if not image_paths:
            return False
            
        media_group_url = f"{self.base_url}/sendMediaGroup"
        
        media_list = []
        files = {}
        
        try:
            opened_files = []
            for idx, img_path in enumerate(image_paths):
                if not os.path.exists(img_path):
                    continue
                file_key = f"photo_{idx}"
                f = open(img_path, "rb")
                opened_files.append(f)
                files[file_key] = f
                
                media_list.append({
                    "type": "photo",
                    "media": f"attach://{file_key}",
                })
                
            payload = {
                "chat_id": self.chat_id,
                "media": json.dumps(media_list)
            }
            
            # Send album
            resp = requests.post(media_group_url, data=payload, files=files, timeout=60)
            
            # Close file handles
            for f in opened_files:
                f.close()
                
            if resp.status_code != 200:
                print(f"[Telegram Error] sendMediaGroup status {resp.status_code}: {resp.text}")
                return False
                
            # Send the caption right below the album
            full_caption_msg = (
                "📋 نص الكابشن المقترح (اضغط للنسخ والنشر مباشرة):\n\n"
                "----------------------------------------\n"
                f"{caption_text}\n"
                "----------------------------------------"
            )
            self.send_message(full_caption_msg)
            return True
            
        except Exception as e:
            print(f"[Telegram Error] send_carousel failed: {e}")
            return False

    def run_polling_listener(self, process_callback: Callable[[str, int], None]):
        """
        Runs a simple Telegram bot loop. Whenever you send an Instagram link to the bot from your phone,
        it automatically processes it and sends back the ready carousel slides and caption!
        """
        print("\n" + "="*50)
        print("🤖 [Telegram Bot Active] بانتظار الروابط من هاتفك على تيليغرام...")
        print("أرسل أي رابط منشور أو ريلز إنستغرام إلى البوت وسيقوم بتجهيز المنشور فوراً!")
        print("="*50 + "\n")
        
        offset = 0
        while True:
            try:
                url = f"{self.base_url}/getUpdates?offset={offset}&timeout=30"
                resp = requests.get(url, timeout=35)
                if resp.status_code != 200:
                    time.sleep(5)
                    continue
                    
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if not msg:
                        continue
                        
                    sender_chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()
                    msg_id = msg.get("message_id")
                    
                    if not text:
                        continue
                        
                    if text.startswith("/start") or text.startswith("/help") or text in ["مساعدة", "تعليمات"]:
                        welcome_msg = (
                            "مرحباً بك في أستوديو MK ARCHVIZ المعماري الذكي! 🏛️✨\n\n"
                            "الخيارات والأوامر المتاحة لك من هاتفك مباشرة:\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "1️⃣ 🔥 **تريندات وأخبار العمارة:**\n"
                            "   أرسل `/trends` أو كلمة `تريند` لاستعراض أبرز الموضوعات الشائعة (CNOA، الورشات، ArchDaily)، ثم أرسل رقم الموضوع (مثلاً `1`) ليتم توليد الكاروسيل كاملاً فوراً.\n\n"
                            "2️⃣ 🎨 **توليد تصميم معماري من الصفر:**\n"
                            "   أرسل `/generate` أو `توليد` لإنشاء فيلا/مبنى مع لوحة المفاهيم والبرومبت.\n\n"
                            "3️⃣ 📥 **إعادة إنتاج منشور إنستغرام:**\n"
                            "   أرسل أي رابط منشور أو ريلز لنسخه وتطويره بهوية MK ARCHVIZ.\n\n"
                            "4️⃣ ✍️ **صناعة كاروسيل من أي فكرة:**\n"
                            "   اكتب أي فكرة أو موضوع (مثل: رخصة البناء، نصائح الـ Jury، أخطاء التسليح) وسأصمم لك كاروسيل هندسي متكامل فوراً! 🚀"
                        )
                        self.send_message(welcome_msg, reply_to_message_id=msg_id)
                        continue
                        
                    try:
                        process_callback(text, msg_id)
                    except Exception as err:
                        print(f"[Callback Error]: {err}")
                        self.send_message(f"⚠️ حدث خطأ أثناء المعالجة: {str(err)[:150]}", reply_to_message_id=msg_id)
                        
            except requests.exceptions.RequestException:
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n[Bot Stopped] تم إيقاف البوت بنجاح.")
                break
            except Exception as e:
                print(f"[Polling Error]: {e}")
                time.sleep(3)
