import os
from PIL import Image, ImageDraw, ImageFont

def build_infographic():
    base = 'Критик/texture_generator'
    os.makedirs(os.path.join(base, 'references'), exist_ok=True)
    w, h = 1400, 780
    img = Image.new('RGB', (w, h), (18, 20, 26))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype('arialbd.ttf', 30)
        font_subtitle = ImageFont.truetype('arial.ttf', 17)
        font_col_header = ImageFont.truetype('arialbd.ttf', 20)
        font_body = ImageFont.truetype('arial.ttf', 15)
        font_badge = ImageFont.truetype('arialbd.ttf', 15)
    except Exception:
        font_title = font_subtitle = font_col_header = font_body = font_badge = ImageFont.load_default()

    # Header
    draw.rectangle([(0, 0), (w, 90)], fill=(28, 32, 42))
    draw.text((40, 16), 'CRITIQUE & METHODOLOGY: PROCEDURAL CODE vs. REAL AAA PIXEL ART', fill=(245, 245, 250), font=font_title)
    draw.text((40, 56), 'Почему скрипты на Python рисуют детский рисунок и как устроен профессиональный пайплайн индустрии', fill=(160, 175, 200), font=font_subtitle)

    # 3 Columns
    cols = [
        {
            'title': '1. 2D Алгоритмический код',
            'badge': 'FAIL: ДЕТСКИЙ РИСУНОК (MS PAINT)',
            'badge_bg': (180, 45, 45),
            'img_p': os.path.join(base, 'results/method2_algorithmic_2d/m2_01_juggernaut_x4.png'),
            'scale_tag': 'Разрешение 48x48 (x4 zoom)',
            'bullets': [
                '• Примитивы: прямоугольники вместо ног, круги для плеч',
                '• Нулевая анатомия: нет суставов, изгиба кирасы и бедер',
                '• Одиночные линии 1px: дают визуальный шум и лесенки',
                '• Плоская заливка: нет объема, металл плоский как картон',
                '• Деревянная поза оловянного солдатика без веса'
            ]
        },
        {
            'title': '2. 3D SDF Raymarching',
            'badge': 'FAIL: ПЛАСТИЛИНОВЫЙ SDF',
            'badge_bg': (210, 120, 25),
            'img_p': os.path.join(base, 'results/method1_3d_sdf/m1_01_juggernaut_x4.png'),
            'scale_tag': 'Разрешение 48x48 (x4 zoom)',
            'bullets': [
                '• Сферы и капсулы: эффект надутых резиновых шаров',
                '• Pillow Shading: круговые градиенты света от центра',
                '• Сглаживание smin() превращает сталь в мыльный пластилин',
                '• Нет острых кованых ребер, фасок и граней брони',
                '• При квантовании дает грязь и шум вокруг контуров'
            ]
        },
        {
            'title': '3. Настоящий референс (AAA)',
            'badge': 'TARGET: ПРОФЕССИОНАЛЬНЫЙ АРТ',
            'badge_bg': (35, 155, 80),
            'img_p': os.path.join(base, 'references/knight_frame0_84x84_x3.png'),
            'scale_tag': 'Разрешение 84x84 (x3 zoom, из assets)',
            'bullets': [
                '• Анатомический каркас: выверенные пропорции человека',
                '• Pixel Clusters: свет и тень уложены в читаемые плашки',
                '• Боевая стойка с естественным переносом центра тяжести',
                '• Hue-Shifting: холодные глубокие тени + зеркальный блик',
                '• Готовая покадровая анимация ударов и бега в 84x84'
            ]
        }
    ]

    col_w = (w - 120) // 3
    for i, c in enumerate(cols):
        cx = 40 + i * (col_w + 20)
        cy = 110
        # Card bg
        draw.rounded_rectangle([(cx, cy), (cx + col_w, cy + 640)], radius=12, fill=(24, 28, 36), outline=(48, 54, 70), width=2)
        
        # Title & Badge
        draw.text((cx + 16, cy + 16), c['title'], fill=(230, 235, 245), font=font_col_header)
        bw = 350
        draw.rounded_rectangle([(cx + 16, cy + 46), (cx + 16 + bw, cy + 74)], radius=6, fill=c['badge_bg'])
        draw.text((cx + 24, cy + 51), c['badge'], fill=(255, 255, 255), font=font_badge)

        # Image box
        box_y = cy + 86
        draw.rounded_rectangle([(cx + 16, box_y), (cx + col_w - 16, box_y + 260)], radius=8, fill=(12, 14, 18), outline=(36, 42, 54), width=1)
        
        # Paste preview sprite centered
        if os.path.exists(c['img_p']):
            sp = Image.open(c['img_p'])
            px = cx + 16 + (col_w - 32 - sp.width) // 2
            py = box_y + (260 - sp.height) // 2
            img.paste(sp, (px, py), sp if sp.mode == 'RGBA' else None)
            draw.text((cx + 22, box_y + 235), c['scale_tag'], fill=(130, 145, 170), font=font_body)

        # Bullet points
        text_y = box_y + 275
        for b in c['bullets']:
            draw.text((cx + 16, text_y), b, fill=(200, 210, 225), font=font_body)
            text_y += 30

    out_path = os.path.join(base, 'references/visual_critique_comparison.png')
    img.save(out_path)
    print(f'Successfully built visual critique comparison: {out_path}')

if __name__ == '__main__':
    build_infographic()
