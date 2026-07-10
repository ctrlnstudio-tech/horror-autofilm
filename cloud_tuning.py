import random


THAI_NAMES = [
    "นนท์", "ตั้ม", "วิน", "บาส", "ก้อง", "พีท", "อาร์ม", "เต้", "มอส", "เคน",
    "มายด์", "ฝน", "แพร", "นุ่น", "เมย์", "แนน", "ขวัญ", "ฟ้า", "พลอย", "จูน",
    "เอม", "ดา", "มิ้น", "น้ำ", "แป้ง", "เบลล์", "ป่าน", "ออย", "กิ๊ฟ", "รุ้ง",
]


def replace_hero_word(text, name):
    if not isinstance(text, str):
        return text
    return text.replace("ตัวเอก", name)


def clean_story_line(line, seed):
    return replace_hero_word(line, seed.get("name") or "นนท์")


async def scary_female_edge_tts(text, output):
    try:
        import edge_tts
    except Exception as error:
        raise RuntimeError("ไม่พบ edge-tts สำหรับรันบนคลาวด์ ติดตั้ง requirements.txt ให้ครบก่อน") from error

    voices = ["th-TH-PremwadeeNeural", "th-TH-AcharaNeural"]
    last_error = None
    for voice in voices:
        try:
            communicate = edge_tts.Communicate(text, voice=voice, rate="-12%", pitch="-8Hz")
            await communicate.save(str(output))
            if output.exists() and output.stat().st_size > 12000:
                return
        except Exception as error:
            last_error = error
    raise RuntimeError(f"สร้างเสียงพากย์บนคลาวด์ไม่สำเร็จ: {last_error}")


def install(server):
    original_make_seed = server.make_seed
    original_story_lines = server.story_lines
    server.make_seed = lambda brief, avoid=None: make_coherent_seed(server, original_make_seed, brief, avoid)
    server.story_lines = lambda seed, mode: story_lines(server, original_story_lines, seed, mode)
    server._make_narration_edge_tts = scary_female_edge_tts
    install_story_name_tuning(server)
    install_visual_tuning(server)
    install_image_stability_tuning(server)
    install_make_story_tuning(server)
    original_run = server.run

    def tuned_run(command):
        if isinstance(command, list):
            command = tune_ffmpeg_command(command)
        return original_run(command)

    server.run = tuned_run


