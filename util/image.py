import tempfile, random
from PIL import Image, ImageDraw, ImageFont


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

def generate_icon_image(text, size=(128, 128)):
    colors = random.choice(COLORS)
    color1 = hex_to_rgb(colors[0])
    color2 = hex_to_rgb(colors[1])
    background_color = (
        random_between(color1[0], color2[0]), 
        random_between(color1[1], color2[1]), 
        random_between(color1[2], color2[2]))
    image = Image.new('RGBA', size=size, color=background_color)
    draw = ImageDraw.Draw(image)
    try:
        # todo: choose font by system
        font = ImageFont.truetype('PingFang.ttc', size=int(size[0]/2))
        draw.text((size[0]/2, size[1]/2), text[0], fill=hex_to_rgb(colors[2]), font=font, anchor="mm")
    except:
        pass
    file = tempfile.NamedTemporaryFile(suffix='.png')
    image.save(file)
    return file
