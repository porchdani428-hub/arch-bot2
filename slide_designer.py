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

def find_serif_font(bold: bool = False):
    font_name = 'timesbd.ttf' if bold else 'times.ttf'
    candidates = [
        f'C:/Windows/Fonts/{font_name}',
        'C:/Windows/Fonts/georgiab.ttf' if bold else 'C:/Windows/Fonts/georgia.ttf',
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', font_name),
        f'/usr/share/fonts/truetype/dejavu/{"DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"}',
        FONT_BOLD if bold else FONT_REGULAR
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return FONT_BOLD if bold else FONT_REGULAR

FONT_SERIF_BOLD = find_serif_font(True)
FONT_SERIF_REGULAR = find_serif_font(False)

def clean_emojis(text: str) -> str:
    if not text:
        return ''
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u26ff]'
        r'|[\u2700-\u27bf]'
        r'|[⭐⭕⌚⌛⏰⏳]'
        r'|[\u200d\ufe0f]', 
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    cleaned = cleaned.replace('✔', '').replace('✅', '').replace('💡', '').replace('⬅', '>>').replace('➡', '<<')
    return cleaned.strip()

# Pattern for preserving atomic units in mixed Arabic/English/French text:
# 1. Parenthesized or bracketed phrases with attached punctuation: (Plan de masse), (Rework):, [CTC]
# 2. Quoted phrases: 'Model-Based Design', "BIM Manager"
# 3. Consecutive Latin words with attached punctuation: Model-Based Design, Plan de masse
# 4. Standard words and symbols
ATOMIC_TOKEN_PATTERN = re.compile(
    r'\([^\)]+\)[^\s\w]*'
    r'|\[[^\]]+\][^\s\w]*'
    r'|\"[^\"]+\"[^\s\w]*|\'[^\']+\'[^\s\w]*'
    r'|[a-zA-Z0-9_#\-\+]+(?:\s+[a-zA-Z0-9_#\-\+]+)*[^\s\w]*'
    r'|[^\s]+'
)

