import os
import re
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

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

def clean_emojis(text: str) -> str:
    if not text:
        return ''
    emoji_pattern = re.compile(
        '[𐀀-􏿿]'
        '|[☀-⛿]'
        '|[✀-➿]'
        '|[⭐⭕⌚⌛⏩-⏬⏰⏳]'
        '|[‍️]', 
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    cleaned = cleaned.replace('✔', '').replace('✅', '').replace('💡', '').replace('⬅', '>>').replace('➡', '<<')
    return cleaned.strip()

def prepare_arabic(text: str) -> str:
    if not text:
        return ''
    cleaned = clean_emojis(text)
    reshaped = arabic_reshaper.reshape(cleaned)
    return get_display(reshaped)

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    cleaned = clean_emojis(text)
    words = cleaned.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        reshaped_test = prepare_arabic(test_line)
        bbox = draw.textbbox((0, 0), reshaped_test, font=font)
        line_w = bbox[2] - bbox[0]
        
        if line_w > max_width and len(current_line) > 1:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines

class ArchitecturalSlideDesigner:
    WIDTH = 1080
    HEIGHT = 1350
    
    COLOR_BG = (18, 20, 24)
    COLOR_CARD = (28, 31, 38)
    COLOR_BORDER = (45, 50, 62)
    COLOR_ACCENT = (212, 163, 115)
    COLOR_TEXT_PRIMARY = (245, 245, 247)
    COLOR_TEXT_SECONDARY = (165, 170, 180)
    COLOR_TIP_BG = (35, 30, 24)
    COLOR_TIP_BORDER = (180, 130, 80)
    
    def __init__(self, brand_name: str = 'استوديو العمارة', brand_handle: str = '@arch.tips'):
        self.brand_name = brand_name
        self.brand_handle = brand_handle
        
        self.font_tag = ImageFont.truetype(FONT_BOLD, size=26)
        self.font_brand = ImageFont.truetype(FONT_BOLD, size=30)
        self.font_hero_title = ImageFont.truetype(FONT_BOLD, size=58)
        self.font_slide_title = ImageFont.truetype(FONT_BOLD, size=46)
        self.font_body = ImageFont.truetype(FONT_REGULAR, size=32)
        self.font_bullet = ImageFont.truetype(FONT_REGULAR, size=30)
        self.font_tip = ImageFont.truetype(FONT_REGULAR, size=28)
        self.font_num = ImageFont.truetype(FONT_BOLD, size=26)

    def _prepare_background(self, bg_image_path: str = None) -> Image.Image:
        if bg_image_path and os.path.exists(bg_image_path):
            try:
                bg = Image.open(bg_image_path).convert('RGB')
                img_w, img_h = bg.size
                target_aspect = self.WIDTH / self.HEIGHT
                current_aspect = img_w / img_h
                if current_aspect > target_aspect:
                    new_w = int(img_h * target_aspect)
                    left = (img_w - new_w) // 2
                    bg = bg.crop((left, 0, left + new_w, img_h))
                else:
                    new_h = int(img_w / target_aspect)
                    top = (img_h - new_h) // 2
                    bg = bg.crop((0, top, img_w, top + new_h))
                return bg.resize((self.WIDTH, self.HEIGHT), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"⚠️ تعذر تحميل صورة الخلفية: {e}")
        return Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BG)

    def _draw_header_footer(self, draw: ImageDraw.ImageDraw, slide_num: int, total_slides: int, category: str):
        badge_text = prepare_arabic(f'• {category} •')
        draw.text((self.WIDTH - 100, 85), badge_text, font=self.font_tag, fill=self.COLOR_ACCENT, anchor='rt')
        
        counter_text = f'{slide_num:02d} / {total_slides:02d}'
        draw.text((100, 85), counter_text, font=self.font_num, fill=self.COLOR_TEXT_SECONDARY, anchor='lt')
        
        draw.line([(100, 140), (self.WIDTH - 100, 140)], fill=(255, 255, 255, 60), width=2)
        
        footer_brand = prepare_arabic(self.brand_name)
        draw.text((self.WIDTH - 100, self.HEIGHT - 90), footer_brand, font=self.font_brand, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
        
        draw.text((100, self.HEIGHT - 90), self.brand_handle, font=self.font_num, fill=self.COLOR_ACCENT, anchor='lt')
        draw.line([(100, self.HEIGHT - 130), (self.WIDTH - 100, self.HEIGHT - 130)], fill=(255, 255, 255, 60), width=2)

    def create_cover_slide(self, title: str, subtitle: str, category: str, total_slides: int = 4, bg_image_path: str = None) -> Image.Image:
        if bg_image_path and os.path.exists(bg_image_path):
            base_img = self._prepare_background(bg_image_path).convert('RGBA')
            overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            d_ol = ImageDraw.Draw(overlay)
            for y in range(self.HEIGHT):
                if y < 180:
                    a = int(160 - (y / 180.0) * 60)
                elif y < 580:
                    a = int(100 + ((y - 180) / 400.0) * 30)
                else:
                    prog = (y - 580) / (self.HEIGHT - 580)
                    a = int(130 + (prog ** 1.3) * 115)
                d_ol.line([(0, y), (self.WIDTH, y)], fill=(10, 12, 16, a))

            img = Image.alpha_composite(base_img, overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            self._draw_header_footer(draw, 1, total_slides, category)

            cy = 820
            title_lines = wrap_text(title, self.font_hero_title, self.WIDTH - 200, draw)
            for line in title_lines:
                draw.text((self.WIDTH // 2, cy), prepare_arabic(line), font=self.font_hero_title, fill=self.COLOR_TEXT_PRIMARY, anchor='mm')
                cy += 75
            draw.line([(self.WIDTH // 2 - 80, cy + 10), (self.WIDTH // 2 + 80, cy + 10)], fill=self.COLOR_ACCENT, width=5)
            cy += 45
            sub_lines = wrap_text(subtitle, self.font_body, self.WIDTH - 200, draw)
            for line in sub_lines:
                draw.text((self.WIDTH // 2, cy), prepare_arabic(line), font=self.font_body, fill=self.COLOR_TEXT_SECONDARY, anchor='mm')
                cy += 50
            swipe_text = prepare_arabic('اسحب لليسار لمعرفة التفاصيل >>')
            draw.text((self.WIDTH // 2, self.HEIGHT - 165), swipe_text, font=self.font_tag, fill=self.COLOR_ACCENT, anchor='mm')
            return img

        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BG)
        draw = ImageDraw.Draw(img)
        self._draw_header_footer(draw, 1, total_slides, category)
        
        margin = 100
        card_top = 220
        card_bottom = self.HEIGHT - 220
        draw.rounded_rectangle([(margin, card_top), (self.WIDTH - margin, card_bottom)], radius=24, fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)
        
        badge_rect = [(self.WIDTH - margin - 260, card_top + 60), (self.WIDTH - margin - 40, card_top + 115)]
        draw.rounded_rectangle(badge_rect, radius=12, fill=self.COLOR_ACCENT)
        badge_title = prepare_arabic('دليل هندسي موجز')
        badge_cx = (badge_rect[0][0] + badge_rect[1][0]) // 2
        badge_cy = (badge_rect[0][1] + badge_rect[1][1]) // 2
        draw.text((badge_cx, badge_cy), badge_title, font=self.font_tag, fill=self.COLOR_BG, anchor='mm')
        
        y_cursor = card_top + 170
        title_lines = wrap_text(title, self.font_hero_title, self.WIDTH - 2 * margin - 100, draw)
        for line in title_lines:
            prep_line = prepare_arabic(line)
            draw.text((self.WIDTH - margin - 50, y_cursor), prep_line, font=self.font_hero_title, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
            y_cursor += 85
            
        y_cursor += 25
        draw.line([(self.WIDTH - margin - 50, y_cursor), (self.WIDTH - margin - 200, y_cursor)], fill=self.COLOR_ACCENT, width=6)
        y_cursor += 45
        
        sub_lines = wrap_text(subtitle, self.font_body, self.WIDTH - 2 * margin - 100, draw)
        for line in sub_lines:
            prep_line = prepare_arabic(line)
            draw.text((self.WIDTH - margin - 50, y_cursor), prep_line, font=self.font_body, fill=self.COLOR_TEXT_SECONDARY, anchor='rt')
            y_cursor += 55
            
        swipe_text = prepare_arabic('اسحب لليسار لمعرفة التفاصيل >>')
        draw.text((self.WIDTH // 2, card_bottom - 70), swipe_text, font=self.font_tag, fill=self.COLOR_ACCENT, anchor='mm')
        
        return img

    def create_content_slide(self, slide_num: int, total_slides: int, category: str, 
                             headline: str, bullets: list[str], tip: str = None, bg_image_path: str = None) -> Image.Image:
        margin = 80
        card_top = 180
        card_bottom = self.HEIGHT - 170
        cx_pad = 50
        content_w = self.WIDTH - 2 * margin - 2 * cx_pad

        if bg_image_path and os.path.exists(bg_image_path):
            base_img = self._prepare_background(bg_image_path).convert('RGBA')
            overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            d_ol = ImageDraw.Draw(overlay)
            # Ambient dark scrim over villa
            d_ol.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(12, 14, 18, 175))
            # Glassmorphism central card
            d_ol.rounded_rectangle([(margin, card_top), (self.WIDTH - margin, card_bottom)], radius=24, 
                                   fill=(18, 22, 28, 220), outline=(212, 163, 115, 110), width=2)
            
            img = Image.alpha_composite(base_img, overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            self._draw_header_footer(draw, slide_num, total_slides, category)

            y_cursor = card_top + 60
            headline_lines = wrap_text(headline, self.font_slide_title, content_w, draw)
            for line in headline_lines:
                draw.text((self.WIDTH - margin - cx_pad, y_cursor), prepare_arabic(line), font=self.font_slide_title, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
                y_cursor += 65
            y_cursor += 15
            draw.line([(self.WIDTH - margin - cx_pad, y_cursor), (self.WIDTH - margin - cx_pad - 140, y_cursor)], fill=self.COLOR_ACCENT, width=4)
            y_cursor += 50

            for b_text in bullets:
                bullet_lines = wrap_text(b_text, self.font_bullet, content_w - 60, draw)
                bx = self.WIDTH - margin - cx_pad - 10
                by = y_cursor + 16
                draw.polygon([(bx, by-8), (bx+8, by), (bx, by+8), (bx-8, by)], fill=self.COLOR_ACCENT)
                for line in bullet_lines:
                    draw.text((self.WIDTH - margin - cx_pad - 35, y_cursor), prepare_arabic(line), font=self.font_bullet, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
                    y_cursor += 54
                y_cursor += 30

            return img

        # Fallback card mode
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BG)
        draw = ImageDraw.Draw(img)
        self._draw_header_footer(draw, slide_num, total_slides, category)
        
        margin = 100
        content_w = self.WIDTH - 2 * margin
        
        y_cursor = 210
        headline_lines = wrap_text(headline, self.font_slide_title, content_w, draw)
        for line in headline_lines:
            prep = prepare_arabic(line)
            draw.text((self.WIDTH - margin, y_cursor), prep, font=self.font_slide_title, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
            y_cursor += 70
            
        y_cursor += 15
        draw.line([(self.WIDTH - margin, y_cursor), (self.WIDTH - margin - 120, y_cursor)], fill=self.COLOR_ACCENT, width=4)
        y_cursor += 50
        
        for b_text in bullets:
            bullet_lines = wrap_text(b_text, self.font_bullet, content_w - 70, draw)
            draw.ellipse([(self.WIDTH - margin - 18, y_cursor + 14), (self.WIDTH - margin - 8, y_cursor + 24)], fill=self.COLOR_ACCENT)
            
            for line in bullet_lines:
                prep = prepare_arabic(line)
                draw.text((self.WIDTH - margin - 35, y_cursor), prep, font=self.font_bullet, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
                y_cursor += 52
            y_cursor += 25
                
        return img

    def create_cta_slide(self, slide_num: int, total_slides: int, category: str,
                         summary_points: list[str], cta_text: str = 'احفظ المنشور وشاركه مع زملائك المهندسين', bg_image_path: str = None) -> Image.Image:
        margin = 80
        card_top = 180
        cx_pad = 50
        content_w = self.WIDTH - 2 * margin - 2 * cx_pad

        if bg_image_path and os.path.exists(bg_image_path):
            base_img = self._prepare_background(bg_image_path).convert('RGBA')
            overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            d_ol = ImageDraw.Draw(overlay)
            d_ol.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(12, 14, 18, 175))
            d_ol.rounded_rectangle([(margin, card_top), (self.WIDTH - margin, card_top + 460)], radius=24, 
                                   fill=(18, 22, 28, 220), outline=(212, 163, 115, 110), width=2)
            
            img = Image.alpha_composite(base_img, overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            self._draw_header_footer(draw, slide_num, total_slides, category)

            cy_cta = card_top + 50
            cta_head = 'خلاصة واستنتاج معماري'
            draw.text((self.WIDTH - margin - cx_pad, cy_cta), prepare_arabic(cta_head), font=self.font_slide_title, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
            cy_cta += 65
            draw.line([(self.WIDTH - margin - cx_pad, cy_cta), (self.WIDTH - margin - cx_pad - 140, cy_cta)], fill=self.COLOR_ACCENT, width=4)
            cy_cta += 50

            for s in summary_points[:3]:
                s_lines = wrap_text(s, self.font_bullet, content_w - 60, draw)
                bx = self.WIDTH - margin - cx_pad - 10
                by = cy_cta + 16
                draw.polygon([(bx, by-8), (bx+8, by), (bx, by+8), (bx-8, by)], fill=self.COLOR_ACCENT)
                for l in s_lines:
                    draw.text((self.WIDTH - margin - cx_pad - 35, cy_cta), prepare_arabic(l), font=self.font_bullet, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
                    cy_cta += 52
                cy_cta += 20

            # Big Luxury CTA Button
            btn_top = card_top + 530
            draw.rounded_rectangle([(margin, btn_top), (self.WIDTH - margin, btn_top + 160)], radius=20, fill=self.COLOR_ACCENT)
            draw.text((self.WIDTH // 2, btn_top + 50), prepare_arabic(cta_text), font=self.font_slide_title, fill=(18, 20, 24), anchor='mm')
            draw.text((self.WIDTH // 2, btn_top + 110), f"{self.brand_handle}  |  {self.brand_name}", font=self.font_tag, fill=(18, 20, 24), anchor='mm')
            return img

        # Fallback card mode
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BG)
        draw = ImageDraw.Draw(img)
        self._draw_header_footer(draw, slide_num, total_slides, category)
        margin = 100
        content_w = self.WIDTH - 2 * margin
        
        y_cursor = 220
        title_prep = prepare_arabic('خلاصة واستنتاج معماري')
        draw.text((self.WIDTH - margin, y_cursor), title_prep, font=self.font_slide_title, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
        y_cursor += 70
        draw.line([(self.WIDTH - margin, y_cursor), (self.WIDTH - margin - 140, y_cursor)], fill=self.COLOR_ACCENT, width=4)
        y_cursor += 50
        
        card_h = 360
        draw.rounded_rectangle([(margin, y_cursor), (self.WIDTH - margin, y_cursor + card_h)], radius=20,
                               fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)
        
        card_y = y_cursor + 40
        for pt in summary_points[:3]:
            pt_lines = wrap_text(pt, self.font_bullet, content_w - 80, draw)
            draw.polygon([(self.WIDTH - margin - 35, card_y + 16), 
                          (self.WIDTH - margin - 25, card_y + 8), 
                          (self.WIDTH - margin - 15, card_y + 16), 
                          (self.WIDTH - margin - 25, card_y + 24)], fill=self.COLOR_ACCENT)
            
            for line in pt_lines:
                draw.text((self.WIDTH - margin - 55, card_y), prepare_arabic(line), font=self.font_bullet, fill=self.COLOR_TEXT_PRIMARY, anchor='rt')
                card_y += 50
            card_y += 18
            
        y_cursor += card_h + 80
        
        cta_box = [(margin, y_cursor), (self.WIDTH - margin, y_cursor + 170)]
        draw.rounded_rectangle(cta_box, radius=20, fill=self.COLOR_ACCENT)
        
        cta_p = prepare_arabic(cta_text)
        draw.text((self.WIDTH // 2, y_cursor + 55), cta_p, font=self.font_slide_title, fill=self.COLOR_BG, anchor='mm')
        
        handle_p = prepare_arabic(f'تابع {self.brand_handle} للمزيد من الأفكار المعمارية')
        draw.text((self.WIDTH // 2, y_cursor + 115), handle_p, font=self.font_tag, fill=self.COLOR_BG, anchor='mm')
        
        return img
