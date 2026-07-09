def install(server):
    server.story_lines = lambda seed, mode: story_lines(server, seed, mode)
    original_run = server.run

    def tuned_run(command):
        if isinstance(command, list):
            command = tune_ffmpeg_command(command)
        return original_run(command)

    server.run = tuned_run


def story_lines(server, seed, mode):
    base = coherent_story_lines(seed)
    if mode == "short":
        return base

    middle = coherent_middle_lines(seed)
    lines = [base[0], base[1], base[2], *middle, base[3], base[4], base[5], base[6], base[7], base[8], base[9]]
    return [server.expand_long_line(line, seed, index, len(lines)) for index, line in enumerate(lines, start=1)]


def coherent_story_lines(seed):
    place = seed["place"][0]
    protagonist = seed["protagonist"]
    object_name = seed["object"]
    ghost = seed["ghost"]
    event = seed["event"]
    twist = seed["twist"]
    time_text = seed["time"]
    witness = seed["witness"]
    sensory = seed["sensory"]
    clue = seed["clue"]
    rule = seed["rule"]
    final_image = seed["final_image"]

    return [
        f"ก่อนจะเล่าเรื่องนี้ ต้องบอกไว้ก่อนว่า {place} ไม่ใช่สถานที่ที่คนแถวนั้นอยากพูดถึงหลังฟ้ามืด เพราะทุกครั้งที่มีคนเอ่ยถึง มักจะมีใครบางคนได้ยินเสียงตอบกลับมาจากข้างใน ทั้งที่ที่นั่นควรถูกทิ้งร้างไปแล้ว",
        f"{time_text} {protagonist} ต้องเข้าไปที่นั่นเพราะมีคนแจ้งว่าเจอ {object_name} วางอยู่ผิดที่ผิดทาง และถ้าไม่รีบเอาออกมา เช้าวันต่อมามันจะหายไปเหมือนไม่เคยมีใครเห็น",
        f"ทันทีที่ก้าวเข้าไป สิ่งแรกที่ชัดที่สุดคือ {sensory} ความเงียบในนั้นไม่เหมือนสถานที่ว่างเปล่า แต่มันเหมือนมีคนหลายคนกำลังหยุดหายใจเพื่อฟังเสียงฝีเท้าของเขา",
        f"เขาเจอ {object_name} อยู่ตรงจุดลึกสุดของ {place} ข้างๆ มี {clue} เหมือนใครตั้งใจทิ้งหลักฐานไว้ให้รู้ว่าเรื่องนี้เคยเกิดขึ้นมาก่อน และไม่ได้จบลงด้วยดี",
        f"ตอนที่เขาจะหยิบของชิ้นนั้น {event} ทุกอย่างเกิดขึ้นพอดีจนเขาเริ่มเข้าใจว่า สิ่งที่ผิดปกติไม่ได้รอให้เขาเจอ แต่มันกำลังจัดฉากให้เขาเดินไปถึงจุดที่ต้องการ",
        f"เขานึกถึงคำเตือนของ {witness} ที่เคยบอกไว้สั้นๆ ว่า {rule} ตอนแรกเขาคิดว่าเป็นแค่เรื่องเล่าคนแก่ แต่ตอนนี้คำเตือนนั้นดังอยู่ในหัวชัดกว่าทุกเสียงรอบตัว",
        f"แล้ว {ghost} ก็เริ่มปรากฏอยู่ตรงขอบสายตา ไม่ได้พุ่งเข้ามา ไม่ได้กรีดร้อง มีแค่การยืนรอเงียบๆ เหมือนรู้ว่าอีกไม่นานเขาจะเป็นฝ่ายเดินกลับไปหาเอง",
        f"เมื่อเขาพยายามออกจาก {place} ทางเดินทุกทางกลับพาเขาวนกลับมาหา {object_name} อีกครั้ง และทุกครั้งที่กลับมา ของชิ้นนั้นจะวางใกล้ตัวเขามากกว่าเดิม",
        f"สุดท้าย {twist} ความจริงนั้นทำให้เขารู้ว่าเขาไม่ได้เผลอเข้ามาในเรื่องผีของคนอื่น แต่ชื่อของเขาถูกลากเข้ามาอยู่ในเรื่องนี้ตั้งแต่ก่อนคืนที่เขาเปิดประตูเข้าไปแล้ว",
        f"หลังจากคืนนั้น ไม่มีใครเห็นเขาเล่าเรื่องนี้ต่อหน้าอีกเลย เหลือเพียง {final_image} ที่ยังปรากฏอยู่ใน {place} เป็นบางคืน เหมือนกำลังรอให้คนต่อไปเดินเข้าไปฟังตอนจบด้วยตัวเอง",
    ]