def prepare_arabic(text: str) -> str:
    """Prepares mixed Arabic and Latin text for PIL rendering with strict RTL base direction."""
    if not text:
        return ''
    cleaned = clean_emojis(text)
    reshaped = arabic_reshaper.reshape(cleaned)
    # CRITICAL: Always enforce base_dir='R' so lines starting with Latin words
    # do not flip to LTR and reverse sentence grammatical order.
    return get_display(reshaped, base_dir='R')

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text intelligently preserving atomic English/French terms and parentheses unbroken."""
    cleaned = clean_emojis(text)
    tokens = ATOMIC_TOKEN_PATTERN.findall(cleaned)
    lines = []
    current_tokens = []
    
    for token in tokens:
        current_tokens.append(token)
        test_line = ' '.join(current_tokens)
        reshaped_test = prepare_arabic(test_line)
        bbox = draw.textbbox((0, 0), reshaped_test, font=font)
        line_w = bbox[2] - bbox[0]
        
        if line_w > max_width and len(current_tokens) > 1:
            current_tokens.pop()
            lines.append(' '.join(current_tokens))
            current_tokens = [token]
            
    if current_tokens:
        lines.append(' '.join(current_tokens))
        
    return lines

class ArchitecturalSlideDesigner:
    WIDTH = 1080
    HEIGHT = 1350
    
    # Theme: Luxury Archviz (Dark Mode)
    COLOR_BG = (18, 20, 24)
    COLOR_CARD = (28, 31, 38)
    COLOR_BORDER = (45, 50, 62)
    COLOR_ACCENT = (212, 163, 115)
    COLOR_TEXT_PRIMARY = (245, 245, 247)
    COLOR_TEXT_SECONDARY = (165, 170, 180)
    
    # Theme: Atelier Prestige (Warm Alabaster / Linen / Ivory / Gold / Espresso)
    COLOR_ATELIER_DARK = (44, 30, 22)         # Deep espresso
    COLOR_ATELIER_SEPIA = (74, 53, 40)        # Warm sepia
    COLOR_ATELIER_GOLD = (197, 160, 89)       # Antique gold
    COLOR_ATELIER_CARD = (253, 250, 245, 240) # Soft alabaster parchment
    COLOR_ATELIER_PILL = (240, 232, 220, 245) # Light pill fill
    COLOR_ATELIER_LINE = (215, 195, 170)      # Subtle divider
    COLOR_ATELIER_DARK_PILL = (62, 39, 24)    # Deep brown takeaway pill
    
    def __init__(self, brand_name: str = 'MK ARCHVIZ', brand_handle: str = '@MK.ARCHVIZ'):
        self.brand_name = brand_name
        self.brand_handle = brand_handle
        
        # Standard Fonts
        self.font_tag = ImageFont.truetype(FONT_BOLD, size=26)
        self.font_brand = ImageFont.truetype(FONT_BOLD, size=30)
        self.font_hero_title = ImageFont.truetype(FONT_BOLD, size=58)
        self.font_slide_title = ImageFont.truetype(FONT_BOLD, size=46)
        self.font_body = ImageFont.truetype(FONT_REGULAR, size=32)
        self.font_bullet = ImageFont.truetype(FONT_REGULAR, size=30)
        self.font_num = ImageFont.truetype(FONT_BOLD, size=26)
        
        # Atelier Prestige Roman Serif Fonts
        self.font_serif_num = ImageFont.truetype(FONT_SERIF_BOLD, size=60)
        self.font_serif_hero = ImageFont.truetype(FONT_SERIF_BOLD, size=66)
        self.font_serif_sub = ImageFont.truetype(FONT_SERIF_REGULAR, size=28)
        self.font_serif_badge = ImageFont.truetype(FONT_SERIF_BOLD, size=28)
        self.font_serif_footer = ImageFont.truetype(FONT_SERIF_BOLD, size=24)
        
        # Ensure branding seal exists
        self.seal_image = self._get_or_create_studio_seal()

    def _get_or_create_studio_seal(self) -> Image.Image:
        """Returns or creates the circular luxury studio monogram seal."""
        seal_path = os.path.join(os.path.dirname(__file__), 'assets', 'branding', 'mk_archviz_seal.png')
        if os.path.exists(seal_path):
            try:
                return Image.open(seal_path).convert('RGBA')
            except Exception:
                pass
        
        size = 180
        seal = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(seal)
        gold = self.COLOR_ATELIER_GOLD
        dark = self.COLOR_ATELIER_DARK
        bg_seal = (246, 241, 235, 230)
        
        d.ellipse([(4, 4), (size-4, size-4)], fill=bg_seal, outline=gold, width=2)
        d.ellipse([(10, 10), (size-10, size-10)], outline=gold, width=1)
        
        d.text((size//2, size//2 - 6), 'MK', font=self.font_serif_hero, fill=gold, anchor='mm')
        d.text((size//2, 28), self.brand_name, font=self.font_serif_footer, fill=dark, anchor='mm')
        d.text((size//2, size - 28), 'STUDIO & ATELIER', font=self.font_serif_footer, fill=dark, anchor='mm')
        return seal

    def _prepare_background(self, bg_image_path: str = None, default_atelier: bool = True) -> Image.Image:
        """Loads and crops background, falling back to warm atelier canvas or dark mode."""
        candidate = bg_image_path
        if not candidate or not os.path.exists(candidate):
            atelier_default = os.path.join(os.path.dirname(__file__), 'assets', 'backgrounds', 'warm_atelier_01.jpg')
            if default_atelier and os.path.exists(atelier_default):
                candidate = atelier_default

        if candidate and os.path.exists(candidate):
            try:
                bg = Image.open(candidate).convert('RGB')
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

    def _draw_atelier_decorations(self, overlay: Image.Image, slide_num: int):
        """Draws classical corner borders, slide number, and studio seal."""
        d = ImageDraw.Draw(overlay)
        margin = 40
        # Double gold border
        d.rectangle([(margin, margin), (self.WIDTH - margin, self.HEIGHT - margin)], outline=self.COLOR_ATELIER_GOLD, width=2)
        d.rectangle([(margin+8, margin+8), (self.WIDTH - margin - 8, self.HEIGHT - margin - 8)], outline=(197, 160, 89, 90), width=1)
        
        # Corner gold corner diamonds
        for cx, cy in [(margin+4, margin+4), (self.WIDTH-margin-4, margin+4), (margin+4, self.HEIGHT-margin-4), (self.WIDTH-margin-4, self.HEIGHT-margin-4)]:
            d.polygon([(cx, cy-4), (cx+4, cy), (cx, cy+4), (cx-4, cy)], fill=self.COLOR_ATELIER_GOLD)

        # Slide number top-left (Roman Serif)
        if slide_num > 1:
            num_str = f'{slide_num:02d}'
            d.text((100, 100), num_str, font=self.font_serif_num, fill=self.COLOR_ATELIER_DARK)
            d.line([(100, 175), (170, 175)], fill=self.COLOR_ATELIER_GOLD, width=3)

        # Studio Seal top-right
        seal_scaled = self.seal_image.resize((130, 130), Image.Resampling.LANCZOS)
        overlay.paste(seal_scaled, (self.WIDTH - margin - 130 - 20, margin + 20), seal_scaled)

    # =========================================================================
    # ATELIER PRESTIGE THEME (ATELIER NOVE AESTHETIC)
    # =========================================================================

    def create_atelier_cover(self, super_title: str = "GUIDE DE L'ÉTUDIANT EN",
                              hero_title: str = "ARCHITECTURE",
                              hook_tag: str = "طالب Architecture",
                              main_title: str = "هذا الـ Guide راح يكون مرجعك من أول سنة حتى التخرج",
                              subtitle: str = "كل ما يحتاجه طالب ومعماري الجزائر في مكان واحد",
                              footer_tags: str = "Plans • Coupes • Façades • Échelles • Logiciels • Conseils",
                              bg_image_path: str = None) -> Image.Image:
        """Creates the luxury editorial cover slide matching Atelier Nove aesthetics."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        
        # Soft warm parchment ambient wash
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 155))
        self._draw_atelier_decorations(overlay, slide_num=1)
        
        # 1. Super-title in Roman Serif
        s_title = super_title or "GUIDE DE L'ÉTUDIANT EN"
        d.text((self.WIDTH//2, 190), f"— {s_title} —", font=self.font_serif_sub, fill=self.COLOR_ATELIER_SEPIA, anchor='mm')
        
        # 2. Hero Roman Serif ARCHITECTURE
        h_title = hero_title or "ARCHITECTURE"
        d.text((self.WIDTH//2, 260), h_title, font=self.font_serif_hero, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        
        # Gold accent divider
        d.line([(self.WIDTH//2 - 120, 315), (self.WIDTH//2 + 120, 315)], fill=self.COLOR_ATELIER_GOLD, width=2)
        d.polygon([(self.WIDTH//2, 310), (self.WIDTH//2 + 8, 315), (self.WIDTH//2, 320), (self.WIDTH//2 - 8, 315)], fill=self.COLOR_ATELIER_GOLD)
        
        # 3. Hook Tag Pill
        if hook_tag:
            hook_text = prepare_arabic(hook_tag)
            hb = d.textbbox((0, 0), hook_text, font=self.font_slide_title)
            hook_w = max(420, min(820, (hb[2] - hb[0]) + 80))
            hook_h = 70
            hx = (self.WIDTH - hook_w) // 2
            hy = 360
            d.rounded_rectangle([(hx, hy), (hx + hook_w, hy + hook_h)], radius=35, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_GOLD, width=2)
            d.text((self.WIDTH//2, hy + hook_h//2), hook_text, font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
            
        # 4. Main Title
        y_cursor = 490
        title_lines = wrap_text(main_title, self.font_slide_title, 760, d)
        for line in title_lines:
            d.text((self.WIDTH//2, y_cursor), prepare_arabic(line), font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
            y_cursor += 65
            
        # 5. Framed Card for Subtitle
        if subtitle:
            card_w = 640
            card_h = 130
            cx = (self.WIDTH - card_w) // 2
            cy = max(y_cursor + 25, 660)
            d.rounded_rectangle([(cx, cy), (cx + card_w, cy + card_h)], radius=20, fill=(244, 237, 226, 235), outline=self.COLOR_ATELIER_GOLD, width=2)
            sub_lines = wrap_text(subtitle, self.font_body, card_w - 60, d)
            sy = cy + (card_h - len(sub_lines)*46)//2 + 20
            for s_line in sub_lines:
                d.text((self.WIDTH//2, sy), prepare_arabic(s_line), font=self.font_body, fill=self.COLOR_ATELIER_DARK, anchor='mm')
                sy += 46

        # 6. Footer tags
        f_tags = footer_tags or "Plans • Coupes • Façades • Échelles • Logiciels • Conseils"
        d.text((self.WIDTH//2, self.HEIGHT - 80), f_tags, font=self.font_serif_footer, fill=self.COLOR_ATELIER_SEPIA, anchor='mm')
        
        return Image.alpha_composite(base_img, overlay).convert('RGB')

    def _draw_row_icon(self, d: ImageDraw.Draw, icon_type: str, ix: int, iy: int):
        """Draws clean architectural line-art icons for definition tables."""
        it = icon_type.lower()
        color = self.COLOR_ATELIER_DARK
        gold = self.COLOR_ATELIER_GOLD
        
        if any(k in it for k in ['vhs', 'heure', 'temps', 'clock', 'time']):
            # Clock
            d.ellipse([(ix-18, iy-18), (ix+18, iy+18)], outline=color, width=2)
            d.line([(ix, iy), (ix, iy-9)], fill=color, width=2)
            d.line([(ix, iy), (ix+7, iy)], fill=color, width=2)
            d.ellipse([(ix-2, iy-2), (ix+2, iy+2)], fill=color)
        elif any(k in it for k in ['cours', 'lecture', 'prof']):
            # Presentation easel
            d.rounded_rectangle([(ix-16, iy-15), (ix+16, iy+4)], radius=2, outline=color, width=2)
            d.line([(ix-10, iy+4), (ix-14, iy+16)], fill=color, width=2)
            d.line([(ix+10, iy+4), (ix+14, iy+16)], fill=color, width=2)
            d.line([(ix, iy+4), (ix, iy+16)], fill=color, width=2)
            d.line([(ix-10, iy-5), (ix+4, iy-5)], fill=gold, width=2)
        elif any(k in it for k in ['td', 'atelier', 'work', 'projet']):
            # Set square triangle
            d.polygon([(ix-14, iy+12), (ix+14, iy+12), (ix-14, iy-14)], outline=color, width=2)
            d.polygon([(ix-8, iy+6), (ix+4, iy+6), (ix-8, iy-4)], outline=gold, width=1)
        elif any(k in it for k in ['tp', 'lab', 'pratique']):
            # Laboratory flask
            d.line([(ix-4, iy-14), (ix-4, iy-6)], fill=color, width=2)
            d.line([(ix+4, iy-14), (ix+4, iy-6)], fill=color, width=2)
            d.line([(ix-4, iy-6), (ix-14, iy+14)], fill=color, width=2)
            d.line([(ix+4, iy-6), (ix+14, iy+14)], fill=color, width=2)
            d.line([(ix-14, iy+14), (ix+14, iy+14)], fill=color, width=2)
            d.ellipse([(ix-3, iy+7), (ix-1, iy+9)], fill=gold)
            d.ellipse([(ix+2, iy+4), (ix+4, iy+6)], fill=gold)
        elif any(k in it for k in ['cc', 'eval', 'rendu']):
            # Evaluation checklist
            d.rounded_rectangle([(ix-12, iy-12), (ix+12, iy+14)], radius=2, outline=color, width=2)
            d.rounded_rectangle([(ix-6, iy-16), (ix+6, iy-10)], radius=2, fill=gold, outline=color, width=1)
            d.line([(ix-7, iy-4), (ix+7, iy-4)], fill=color, width=2)
            d.line([(ix-7, iy+2), (ix+7, iy+2)], fill=color, width=2)
            d.line([(ix-7, iy+8), (ix+3, iy+8)], fill=color, width=2)
        elif any(k in it for k in ['examen', 'exam', 'test']):
            # Exam sheet with folded corner
            d.polygon([(ix-12, iy-14), (ix+4, iy-14), (ix+12, iy-6), (ix+12, iy+14), (ix-12, iy+14)], outline=color, width=2)
            d.polygon([(ix+4, iy-14), (ix+4, iy-6), (ix+12, iy-6)], fill=gold, outline=color, width=1)
            d.line([(ix-6, iy), (ix+6, iy)], fill=color, width=2)
            d.line([(ix-6, iy+6), (ix+2, iy+6)], fill=color, width=2)
        elif any(k in it for k in ['coef', 'stat', 'bar', 'grade']):
            # Rising bar chart
            d.line([(ix-14, iy+14), (ix+14, iy+14)], fill=color, width=2)
            d.line([(ix-14, iy+14), (ix-14, iy-14)], fill=color, width=2)
            d.rectangle([(ix-10, iy+4), (ix-6, iy+12)], fill=gold)
            d.rectangle([(ix-4, iy-2), (ix, iy+12)], fill=color)
            d.rectangle([(ix+2, iy-8), (ix+6, iy+12)], fill=gold)
            d.line([(ix-8, iy), (ix+4, iy-12)], fill=color, width=2)
        else:
            # Diamond flourish
            d.polygon([(ix, iy-12), (ix+12, iy), (ix, iy+12), (ix-12, iy)], outline=gold, width=2)
            d.ellipse([(ix-3, iy-3), (ix+3, iy+3)], fill=color)

    def create_atelier_definition_table(self, slide_num: int, total_slides: int,
                                        headline: str, items: list,
                                        bg_image_path: str = None) -> Image.Image:
        """Slide Type: Terminology definition table (Icons -> Badges -> Arrows -> Explanations)."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 125))
        self._draw_atelier_decorations(overlay, slide_num)
        
        # Headline with soft background banner
        head_lines = wrap_text(headline, self.font_slide_title, 740, d)
        y_head = 230
        for l in head_lines:
            d.text((self.WIDTH//2, y_head), prepare_arabic(l), font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
            y_head += 60
        d.polygon([(self.WIDTH//2, y_head + 5), (self.WIDTH//2 + 8, y_head + 13), (self.WIDTH//2, y_head + 21), (self.WIDTH//2 - 8, y_head + 13)], fill=self.COLOR_ATELIER_GOLD)
        
        # Central Table Card
        card_left = 100
        card_right = self.WIDTH - 100
        card_top = max(y_head + 40, 360)
        card_bottom = self.HEIGHT - 160
        
        d.rounded_rectangle([(card_left, card_top), (card_right, card_bottom)], radius=24, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_GOLD, width=2)
        
        safe_items = items[:7] if items else []
        if safe_items:
            row_y = card_top + 30
            row_h = (card_bottom - card_top - 50) // len(safe_items)
            
            for item in safe_items:
                term = str(item.get("term", "") if isinstance(item, dict) else item[0]).strip()
                exp = str(item.get("explanation", "") if isinstance(item, dict) else item[1]).strip()
                
                # Keep acronym only for the badge pill if parentheses exist
                clean_term = term
                if "(" in term:
                    clean_term = term.split("(")[0].strip()
                
                # Dynamic pill sizing
                tb = d.textbbox((0, 0), clean_term, font=self.font_serif_badge)
                tw = tb[2] - tb[0]
                badge_font = self.font_serif_badge
                if tw > 170:
                    badge_font = self.font_tag
                    tb = d.textbbox((0, 0), clean_term, font=badge_font)
                    tw = tb[2] - tb[0]
                    
                pill_w = max(150, min(230, tw + 34))
                pill_h = min(56, row_h - 14)
                
                center_y = row_y + row_h // 2
                
                # 1. Row Icon
                ix = card_left + 45
                self._draw_row_icon(d, clean_term, ix, center_y)
                
                # 2. Term Pill
                px = card_left + 85
                py = center_y - pill_h // 2
                d.rounded_rectangle([(px, py), (px + pill_w, py + pill_h)], radius=12, fill=self.COLOR_ATELIER_PILL)
                d.text((px + pill_w//2, center_y), clean_term, font=badge_font, fill=self.COLOR_ATELIER_DARK, anchor='mm')
                
                # 3. Arrow
                arrow_x = px + pill_w + 24
                d.text((arrow_x, center_y - 2), '→', font=self.font_tag, fill=self.COLOR_ATELIER_SEPIA, anchor='mm')
                
                # 4. Arabic explanation (multi-line safe)
                max_exp_w = (card_right - 35) - (arrow_x + 25)
                exp_lines = wrap_text(exp, self.font_bullet, max_exp_w, d)
                
                if len(exp_lines) == 1:
                    d.text((card_right - 35, center_y), prepare_arabic(exp_lines[0]), font=self.font_bullet, fill=self.COLOR_ATELIER_DARK, anchor='rm')
                elif len(exp_lines) >= 2:
                    d.text((card_right - 35, center_y - 15), prepare_arabic(exp_lines[0]), font=self.font_bullet, fill=self.COLOR_ATELIER_DARK, anchor='rm')
                    d.text((card_right - 35, center_y + 18), prepare_arabic(exp_lines[1]), font=self.font_bullet, fill=self.COLOR_ATELIER_DARK, anchor='rm')
                
                # Divider line
                if item != safe_items[-1]:
                    d.line([(card_left + 30, row_y + row_h), (card_right - 30, row_y + row_h)], fill=(225, 215, 200, 180), width=1)
                row_y += row_h

        return Image.alpha_composite(base_img, overlay).convert('RGB')

    def _draw_pediment_icon(self, d: ImageDraw.Draw, cx: int, cy: int):
        """Draws classical architectural temple pediment icon."""
        gold = self.COLOR_ATELIER_GOLD
        d.polygon([(cx, cy-18), (cx-26, cy-6), (cx+26, cy-6)], outline=gold, width=2)
        d.line([(cx-28, cy-5), (cx+28, cy-5)], fill=gold, width=2)
        for col_x in [cx-18, cx-6, cx+6, cx+18]:
            d.line([(col_x, cy-3), (col_x, cy+14)], fill=gold, width=2)
        d.line([(cx-28, cy+15), (cx+28, cy+15)], fill=gold, width=2)
        d.line([(cx-30, cy+18), (cx+30, cy+18)], fill=gold, width=2)

    def create_atelier_hero_spotlight(self, slide_num: int, total_slides: int,
                                      headline: str, hero_title: str,
                                      coef_text: str, stats: list,
                                      takeaway: str = None,
                                      bg_image_path: str = None) -> Image.Image:
        """Slide Type: Hero Spotlight (Focal subject + metric rows + bottom takeaway pill)."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 125))
        self._draw_atelier_decorations(overlay, slide_num)
        
        # Classical Temple Pediment Flourish
        self._draw_pediment_icon(d, self.WIDTH//2, 175)
        
        # Section Title
        head_lines = wrap_text(headline, self.font_slide_title, 720, d)
        y_head = 230
        for hl in head_lines:
            d.text((self.WIDTH//2, y_head), prepare_arabic(hl), font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
            y_head += 55
        
        # Big Hero Subject Framed Box with Roman Serif
        box_w = 780
        box_h = 135
        bx = (self.WIDTH - box_w) // 2
        by = max(y_head + 25, 340)
        d.rounded_rectangle([(bx, by), (bx + box_w, by + box_h)], radius=16, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_GOLD, width=2)
        
        h_title = hero_title or "ATELIER DE PROJET"
        d.text((self.WIDTH//2, by + 48), h_title, font=self.font_serif_hero, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        c_text = coef_text or "— COEF. 4 —"
        d.text((self.WIDTH//2, by + 98), c_text, font=self.font_serif_badge, fill=self.COLOR_ATELIER_GOLD, anchor='mm')
        
        # Stats Card
        card_w = 780
        card_h = 320
        cx = (self.WIDTH - card_w) // 2
        cy = by + box_h + 30
        d.rounded_rectangle([(cx, cy), (cx + card_w, cy + card_h)], radius=20, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_LINE, width=1)
        
        safe_stats = stats[:3] if stats else []
        if safe_stats:
            sy = cy + 15
            sh = (card_h - 30) // len(safe_stats)
            for s in safe_stats:
                val = s.get("value", "") if isinstance(s, dict) else str(s[0])
                center_row_y = sy + sh//2
                
                # Dynamic Icon (Clock / Calendar / Checkmark)
                ix = cx + 55
                val_l = val.lower()
                d.ellipse([(ix-20, center_row_y-20), (ix+20, center_row_y+20)], fill=(244, 237, 226), outline=self.COLOR_ATELIER_GOLD, width=1)
                
                if "ساعة" in val or "heure" in val_l or "temps" in val_l:
                    # Clock
                    d.ellipse([(ix-12, center_row_y-12), (ix+12, center_row_y+12)], outline=self.COLOR_ATELIER_DARK, width=2)
                    d.line([(ix, center_row_y), (ix, center_row_y-6)], fill=self.COLOR_ATELIER_DARK, width=2)
                    d.line([(ix, center_row_y), (ix+5, center_row_y)], fill=self.COLOR_ATELIER_DARK, width=2)
                elif "أسبوع" in val or "semaine" in val_l or "cours" in val_l:
                    # Calendar
                    d.rectangle([(ix-10, center_row_y-8), (ix+10, center_row_y+10)], outline=self.COLOR_ATELIER_DARK, width=2)
                    d.line([(ix-10, center_row_y-3), (ix+10, center_row_y-3)], fill=self.COLOR_ATELIER_GOLD, width=1)
                    d.line([(ix-5, center_row_y-11), (ix-5, center_row_y-8)], fill=self.COLOR_ATELIER_DARK, width=2)
                    d.line([(ix+5, center_row_y-11), (ix+5, center_row_y-8)], fill=self.COLOR_ATELIER_DARK, width=2)
                else:
                    # Checkmark
                    d.line([(ix-7, center_row_y), (ix-2, center_row_y+5)], fill=self.COLOR_ATELIER_GOLD, width=2)
                    d.line([(ix-2, center_row_y+5), (ix+7, center_row_y-5)], fill=self.COLOR_ATELIER_GOLD, width=2)
                
                # Vertical divider
                d.line([(cx + 105, center_row_y - 22), (cx + 105, center_row_y + 22)], fill=(220, 205, 185), width=1)
                
                # Value text
                d.text((cx + card_w - 45, center_row_y), prepare_arabic(val), font=self.font_bullet, fill=self.COLOR_ATELIER_DARK, anchor='rm')
                
                if s != safe_stats[-1]:
                    d.line([(cx + 35, sy + sh), (cx + card_w - 35, sy + sh)], fill=(230, 220, 205, 160), width=1)
                sy += sh

        # Bottom Takeaway Pill
        if takeaway:
            pill_w = 740
            pill_h = 75
            px = (self.WIDTH - pill_w) // 2
            py = cy + card_h + 30
            d.rounded_rectangle([(px, py), (px + pill_w, py + pill_h)], radius=20, fill=self.COLOR_ATELIER_DARK_PILL)
            d.text((self.WIDTH//2, py + pill_h//2), prepare_arabic(takeaway), font=self.font_body, fill=(255, 245, 230), anchor='mm')
            
        return Image.alpha_composite(base_img, overlay).convert('RGB')

    def create_atelier_cards_grid(self, slide_num: int, total_slides: int,
                                  headline: str, cards: list,
                                  bottom_quote: str = None,
                                  bg_image_path: str = None) -> Image.Image:
        """Slide Type: Cards grid (2-4 distinct modules or items)."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 125))
        self._draw_atelier_decorations(overlay, slide_num)
        
        # Headline
        d.text((self.WIDTH//2, 250), prepare_arabic(headline), font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        d.polygon([(self.WIDTH//2, 295), (self.WIDTH//2 + 8, 303), (self.WIDTH//2, 311), (self.WIDTH//2 - 8, 303)], fill=self.COLOR_ATELIER_GOLD)
        
        safe_cards = cards[:4] if cards else []
        c_w = 780
        total_h = 560
        cy = 340
        card_h = (total_h - (len(safe_cards)-1)*20) // max(len(safe_cards), 1)
        
        for c in safe_cards:
            title = c.get("title", "") if isinstance(c, dict) else str(c)
            desc = c.get("desc", "") if isinstance(c, dict) else ""
            
            cx = (self.WIDTH - c_w) // 2
            d.rounded_rectangle([(cx, cy), (cx + c_w, cy + card_h)], radius=18, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_LINE, width=1)
            
            # Circular icon placeholder
            ix = cx + 55
            iy = cy + card_h//2
            d.ellipse([(ix-22, iy-22), (ix+22, iy+22)], fill=(242, 235, 224), outline=self.COLOR_ATELIER_GOLD, width=1)
            d.polygon([(ix, iy-8), (ix+8, iy), (ix, iy+8), (ix-8, iy)], fill=self.COLOR_ATELIER_GOLD)
            
            # Title & Desc
            if desc:
                d.text((cx + 105, cy + card_h//2 - 16), title, font=self.font_serif_badge, fill=self.COLOR_ATELIER_DARK, anchor='lm')
                d.text((cx + c_w - 40, cy + card_h//2 + 16), prepare_arabic(desc), font=self.font_tag, fill=self.COLOR_ATELIER_SEPIA, anchor='rm')
            else:
                d.text((cx + 105, cy + card_h//2), title, font=self.font_serif_badge, fill=self.COLOR_ATELIER_DARK, anchor='lm')
            cy += card_h + 20

        # Bottom quote pill
        if bottom_quote:
            py = cy + 20
            q_text = prepare_arabic(bottom_quote)
            qb = d.textbbox((0, 0), q_text, font=self.font_body)
            qw = qb[2] - qb[0]
            pill_w = min(900, max(520, qw + 60))
            pill_h = 68
            px = (self.WIDTH - pill_w) // 2
            d.rounded_rectangle([(px, py), (px + pill_w, py + pill_h)], radius=18, fill=(238, 228, 215, 235), outline=self.COLOR_ATELIER_GOLD, width=1)
            q_font = self.font_body if qw <= 840 else self.font_tag
            d.text((self.WIDTH//2, py + pill_h//2), q_text, font=q_font, fill=self.COLOR_ATELIER_DARK, anchor='mm')

        return Image.alpha_composite(base_img, overlay).convert('RGB')

    def create_atelier_content_slide(self, slide_num: int, total_slides: int,
                                     headline: str, bullets: list,
                                     takeaway: str = None,
                                     bg_image_path: str = None) -> Image.Image:
        """Standard bullet content slide rendered in warm Atelier Prestige style."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 125))
        self._draw_atelier_decorations(overlay, slide_num)
        
        # Headline
        d.text((self.WIDTH//2, 250), prepare_arabic(headline), font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        d.polygon([(self.WIDTH//2, 295), (self.WIDTH//2 + 8, 303), (self.WIDTH//2, 311), (self.WIDTH//2 - 8, 303)], fill=self.COLOR_ATELIER_GOLD)
        
        # Central card for bullets
        card_w = 820
        card_h = 580
        cx = (self.WIDTH - card_w) // 2
        cy = 340
        d.rounded_rectangle([(cx, cy), (cx + card_w, cy + card_h)], radius=24, fill=self.COLOR_ATELIER_CARD, outline=self.COLOR_ATELIER_GOLD, width=2)
        
        by_cursor = cy + 50
        content_w = card_w - 90
        
        for b_text in bullets[:4]:
            b_lines = wrap_text(b_text, self.font_bullet, content_w - 50, d)
            # Gold diamond bullet
            bx = cx + card_w - 40
            by = by_cursor + 16
            d.polygon([(bx, by-7), (bx+7, by), (bx, by+7), (bx-7, by)], fill=self.COLOR_ATELIER_GOLD)
            
            for line in b_lines:
                d.text((bx - 25, by_cursor), prepare_arabic(line), font=self.font_bullet, fill=self.COLOR_ATELIER_DARK, anchor='rt')
                by_cursor += 50
            by_cursor += 24

        # Bottom Takeaway Pill
        if takeaway:
            pill_w = 720
            pill_h = 70
            px = (self.WIDTH - pill_w) // 2
            py = cy + card_h + 35
            d.rounded_rectangle([(px, py), (px + pill_w, py + pill_h)], radius=18, fill=self.COLOR_ATELIER_DARK_PILL)
            d.text((self.WIDTH//2, py + pill_h//2), prepare_arabic(takeaway), font=self.font_tag, fill=(255, 245, 230), anchor='mm')

        return Image.alpha_composite(base_img, overlay).convert('RGB')

    def create_atelier_cta_slide(self, slide_num: int, total_slides: int,
                                 main_question: str = "درك فهمتي البرنامج تاعك أكثر؟",
                                 cta_badge: str = "Sauvegarde le post 📌",
                                 cta_quote: str = "وابعثيه لصديقتك في الأتيلييه لي راهي ضايعة مع البرنامج!",
                                 bg_image_path: str = None) -> Image.Image:
        """Viral save & share CTA slide in Atelier Prestige aesthetic."""
        base_img = self._prepare_background(bg_image_path, default_atelier=True).convert('RGBA')
        overlay = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=(248, 243, 236, 125))
        self._draw_atelier_decorations(overlay, slide_num)
        
        # Question Title
        q = main_question or "درك فهمت البرنامج تاعك أكثر؟"
        d.text((self.WIDTH//2, 320), prepare_arabic(q), font=self.font_hero_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        d.polygon([(self.WIDTH//2, 375), (self.WIDTH//2 + 8, 383), (self.WIDTH//2, 391), (self.WIDTH//2 - 8, 383)], fill=self.COLOR_ATELIER_GOLD)
        
        # Parchment Callout Card
        card_w = 760
        card_h = 320
        cx = (self.WIDTH - card_w) // 2
        cy = 450
        d.rounded_rectangle([(cx, cy), (cx + card_w, cy + card_h)], radius=24, fill=(244, 236, 224, 235), outline=self.COLOR_ATELIER_GOLD, width=2)
        
        badge = clean_emojis(cta_badge or "Sauvegarde le post")
        tb = d.textbbox((0, 0), badge, font=self.font_slide_title)
        bw = tb[2] - tb[0]
        badge_cx = self.WIDTH//2 - 15
        d.text((badge_cx, cy + 80), badge, font=self.font_slide_title, fill=self.COLOR_ATELIER_DARK, anchor='mm')
        
        # Elegant pushpin illustration
        pin_x = badge_cx + bw//2 + 25
        pin_y = cy + 78
        d.ellipse([(pin_x-7, pin_y-14), (pin_x+7, pin_y)], fill=(190, 55, 45))
        d.ellipse([(pin_x-9, pin_y-3), (pin_x+9, pin_y+3)], fill=(190, 55, 45))
        d.line([(pin_x, pin_y+3), (pin_x-3, pin_y+13)], fill=(150, 150, 150), width=2)
        
        quote = cta_quote or "وابعثو لصحابك في الأتيلييه لي راهم ضايعين مع البرنامج!"
        q_lines = wrap_text(quote, self.font_body, card_w - 80, d)
        qy = cy + 180
        for ql in q_lines:
            d.text((self.WIDTH//2, qy), prepare_arabic(ql), font=self.font_body, fill=self.COLOR_ATELIER_SEPIA, anchor='mm')
            qy += 52
            
        # Studio Branding in Footer
        d.text((self.WIDTH//2, self.HEIGHT - 100), f"{self.brand_handle}  |  STUDIO & ATELIER", font=self.font_serif_badge, fill=self.COLOR_ATELIER_GOLD, anchor='mm')
        
        return Image.alpha_composite(base_img, overlay).convert('RGB')

    # =========================================================================
    # BACKWARD COMPATIBLE & LUXURY DARK SLIDE METHODS
    # =========================================================================

    def create_cover_slide(self, title: str, subtitle: str, category: str, total_slides: int, bg_image_path: str = None) -> Image.Image:
        """Unified cover slide dispatcher."""
        return self.create_atelier_cover(
            super_title="GUIDE DE L'ÉTUDIANT EN",
            hero_title="ARCHITECTURE",
            hook_tag=category,
            main_title=title,
            subtitle=subtitle,
            bg_image_path=bg_image_path
        )

    def create_content_slide(self, slide_num: int, total_slides: int, category: str, 
                             headline: str, bullets: list, tip: str = None, bg_image_path: str = None) -> Image.Image:
        """Unified content slide dispatcher."""
        return self.create_atelier_content_slide(
            slide_num=slide_num,
            total_slides=total_slides,
            headline=headline,
            bullets=bullets,
            takeaway=tip,
            bg_image_path=bg_image_path
        )

    def create_cta_slide(self, slide_num: int, total_slides: int, category: str,
                         summary_points: list, cta_text: str, bg_image_path: str = None) -> Image.Image:
        """Unified CTA slide dispatcher."""
        return self.create_atelier_cta_slide(
            slide_num=slide_num,
            total_slides=total_slides,
            main_question="درك فهمت البرنامج تاعك أكثر؟",
            cta_badge="Sauvegarde le post 📌",
            cta_quote=cta_text,
            bg_image_path=bg_image_path
        )