def strip_forbidden_title_prefix(text):
    text = text.strip()
    for prefix in ("อย่าเปิด...", "อย่าเปิด..", "อย่าเปิด.", "อย่าเปิด"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return text.strip(" .ๆ…:：-–—")


def compact_place_title(server, place_title):
    known_places = [item[0] for item in getattr(server, "PLACES", [])] + [item[0] for item in getattr(server, "PLACE_ROOTS", [])]
    for name in sorted(known_places, key=len, reverse=True):
        if place_title.startswith(name) or name in place_title:
            return name
    return place_title[:18].rstrip("ในข้างหลังใต้บนริม")


def compact_object_title(object_name):
    keys = [
        "เทปวิดีโอ", "กล่องยา", "ม้วนฟิล์ม", "นาฬิกา", "เสื้อกันฝน", "ตลับเทป",
        "ตุ๊กตาไม้", "กุญแจห้อง", "กุญแจ", "ซองจดหมาย", "ไฟฉาย", "กล่องรับฝาก",
        "ผ้าคลุมกระจก", "บัตรพนักงาน", "แฟ้มคดี", "สมุดลงชื่อ", "รูปถ่าย",
        "พวงกุญแจ", "บัตรคิว", "ใบเสร็จ",
    ]
    for key in keys:
        if key in object_name:
            return key
    return object_name[:14]


def make_story_title(server, place_title, object_name, pattern_name, brief=""):
    cleaned = strip_forbidden_title_prefix(brief)
    if cleaned and len(cleaned) >= 4:
        return cleaned[:42]

    place_title = compact_place_title(server, place_title)
    object_name = compact_object_title(object_name)
    choices = {
        "ของต้องห้ามเลือกเจ้าของ": [
            f"{object_name}ต้องห้าม",
            f"ของคืนเดียวจาก{place_title}",
            f"เจ้าของคนสุดท้ายของ{object_name}",
        ],
        "กล้องเห็นสิ่งที่ยังไม่เกิด": [
            f"ภาพสุดท้ายจาก{place_title}",
            f"กล้องคืนตายที่{place_title}",
            "ภาพที่ยังไม่เกิด",
        ],
        "คนที่โทรมาจากสถานที่ปิดตาย": [
            f"สายสุดท้ายจาก{place_title}",
            f"เบอร์ที่โทรจาก{place_title}",
            f"เสียงเรียกใน{place_title}",
        ],
        "ห้องที่ไม่มีอยู่ในแปลน": [
            f"ชั้นที่หายไปใน{place_title}",
            f"ห้องลับหลัง{place_title}",
            "ทางออกที่ไม่มีในแปลน",
        ],
        "ความผิดที่สถานที่จำได้": [
            f"แฟ้มสุดท้ายของ{place_title}",
            f"ชื่อถัดไปใน{place_title}",
            f"คืนที่{place_title}จำได้",
        ],
        "พิธีเก่าที่ถูกเปิดซ้ำ": [
            f"พิธีคืนกลับที่{place_title}",
            f"รอยมือบน{object_name}",
            f"คืนส่งคนแทนที่{place_title}",
        ],
    }
    title = random.choice(choices.get(pattern_name, [f"คืนสุดท้ายที่{place_title}", f"เสียงจาก{place_title}", f"เงาใน{place_title}"]))
    return strip_forbidden_title_prefix(title)[:42]


SCENARIO_PACKS = [
    {
        "pattern": "คนที่โทรมาจากสถานที่ปิดตาย",
        "place": ("ห้องเช่าเหนือร้านยา", "old rental room above a closed Thai pharmacy"),
        "protagonist": "คนส่งเวชภัณฑ์",
        "object": "กล่องยาเก่าที่ฉลากถูกขูดออก",
        "ghost": "แม่ของตัวเอก",
        "event": "โทรศัพท์โทรเข้ามาจากเบอร์ของสถานที่เดียวกัน",
        "twist": "คนที่โทรมาขอความช่วยเหลือไม่เคยมีตัวตนในทะเบียนคนเป็น",
        "witness": "พนักงานเก่าที่ลาออกไปแล้ว",
        "sensory": "กลิ่นยาฆ่าเชื้อจางๆ เหมือนโรงพยาบาลเก่า",
        "clue": "ชื่อคนตายในสมุดลงเวลา",
        "rule": "ห้ามตอบถ้ามีคนเรียกจากด้านใน",
        "final_image": "ของต้องห้ามที่กลับมาอยู่บนโต๊ะตัวเดิม",
    },
    {
        "pattern": "กล้องเห็นสิ่งที่ยังไม่เกิด",
        "place": ("ห้องควบคุมกล้องโรงหนังปิดตาย", "abandoned cinema CCTV control room"),
        "protagonist": "ช่างซ่อมกล้องวงจรปิด",
        "object": "ม้วนฟิล์มที่ถ่ายรูปหลังจากเจ้าของตายแล้ว",
        "ghost": "คนขายตั๋วที่ตายก่อนโรงหนังปิด",
        "event": "คนขายตั๋วยืนอยู่กลางโถงโรงหนังทั้งที่พื้นที่จริงว่างเปล่า",
        "twist": "ภาพสุดท้ายจากกล้องไม่ได้ถ่ายอดีตหรืออนาคต แต่มันถ่ายช่วงเวลาหลังจากตัวเอกตายไปแล้ว",
        "witness": "พนักงานเก่าที่ลาออกไปแล้ว",
        "sensory": "เสียงวิทยุแตกพร่าที่ไม่มีใครเปิด",
        "clue": "รอยเท้าที่หยุดตรงหน้ากล้อง",
        "rule": "ห้ามหันกลับไปมองหลังได้ยินเสียงครั้งที่สาม",
        "final_image": "กล้องวงจรปิดที่ยังบันทึกภาพทั้งที่ไม่มีไฟ",
    },
    {
        "pattern": "ของต้องห้ามเลือกเจ้าของ",
        "place": ("คลังของหายใต้ทางด่วน", "old lost-and-found warehouse under a Thai expressway"),
        "protagonist": "เจ้าหน้าที่รับฝากของ",
        "object": "กล่องรับฝากที่มีเสียงหายใจอยู่ข้างใน",
        "ghost": "ผู้หญิงผมเปียกที่พูดด้วยเสียงของคนรู้จัก",
        "event": "กล่องรับฝากสั่นเหมือนมีคนเคาะจากข้างใน",
        "twist": "ของต้องห้ามไม่ได้ถูกเก็บไว้เพื่อกันคนเข้า แต่เพื่อกันบางอย่างไม่ให้ออกมา",
        "witness": "ลุงยามหน้าอาคาร",
        "sensory": "กลิ่นธูปเก่าปนกลิ่นน้ำขัง",
        "clue": "รอยนิ้วมือเปียกบนฝุ่นแห้ง",
        "rule": "ห้ามเอาของชิ้นนั้นออกจากอาคาร",
        "final_image": "ประตูที่เปิดแง้มไว้แค่พอเห็นเงาคนยืนรอ",
    },
    {
        "pattern": "ห้องที่ไม่มีอยู่ในแปลน",
        "place": ("ชั้นลอยหลังลิฟต์โรงพยาบาลเก่า", "hidden mezzanine behind an old hospital elevator"),
        "protagonist": "เจ้าหน้าที่เวชระเบียน",
        "object": "กุญแจห้องที่ไม่มีอยู่ในแปลนอาคาร",
        "ghost": "คนไข้เก่าที่ถามหาห้องของตัวเองทุกคืน",
        "event": "ลิฟต์ขึ้นไปชั้นที่ไม่มีอยู่จริง",
        "twist": "ประตูที่ห้ามเปิดไม่ได้พาเข้าไปเจอผี แต่มันพาออกไปยังคืนที่ไม่มีใครควรรอดกลับมา",
        "witness": "แม่บ้านที่ไม่ยอมขึ้นชั้นบน",
        "sensory": "ลมเย็นที่พัดออกมาจากห้องปิด",
        "clue": "เลขห้องที่ถูกขูดทิ้งจากแผนผัง",
        "rule": "ห้ามเปิดไฟดวงสุดท้ายในทางเดิน",
        "final_image": "ไฟดวงเดียวที่ติดอยู่ลึกสุดทางเดิน",
    },
    {
        "pattern": "ความผิดที่สถานที่จำได้",
        "place": ("ห้องเก็บแฟ้มเทศบาล", "municipal archive room filled with dusty case files"),
        "protagonist": "เจ้าหน้าที่ธุรการ",
        "object": "แฟ้มคดีที่หน้าสุดท้ายหายไป",
        "ghost": "ชายในรูปถ่ายที่ค่อยๆ หันหน้ามามอง",
        "event": "ชื่อของตัวเอกไปปรากฏในสมุดลงชื่อเมื่อสิบปีก่อน",
        "twist": "พอทุกอย่างจบ ตัวเอกพบว่าตัวเองกลายเป็นชื่อถัดไปในแฟ้มคดี",
        "witness": "ลุงยามหน้าอาคาร",
        "sensory": "เสียงน้ำหยดเหมือนมีใครนับเวลา",
        "clue": "ใบเสร็จที่พิมพ์เวลาหลังจากเหตุการณ์จบ",
        "rule": "ห้ามอ่านข้อความที่อยู่หลังรูปถ่าย",
        "final_image": "แฟ้มคดีที่ยังเปิดค้างอยู่บนโต๊ะตัวเดิม",
    },
    {
        "pattern": "พิธีเก่าที่ถูกเปิดซ้ำ",
        "place": ("ห้องเก็บชุดไทยท้ายโรงละคร", "old Thai costume storage room behind a theater"),
        "protagonist": "แม่บ้านโรงแรม",
        "object": "ผ้าคลุมกระจกที่มีรอยมือเปียก",
        "ghost": "หญิงใส่ชุดไทยที่หันหลังตลอดเวลา",
        "event": "นาฬิกาทุกเรือนหยุดพร้อมกันที่เวลาตายของใครบางคน",
        "twist": "ทุกคนที่บอกว่าไม่รู้เรื่อง ความจริงเคยรอดออกมาได้ด้วยการส่งคนใหม่เข้าไปแทน",
        "witness": "แม่บ้านที่ไม่ยอมขึ้นชั้นบน",
        "sensory": "กลิ่นธูปเก่าปนกลิ่นน้ำขัง",
        "clue": "รูปถ่ายที่มีเงาเพิ่มขึ้นหนึ่งคน",
        "rule": "ห้ามพูดชื่อสถานที่หลังเที่ยงคืน",
        "final_image": "รอยเท้าเปียกคู่ใหม่หน้าห้อง",
    },
    {
        "pattern": "คนที่โทรมาจากสถานที่ปิดตาย",
        "place": ("ตู้โทรศัพท์หน้าวัดร้าง", "abandoned public phone booth in front of an old Thai temple"),
        "protagonist": "คนขับวินที่ไม่กล้าดับเครื่อง",
        "object": "ซองจดหมายที่ไม่มีชื่อผู้ส่ง",
        "ghost": "แม่ของตัวเอก",
        "event": "เสียงประกาศเรียกชื่อคนที่ยังไม่เข้ามาในอาคาร",
        "twist": "เสียงที่คอยเตือนมาตลอดคือเสียงของตัวเอกจากคืนสุดท้าย",
        "witness": "พระเวรหน้าวัด",
        "sensory": "เสียงวิทยุแตกพร่าที่ไม่มีใครเปิด",
        "clue": "รอยนิ้วมือเปียกบนฝุ่นแห้ง",
        "rule": "ห้ามตอบถ้ามีคนเรียกจากด้านใน",
        "final_image": "ประตูที่เปิดแง้มไว้แค่พอเห็นเงาคนยืนรอ",
    },
    {
        "pattern": "ของต้องห้ามเลือกเจ้าของ",
        "place": ("บ้านเช่าข้างทางรถไฟ", "old rental house beside a railway track"),
        "protagonist": "คนเก็บค่าเช่า",
        "object": "นาฬิกาข้อมือที่เดินถอยหลัง",
        "ghost": "ผู้หญิงผมเปียกที่พูดด้วยเสียงของคนรู้จัก",
        "event": "นาฬิกาทุกเรือนหยุดพร้อมกันที่เวลาตายของใครบางคน",
        "twist": "ของที่คิดว่าเก็บมาได้ ความจริงเป็นของที่ตัวเอกเคยเอาไปทิ้งเองเมื่อหลายปีก่อน",
        "witness": "แม่ค้าข้าวแกงฝั่งตรงข้าม",
        "sensory": "เสียงรองเท้าลากช้าๆ หลังผนัง",
        "clue": "ชื่อคนตายในสมุดลงเวลา",
        "rule": "ห้ามหันกลับไปมองหลังได้ยินเสียงครั้งที่สาม",
        "final_image": "ไฟดวงเดียวที่ติดอยู่ลึกสุดทางเดิน",
    },
]


def make_coherent_seed(server, original_make_seed, brief, avoid=None):
    seed = original_make_seed(brief, avoid=avoid)
    avoid = avoid or {}
    name = random.choice(THAI_NAMES)
    candidates = SCENARIO_PACKS[:]
    random.shuffle(candidates)
    blocked_places = avoid.get("places", set())
    blocked_patterns = avoid.get("patterns", set())
    curated = [
        item for item in candidates
        if item["place"][0] not in blocked_places and item["pattern"] not in blocked_patterns
    ]
    use_curated = curated and random.random() < 0.22
    if use_curated:
        scenario = random.choice(curated)
    else:
        scenario = {
            "pattern": seed["pattern"]["name"],
            "place": seed["place"],
            "protagonist": seed["protagonist"],
            "object": seed["object"],
            "ghost": seed["ghost"],
            "event": seed["event"],
            "twist": seed["twist"],
            "witness": seed["witness"],
            "sensory": seed["sensory"],
            "clue": seed["clue"],
            "rule": seed["rule"],
            "final_image": seed["final_image"],
        }
        for _ in range(8):
            if scenario["place"][0] not in blocked_places and scenario["pattern"] not in blocked_patterns:
                break
            retry = original_make_seed(brief, avoid=avoid)
            scenario.update({
                "pattern": retry["pattern"]["name"],
                "place": retry["place"],
                "protagonist": retry["protagonist"],
                "object": retry["object"],
                "ghost": retry["ghost"],
                "event": retry["event"],
                "twist": retry["twist"],
                "witness": retry["witness"],
                "sensory": retry["sensory"],
                "clue": retry["clue"],
                "rule": retry["rule"],
                "final_image": retry["final_image"],
            })
    pattern = next(item for item in server.STORY_PATTERNS if item["name"] == scenario["pattern"])
    ghost = replace_hero_word(scenario["ghost"], name)
    if scenario["ghost"] == "แม่ของตัวเอก":
        server.GHOST_VISUALS[ghost] = "a mother-shaped shadow at the edge of a dark room"
    seed.update({
        "title": make_story_title(server, scenario["place"][0], scenario["object"], scenario["pattern"], brief),
        "name": name,
        "place": scenario["place"],
        "protagonist": scenario["protagonist"],
        "object": scenario["object"],
        "ghost": ghost,
        "event": replace_hero_word(scenario["event"], name),
        "twist": replace_hero_word(scenario["twist"], name),
        "witness": replace_hero_word(scenario["witness"], name),
        "sensory": replace_hero_word(scenario["sensory"], name),
        "clue": replace_hero_word(scenario["clue"], name),
        "rule": replace_hero_word(scenario["rule"], name),
        "final_image": replace_hero_word(scenario["final_image"], name),
        "pattern": pattern,
        "_curated": True,
    })
    return seed


def story_lines(server, original_story_lines, seed, mode):
    if not seed.get("_curated"):
        return [clean_story_line(line, seed) for line in original_story_lines(seed, mode)]

    base = [clean_story_line(server.fill_story_template(template, seed).strip(), seed) for template in seed["pattern"]["beats"]]
    middles = [clean_story_line(server.fill_story_template(template, seed).strip(), seed) for template in seed["pattern"].get("middles", [])]
    lines = []
    middle_groups = {2: middles[0:2], 4: middles[2:4], 6: middles[4:6], 8: middles[6:8]}
    for index, line in enumerate(base, start=1):
        lines.append(line)
        lines.extend(middle_groups.get(index, []))
    if mode == "short":
        return lines
    return [clean_story_line(server.expand_long_line(line, seed, index, len(lines)), seed) for index, line in enumerate(lines, start=1)]


def install_story_name_tuning(server):
    original_story_context = server.story_context

    def tuned_story_context(seed):
        context = original_story_context(seed)
        context["name"] = seed.get("name") or "นนท์"
        return context

    server.story_context = tuned_story_context


def install_make_story_tuning(server):
    def tuned_make_story(mode, brief, avoid=None):
        seed = server.make_seed(brief, avoid=avoid)
        lines = server.story_lines(seed, mode)
        target_seconds = 174 if mode == "short" else 420
        duration = max(6, round(target_seconds / len(lines)))
        scenes = []
        for index, line in enumerate(lines, start=1):
            scenes.append({
                "number": index,
                "beat": "เสียงเล่าเรื่องต่อเนื่อง",
                "duration": duration,
                "narration": clean_story_line(line, seed),
                "visual": server.scene_visual_detail(seed, line, index),
            })
        return {
            "mode": mode,
            "title": seed["title"],
            "seed": {
                "name": seed.get("name", ""),
                "placeTitle": seed["place"][0],
                "placeVisual": seed["place"][1],
                "protagonist": seed["protagonist"],
                "object": seed["object"],
                "ghost": seed["ghost"],
                "event": seed["event"],
                "twist": seed["twist"],
                "pattern": seed["pattern"]["name"],
            },
            "targetSeconds": target_seconds,
            "scenes": scenes,
            "script": "\n\n".join(clean_story_line(line, seed) for line in lines),
        }

    server.make_story = tuned_make_story


def install_visual_tuning(server):
    server.ROLE_VISUALS.update({
        "เจ้าหน้าที่รับฝากของ": "one adult Thai lost-and-found clerk with a small tag book",
        "คนเก็บค่าเช่า": "one adult Thai rent collector holding a receipt book",
        "คนส่งเวชภัณฑ์": "one adult Thai medical supply courier carrying a sealed box",
        "เจ้าหน้าที่ธุรการ": "one adult Thai office clerk holding a document folder",
    })
    server.OBJECT_VISUALS.update({
        "ม้วนฟิล์มที่ถ่ายรูปหลังจากเจ้าของตายแล้ว": "an old camera film roll in a metal canister, dusty and ominous",
        "นาฬิกาข้อมือที่เดินถอยหลัง": "an old wristwatch with its hands pointing backward, no readable numbers",
        "ซองจดหมายที่ไม่มีชื่อผู้ส่ง": "a sealed old envelope with no readable address",
        "กล่องรับฝากที่มีเสียงหายใจอยู่ข้างใน": "a locked deposit box with small breathing holes",
        "ผ้าคลุมกระจกที่มีรอยมือเปียก": "a cloth covering a mirror with wet handprints",
    })
    server.GHOST_VISUALS.update({
        "แม่ของตัวเอก": "a mother-shaped shadow at the edge of a dark room",
        "ชายในรูปถ่ายที่ค่อยๆ หันหน้ามามอง": "a man in an old photograph slowly turning toward camera",
        "คนไข้เก่าที่ถามหาห้องของตัวเองทุกคืน": "an old patient apparition in a faded hospital gown",
    })
    server.EVENT_VISUALS.update({
        "คนขายตั๋วยืนอยู่กลางโถงโรงหนังทั้งที่พื้นที่จริงว่างเปล่า": "a dead ticket seller silhouette in an empty abandoned cinema lobby",
        "กล่องรับฝากสั่นเหมือนมีคนเคาะจากข้างใน": "a locked deposit box trembling as if knocked from inside",
        "นาฬิกาทุกเรือนหยุดพร้อมกันที่เวลาตายของใครบางคน": "many old clocks stopped at the same time, no readable numbers",
        "เสียงประกาศเรียกชื่อคนที่ยังไม่เข้ามาในอาคาร": "an old ceiling speaker in an empty corridor, no visible text",
    })
    # Keep the original image prompt style. The mapping updates above only help
    # existing prompts translate the story objects/roles more clearly.


def aligned_scene_visual_detail(server, seed, line, number):
    place_th, place_en = seed["place"]
    role = server.ROLE_VISUALS.get(seed["protagonist"], f"one adult Thai {seed['protagonist']}")
    object_visual = server.OBJECT_VISUALS.get(seed["object"], seed["object"])
    ghost_visual = server.GHOST_VISUALS.get(seed["ghost"], seed["ghost"])
    event_visual = server.EVENT_VISUALS.get(seed["event"], seed["event"])

    if number == 1:
        return f"opening shot of {place_en}, the forbidden place clearly visible, {object_visual} in the foreground, no people yet"
    if "สุดท้าย" in line or "ตั้งแต่นั้น" in line or "หลังจากคืนนั้น" in line or "เหลือเพียง" in line:
        return f"final aftermath shot of {place_en}, {object_visual} or {ghost_visual} remains as the haunting clue, no extra people"
    if seed["event"] in line or "ทุกอย่างเกิดขึ้น" in line:
        return f"{event_visual} inside {place_en}, {role} frozen in fear, cinematic practical lighting"
    if seed["ghost"] in line or "ปรากฏ" in line or "เงา" in line:
        return f"{ghost_visual} appearing subtly at the dark edge of {place_en}, {role} in the same frame but only one living person"
    if any(token in line for token in ("ถูกเรียก", "เข้าไปเอา", "เข้าไปที่นั่น", "ก้าวเข้า", "เดินเข้าไป")):
        return f"{role} entering {place_en} at night, {object_visual} visible nearby, tense but realistic"
    if seed["object"] in line or "ของชิ้นนั้น" in line or "ของต้องห้าม" in line:
        return f"close shot of {object_visual} placed inside {place_en}, ominous empty space around it"
    if "โทร" in line or "มือถือ" in line or "ปลายสาย" in line:
        return f"{role} holding a glowing mobile phone inside {place_en}, the location clearly visible behind them, no readable text"
    if "ชื่อ" in line or "บันทึก" in line or "เอกสาร" in line or "สมุด" in line or "แฟ้ม" in line or "หลักฐาน" in line:
        return f"{role} discovering old evidence beside {object_visual} inside {place_en}, no readable writing"
    if "กระจก" in line:
        return f"{role} staring into a dirty mirror inside {place_en}, {ghost_visual} appears only as a reflection"
    if "รอยเท้า" in line:
        return f"wet footprints circling on the floor of {place_en}, {role} standing back with a flashlight"
    if "นาฬิกา" in line:
        return f"old clocks inside {place_en}, all stopped strangely, {role} looking terrified"
    if "ทางเดิน" in line or "ประตู" in line:
        return f"a tense corridor or doorway inside {place_en}, {object_visual} still visible as the key clue"
    return f"{role} inside {place_en}, {object_visual} nearby, {ghost_visual} suggested in the shadows, realistic horror scene"


def install_image_stability_tuning(server):
    original_scene_visual_detail = server.scene_visual_detail
    original_ai_image_prompt = server.ai_image_prompt

    def stable_scene_visual_detail(seed, line, number):
        if seed.get("_curated"):
            visual = aligned_scene_visual_detail(server, seed, line, number)
        else:
            visual = original_scene_visual_detail(seed, line, number)
        stability = (
            "medium or wide Thai horror film shot, location and forbidden object dominate, "
            "one adult person at most, person seen from behind or in partial shadow, "
            "faces small and not close to camera, hands mostly hidden, realistic body proportions"
        )
        return f"{visual}, {stability}"

    def stable_ai_image_prompt(scene, story, size):
        prompt = original_ai_image_prompt(scene, story, size)
        return " ".join([
            prompt,
            "Keep the original scene meaning exactly.",
            "Avoid close-up portraits, visible hands, extra fingers, warped bodies, melted faces, duplicated people, random children, random extra characters.",
            "Use a restrained realistic Thai horror movie look with natural colors, practical lighting, and clear location detail.",
            "Show the exact place and the key object or event from this scene; do not replace it with an unrelated old house.",
        ])

    server.scene_visual_detail = stable_scene_visual_detail
    server.ai_image_prompt = stable_ai_image_prompt


def scene_image_directives(server, scene, story):
    seed = story.get("seed", {})
    place_en = seed.get("placeVisual", "old Thai haunted interior")
    role = server.ROLE_VISUALS.get(seed.get("protagonist", ""), f"one adult Thai {seed.get('protagonist', 'person')}")
    object_visual = server.OBJECT_VISUALS.get(seed.get("object", ""), seed.get("object", "forbidden object"))
    ghost_visual = server.GHOST_VISUALS.get(seed.get("ghost", ""), seed.get("ghost", "subtle ghost presence"))
    event_visual = server.EVENT_VISUALS.get(seed.get("event", ""), seed.get("event", "supernatural event"))
    line = scene["narration"]
    directives = [
        f"exact location: {place_en}",
        f"main forbidden object: {object_visual}",
        "Thai horror realism, adult characters only",
    ]
    if scene["number"] == 1:
        directives += [
            "opening establishing shot of the exact location from the story",
            "the forbidden object must be visible in the foreground",
            "no living character in the foreground, no random extra people",
        ]
    elif seed.get("event", "") in line or "ทุกอย่างเกิดขึ้น" in line:
        directives += [f"show the specific supernatural event: {event_visual}", f"show exactly one living person: {role}"]
    elif seed.get("ghost", "") in line or "ปรากฏ" in line or "เงา" in line:
        directives += [f"show exactly one living person: {role}", f"show the ghost only as a subtle background figure: {ghost_visual}", "do not add a second normal person"]
    elif "สุดท้าย" in line or "หลังจากคืนนั้น" in line or "เหลือเพียง" in line:
        directives += ["final aftermath shot of the exact location", f"show {object_visual} or {ghost_visual} as the final haunting detail", "no unrelated house, no extra character"]
    else:
        directives += [f"show exactly one living person: {role}", f"keep {object_visual} visible in the scene", f"ghost presence is subtle: {ghost_visual}"]
    return ". ".join(directives)


def tuned_ai_image_prompt(server, scene, story, size):
    width, height = size
    aspect = "vertical 9:16 composition, 1080x1920" if height > width else "wide horizontal 16:9 composition, 1920x1080"
    seed = story.get("seed", {})
    directives = scene_image_directives(server, scene, story)
    return " ".join([
        "Photorealistic Thai supernatural horror movie still.",
        aspect + ".",
        "Looks like a real film frame, realistic adult Thai people, natural body proportions, cinematic lens, practical lighting, detailed location, not AI art.",
        f"Scene visual summary: {scene['visual']}.",
        f"Strict scene directives: {directives}.",
        f"Story title meaning: {story['title']}. Place: {seed.get('placeTitle', '')}. Event: {seed.get('event', '')}.",
        "Mysterious, frightening, suspenseful, no gore.",
        "All documents, labels, signs, screens, tickets and pages must be blank, turned away, or unreadably blurred.",
        "No children, no extra unrelated people, no random second protagonist, no unrelated house, no unrelated hospital unless it is the story location.",
        "No cartoon, no illustration, no anime, no text, no subtitles, no letters, no numbers, no watermark, no logo, no stretched faces, no deformed bodies.",
    ])


def tune_ffmpeg_command(command):
    tuned = []
    old_music_expression = "0.135*sin(2*PI*43*t)+0.078*sin(2*PI*69*t)+0.052*sin(2*PI*(94+7*sin(2*PI*0.045*t))*t)"
    new_music_expression = "0.172*sin(2*PI*43*t)+0.104*sin(2*PI*69*t)+0.068*sin(2*PI*(94+7*sin(2*PI*0.045*t))*t)+0.034*sin(2*PI*(156+13*sin(2*PI*0.031*t))*t)"
    for item in command:
        if isinstance(item, str):
            item = item.replace(old_music_expression, new_music_expression)
            item = item.replace("volume=1.18", "volume=1.42")
            item = item.replace("[1:a]volume=1.28,asplit=3[a_voice][voice_sc_music][voice_sc_sfx];", "[1:a]volume=1.58,asplit=3[a_voice][voice_sc_music][voice_sc_sfx];")
            item = item.replace("[2:a]volume=1.25[a_music_raw];", "[2:a]volume=1.72[a_music_raw];")
            item = item.replace(
                "[a_music_raw][voice_sc_music]sidechaincompress=threshold=0.042:ratio=2.8:attack=18:release=420:makeup=1[a_music];",
                "[a_music_raw][voice_sc_music]sidechaincompress=threshold=0.058:ratio=2.2:attack=18:release=520:makeup=1.12[a_music];",
            )
            item = item.replace("[3:a]volume=0.66[a_sfx_raw];", "[3:a]volume=0.74[a_sfx_raw];")
        tuned.append(item)
    return tuned