def coherent_middle_lines(seed):
    place = seed["place"][0]
    protagonist = seed["protagonist"]
    object_name = seed["object"]
    ghost = seed["ghost"]
    clue = seed["clue"]
    sensory = seed["sensory"]
    rule = seed["rule"]

    return [
        f"{protagonist} พยายามโทรหาคนที่แจ้งเรื่องเข้ามา แต่ปลายสายมีเพียงเสียงลมหายใจเบาๆ และเสียงนั้นดังซ้อนกับเสียงหายใจที่มาจากมุมมืดใน {place}",
        f"เขาเริ่มถ่ายรูปเก็บหลักฐาน แต่รูปแรกที่ได้กลับเห็น {object_name} อยู่ในมือของเขาแล้ว ทั้งที่ในโลกจริงมันยังวางอยู่ห่างออกไปหลายก้าว",
        f"ยิ่งเดินลึกเข้าไป {sensory} ก็ยิ่งแรงขึ้นจนเหมือนมีใครเอาความทรงจำของสถานที่นั้นมาบีบไว้ตรงหน้าอก",
        f"บนผนังใกล้ๆ มีร่องรอยใหม่ที่ดูคล้าย {clue} แต่เมื่อเอาไฟส่องใกล้ๆ ร่องรอยนั้นกลับยังเปียกเหมือนเพิ่งถูกทิ้งไว้ไม่กี่วินาที",
        f"เสียงของ {ghost} ไม่ได้เรียกชื่อเขาตรงๆ แต่มันพูดประโยคที่มีแต่คนใกล้ตัวเขาเท่านั้นที่ควรรู้ ทำให้เขาเริ่มไม่แน่ใจว่าสิ่งที่ตามอยู่รู้จักเขามานานแค่ไหน",
        f"เขาฝืนทำตรงข้ามกับคำเตือนที่ว่า {rule} และทันทีที่ฝืน ความมืดทั้งห้องก็เหมือนขยับเข้ามาใกล้พร้อมกัน",
        f"ก่อนถึงทางออก เขาพบ {object_name} อีกครั้ง คราวนี้มันไม่ได้วางนิ่ง แต่มันเอียงเข้าหาเขาช้าๆ เหมือนถูกมือที่มองไม่เห็นผลักมาให้รับไว้",
        "สิ่งที่น่ากลัวที่สุดไม่ใช่การเห็นผี แต่คือการรู้ว่าทุกทางเลือกที่เขาคิดว่าตัวเองตัดสินใจเอง ถูกสถานที่นี้จัดไว้ล่วงหน้าหมดแล้ว",
    ]


def tune_ffmpeg_command(command):
    tuned = []
    old_music_expression = "0.135*sin(2*PI*43*t)+0.078*sin(2*PI*69*t)+0.052*sin(2*PI*(94+7*sin(2*PI*0.045*t))*t)"
    new_music_expression = "0.172*sin(2*PI*43*t)+0.104*sin(2*PI*69*t)+0.068*sin(2*PI*(94+7*sin(2*PI*0.045*t))*t)+0.034*sin(2*PI*(156+13*sin(2*PI*0.031*t))*t)"
    for item in command:
        if isinstance(item, str):
            item = item.replace(old_music_expression, new_music_expression)
            item = item.replace("[2:a]volume=1.25[a_music_raw];", "[2:a]volume=1.72[a_music_raw];")
            item = item.replace(
                "[a_music_raw][voice_sc_music]sidechaincompress=threshold=0.042:ratio=2.8:attack=18:release=420:makeup=1[a_music];",
                "[a_music_raw][voice_sc_music]sidechaincompress=threshold=0.058:ratio=2.2:attack=18:release=520:makeup=1.12[a_music];",
            )
            item = item.replace("[3:a]volume=0.66[a_sfx_raw];", "[3:a]volume=0.74[a_sfx_raw];")
        tuned.append(item)
    return tuned
