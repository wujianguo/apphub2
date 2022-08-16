def is_chinese(char):
    cjk_ranges = [
        (0x4E00, 0x62FF),
        (0x6300, 0x77FF),
        (0x7800, 0x8CFF),
        (0x8D00, 0x9FCC),
        (0x3400, 0x4DB5),
        (0x20000, 0x215FF),
        (0x21600, 0x230FF),
        (0x23100, 0x245FF),
        (0x24600, 0x260FF),
        (0x26100, 0x275FF),
        (0x27600, 0x290FF),
        (0x29100, 0x2A6DF),
        (0x2A700, 0x2B734),
        (0x2B740, 0x2B81D),
        (0x2B820, 0x2CEAF),
        (0x2CEB0, 0x2EBEF),
        (0x2F800, 0x2FA1F),
    ]
    char = ord(char)
    for bottom, top in cjk_ranges:
        if char >= bottom and char <= top:
            return True
    return False


def is_fuxing(name):
    names = [
        "欧阳",
        "令狐",
        "皇甫",
        "上官",
        "司徒",
        "诸葛",
        "司马",
        "宇文",
        "呼延",
        "端木",
        "南宫",
        "司空",
        "独孤",
        "西门",
        "东方",
    ]
    return name in names


def parse_name(name):
    if len(name) > 1 and len(name) <= 4:
        chinese = True
        for item in name:
            if not is_chinese(item):
                chinese = False
                break
        if chinese:
            if len(name) == 4:
                return name[0:2], name[2:]
            if len(name) == 3 and is_fuxing(name[:2]):
                return name[:2], name[2:]
            return name[0], name[1:]
    name_parts = (name or "").partition(" ")
    return name_parts[0], name_parts[-1]


if __name__ == "__main__":
    print(parse_name("bill gates"))
    print(parse_name("bill m gates"))
    print(parse_name("billgates"))
    print(parse_name("张在三风"))
    print(parse_name("司徒三风"))
    print(parse_name("司徒三"))
    print(parse_name("司三"))
    print(parse_name("司三二"))

    # print(is_chinese('我'))
