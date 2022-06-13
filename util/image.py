import tempfile, random
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

def generate_random_image(size=(128, 128)):
    image = Image.new('RGBA', size=size)
    pixels = image.load()
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    file = tempfile.NamedTemporaryFile(suffix='.png')
    image.save(file)
    return file

COLORS = [
    ['#DF7FD7', '#DF7FD7', '#591854'],
    ['#E3CAC8', '#DF8A82', '#5E3A37'],
    ['#E6845E', '#E05118', '#61230B'],
    ['#E0B050', '#E6CB97', '#614C23'],
    ['#9878AD', '#492661', '#C59BE0'],
    ['#787BAD', '#141961', '#9B9FE0'],
    ['#78A2AD', '#104F61', '#9BD1E0'],
    ['#78AD8A', '#0A6129', '#9BE0B3'],
]

def hex_to_rgb(hex_string):
    r_hex = hex_string[1:3]
    g_hex = hex_string[3:5]
    b_hex = hex_string[5:7]
    return int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)

def random_between(int1, int2):
    return random.randint(min(int1, int2), max(int1, int2))

def interpolate(f_co, t_co, interval):
    det_co =[(t - f) / interval for f , t in zip(f_co, t_co)]
    for i in range(interval):
        yield [round(f + det * i) for f, det in zip(f_co, det_co)]

def generate_icon_image(text, size=(128, 128)):

    image = Image.new('RGBA', size=size, color=0)
    draw = ImageDraw.Draw(image)

    colors = random.choice(COLORS)
    from_color = hex_to_rgb(colors[0])
    to_color = hex_to_rgb(colors[1])
    for i, color in enumerate(interpolate(from_color, to_color, image.width * 2)):
        draw.line([(i, 0), (0, i)], tuple(color), width=1)

    try:
        # todo: choose font by system
        font = ImageFont.truetype(settings.FONT_FILE, size=int(size[0]/2))
        draw.text((size[0]/2, size[1]/2), text[0], fill=hex_to_rgb(colors[2]), font=font, anchor="mm")
    except:
        pass
    file = tempfile.NamedTemporaryFile(suffix='.png')
    image.save(file)
    return file

def generate_logo_image(colors, size=(128, 128)):

    image = Image.new('RGBA', size=size, color=0)
    draw = ImageDraw.Draw(image)

    from_color = hex_to_rgb(colors[0])
    to_color = hex_to_rgb(colors[1])
    for i, color in enumerate(interpolate(from_color, to_color, image.width * 2)):
        draw.line([(i, 0), (0, i)], tuple(color), width=1)

    try:
        font_name = 'Apple Chancery.ttf'
        font = ImageFont.truetype(font_name, size=int(size[0]/2))
        draw.text((size[0]/2, size[1]/2), 'A', fill=hex_to_rgb(colors[2]), font=font, anchor="mm")

        # font_name = 'Brush Script.ttf'
        # font = ImageFont.truetype(font_name, size=int(size[0]/5))
        # draw.text((size[0]/2, size[1] / 15 * 13), 'APPHUB', fill=hex_to_rgb(colors[2]), font=font, anchor="mm")
    except:
        pass
    image.show()
    # return file

if __name__ == '__main__':
    generate_logo_image(COLORS[4], size=(128,128))
