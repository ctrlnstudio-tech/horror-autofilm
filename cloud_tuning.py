import asyncio
import random
import re
import time


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


_LAST_EDGE_REQUEST = 0.0


def edge_text_chunks(text, max_chars=180):
    remaining = " ".join(text.split()).strip()
    chunks = []
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        cut = max(remaining.rfind(mark, 0, max_chars + 1) for mark in (" ", ",", ".", "!", "?", "…", "ๆ", "ฯ"))
        if cut < max_chars // 2:
            cut = max_chars
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return [chunk for chunk in chunks if chunk]


async def scary_female_edge_tts(text, output):
    global _LAST_EDGE_REQUEST
    try:
        import edge_tts
    except Exception as error:
        raise RuntimeError("ไม่พบ edge-tts สำหรับรันบนคลาวด์ ติดตั้ง requirements.txt ให้ครบก่อน") from error

    # Achara is clearer on short Thai narration phrases. Premwadee remains a
    # same-gender fallback so one unavailable voice never changes the speaker.
    voices = ("th-TH-AcharaNeural", "th-TH-PremwadeeNeural")
    parts = []
    last_error = None
    try:
        for index, chunk in enumerate(edge_text_chunks(text), start=1):
            part = output.with_name(f"{output.stem}-edge-{index:02d}.mp3")
            parts.append(part)
            generated = False
            for voice in voices:
                for attempt in range(3):
                    try:
                        spacing = 5.0 - (time.monotonic() - _LAST_EDGE_REQUEST)
                        if spacing > 0:
                            await asyncio.sleep(spacing)
                        part.unlink(missing_ok=True)
                        communicate = edge_tts.Communicate(
                            chunk,
                            voice=voice,
                            rate="-8%",
                            pitch="-2Hz",
                        )
                        _LAST_EDGE_REQUEST = time.monotonic()
                        await communicate.save(str(part))
                        if part.exists() and part.stat().st_size > 2500:
                            generated = True
                            break
                    except Exception as error:
                        last_error = error
                    await asyncio.sleep(5.0 * (attempt + 1))
                if generated:
                    break
            if not generated:
                raise RuntimeError(f"สร้างเสียงพากย์ช่วงที่ {index} ไม่สำเร็จ: {last_error}")

        output.unlink(missing_ok=True)
        with output.open("wb") as combined:
            for part in parts:
                combined.write(part.read_bytes())
        if output.exists() and output.stat().st_size > 12000:
            return
        raise RuntimeError("ไฟล์เสียงที่รวมแล้วสั้นหรือเสียผิดปกติ")
    finally:
        for part in parts:
            part.unlink(missing_ok=True)


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


# The cloud worker must tell a new story every time it runs.  These settings are
# deliberately grounded in distinct Thai places, jobs and physical evidence so
# the narration and AI frame have concrete facts to share.
EXPERIENCE_SETTINGS = [
    {
        "place": "ท่ารถสองแถวเก่าริมแม่น้ำ",
        "visual": "a weathered Thai songthaew terminal beside a river at night, faded blue benches and a dim ticket counter",
        "role": "พนักงานตรวจเที่ยวรถ",
        "role_visual": "one adult Thai transport clerk in a plain dark uniform",
        "object": "ตั๋วเที่ยวสุดท้ายที่ยังเปียกอยู่",
        "object_visual": "a single damp paper songthaew ticket on a metal counter, no readable text",
        "witness": "คนขับเก่าที่เลิกขับรถไปนานแล้ว",
    },
    {
        "place": "แพขนานยนต์เที่ยวสุดท้าย",
        "visual": "an old Thai vehicle ferry dock on a black river at night, wet ramps and one moored ferry",
        "role": "เจ้าหน้าที่เก็บค่าโดยสารแพ",
        "role_visual": "one adult Thai ferry attendant holding a small flashlight",
        "object": "เหรียญโดยสารที่เย็นจัดเหมือนแช่น้ำแข็ง",
        "object_visual": "one tarnished ferry token on a wet wooden ticket booth counter, no readable text",
        "witness": "แม่ค้าริมท่าที่ไม่เคยอยู่เกินสองทุ่ม",
    },
    {
        "place": "ห้องเก็บศพของโรงพยาบาลอำเภอเก่า",
        "visual": "an old Thai district hospital morgue corridor with pale tiled walls, closed steel drawers and practical fluorescent light",
        "role": "เจ้าหน้าที่เวรเปล",
        "role_visual": "one adult Thai hospital orderly in a simple pale uniform",
        "object": "ป้ายชื่อผู้ป่วยที่ไม่มีชื่อพิมพ์อยู่",
        "object_visual": "one blank patient identification tag on a stainless steel tray, no readable text",
        "witness": "พยาบาลเกษียณที่ไม่ยอมเดินผ่านตึกนี้หลังเที่ยงคืน",
    },
    {
        "place": "สถานีสูบน้ำท้ายหมู่บ้าน",
        "visual": "a small abandoned Thai water pumping station beside rice fields at night, rusty pipes and a concrete control room",
        "role": "ช่างซ่อมปั๊มน้ำ",
        "role_visual": "one adult Thai maintenance technician with a tool bag and flashlight",
        "object": "มาตรวัดน้ำที่เข็มหมุนถอยหลังเอง",
        "object_visual": "a rusty water pressure gauge with its needle pointing backward in a concrete pump room",
        "witness": "ผู้ใหญ่บ้านที่ไม่ยอมให้ใครลงไปดูคนเดียว",
    },
    {
        "place": "ห้องฉายหนังของโรงภาพยนตร์ปิดกิจการ",
        "visual": "an abandoned Thai cinema projection room with dusty reels, a cracked projector window and empty red seats below",
        "role": "ช่างซ่อมเครื่องฉาย",
        "role_visual": "one adult Thai projection technician holding a small torch",
        "object": "ฟิล์มม้วนสุดท้ายที่ไม่มีชื่อเรื่อง",
        "object_visual": "one dusty unlabelled film reel beside an old projector, no readable text",
        "witness": "พนักงานขายตั๋วคนสุดท้ายของโรงหนัง",
    },
    {
        "place": "โรงน้ำแข็งร้างหลังตลาดเช้า",
        "visual": "an abandoned Thai ice factory behind an early morning market, cold storage doors, wet concrete and hanging hooks",
        "role": "คนส่งน้ำแข็ง",
        "role_visual": "one adult Thai ice delivery worker wearing a plain jacket",
        "object": "สมุดส่งของที่หน้ากระดาษเปียกทั้งเล่ม",
        "object_visual": "a soaked delivery ledger on a plastic crate, pages blank and unreadable",
        "witness": "แม่ค้าปลาแห้งที่เห็นประตูห้องเย็นเปิดเองทุกคืน",
    },
    {
        "place": "หอระฆังวัดริมคลอง",
        "visual": "an old Thai temple bell tower beside a canal at night, wooden stairs, a bronze bell and moonlit water",
        "role": "เด็กวัดที่โตแล้วกลับมาเยี่ยมบ้าน",
        "role_visual": "one adult Thai man in casual clothes carrying a flashlight",
        "object": "เชือกตีระฆังที่เปียกเหมือนเพิ่งถูกจับ",
        "object_visual": "a wet bell rope hanging below an old bronze temple bell",
        "witness": "พระเวรที่ไม่เคยบอกว่าได้ยินเสียงระฆังกี่ครั้ง",
    },
    {
        "place": "ห้องพักครูของโรงเรียนปิดเทอม",
        "visual": "a deserted Thai rural school teachers room at dusk, old desks, ceiling fans and rain on the windows",
        "role": "ครูฝึกสอนที่มารับเอกสาร",
        "role_visual": "one adult Thai teacher holding a document envelope",
        "object": "บัตรลงเวลาที่เจาะรูเพิ่มขึ้นทุกคืน",
        "object_visual": "an old time card beside a metal punch clock, text blank and unreadable",
        "witness": "ภารโรงที่ล็อกอาคารก่อนพระอาทิตย์ตกเสมอ",
    },
    {
        "place": "อู่เรือหางยาวริมคลอง",
        "visual": "a quiet Thai long-tail boat repair yard beside a canal at night, wooden boats, tarps and still water",
        "role": "ช่างเครื่องเรือ",
        "role_visual": "one adult Thai boat mechanic with a grease-stained work shirt",
        "object": "กุญแจเรือที่มีเชือกผูกด้วยผมเปียก",
        "object_visual": "an old boat key tied with a wet strand of hair on a wooden workbench",
        "witness": "เจ้าของอู่ที่ไม่ยอมให้ใครนอนเฝ้าเรือ",
    },
    {
        "place": "จุดคัดแยกพัสดุของที่ทำการไปรษณีย์เก่า",
        "visual": "an old Thai post office sorting room at night, canvas mail sacks, wooden pigeonholes and a single desk lamp",
        "role": "พนักงานคัดแยกพัสดุ",
        "role_visual": "one adult Thai postal worker in a plain uniform",
        "object": "กล่องพัสดุที่จ่าหน้าถึงคนตาย",
        "object_visual": "one sealed parcel with a blank turned-away label on a wooden sorting table",
        "witness": "หัวหน้าที่ทำการคนเก่าที่ไม่ยอมพูดถึงเที่ยวส่งคืน",
    },
    {
        "place": "ห้องควบคุมลิฟต์ของห้างเก่า",
        "visual": "a hidden Thai shopping mall elevator control room with relay panels, cables and a narrow service corridor",
        "role": "ช่างลิฟต์เวรกะดึก",
        "role_visual": "one adult Thai elevator technician wearing a work vest",
        "object": "ปุ่มลิฟต์สำรองที่มีรอยนิ้วมือเปียก",
        "object_visual": "one wet spare elevator button on a maintenance panel, no readable numbers",
        "witness": "รปภ.กะกลางคืนที่ไม่ขึ้นลิฟต์หลังห้างปิด",
    },
    {
        "place": "บ้านพักนายสถานีรถไฟเล็ก",
        "visual": "an old Thai railway station master's house at night, a signal lamp, peeling wood walls and empty tracks nearby",
        "role": "พนักงานซ่อมสัญญาณรถไฟ",
        "role_visual": "one adult Thai railway maintenance worker holding a signal lantern",
        "object": "นาฬิกาพกที่หยุดตรงเวลาขบวนสุดท้าย",
        "object_visual": "a stopped old pocket watch on a railway desk beside a signal lamp",
        "witness": "นายสถานีเก่าที่ไม่เคยยอมบอกเลขขบวนสุดท้าย",
    },
    {
        "place": "ปั๊มน้ำมันร้างบนถนนสายเก่า",
        "visual": "an abandoned Thai roadside petrol station at night, old pumps, fluorescent canopy and empty highway",
        "role": "พนักงานเติมน้ำมันที่ขับผ่านมาพอดี",
        "role_visual": "one adult Thai petrol station worker in a simple uniform",
        "object": "ใบเสร็จเติมน้ำมันที่ยังอุ่นอยู่",
        "object_visual": "one freshly printed blank fuel receipt on an abandoned petrol station counter",
        "witness": "คนขายก๋วยเตี๋ยวฝั่งตรงข้ามที่เก็บร้านก่อนฟ้ามืด",
    },
    {
        "place": "หอพักพยาบาลหลังโรงพยาบาล",
        "visual": "an old Thai nurses dormitory hallway at night, numbered doors turned away, laundry lines and dim practical lights",
        "role": "พนักงานเวรเปลที่มาส่งของ",
        "role_visual": "one adult Thai hospital orderly carrying a small parcel",
        "object": "กุญแจห้องพักที่ไม่มีหมายเลข",
        "object_visual": "one old room key with a blank key tag on a dormitory windowsill",
        "witness": "แม่บ้านที่ไม่ยอมเก็บผ้าชั้นบนหลังสองทุ่ม",
    },
    {
        "place": "สถานีวิทยุชุมชนบนเนินเขา",
        "visual": "a small Thai community radio station on a misty hill at night, antennas, analog mixer and rain-streaked windows",
        "role": "ดีเจฝึกหัดที่มาปิดเครื่อง",
        "role_visual": "one adult Thai radio technician wearing headphones",
        "object": "เทปบันทึกเสียงที่มีลมหายใจอยู่ท้ายม้วน",
        "object_visual": "one old cassette tape and a small radio recorder on an analog broadcast desk",
        "witness": "ดีเจรุ่นก่อนที่ลาออกโดยไม่บอกเหตุผล",
    },
    {
        "place": "ร้านซ่อมรองเท้าใต้สะพานลอย",
        "visual": "a cramped Thai shoe repair stall beneath a pedestrian overpass at night, hanging shoes, tools and wet pavement",
        "role": "ช่างซ่อมรองเท้ากะดึก",
        "role_visual": "one adult Thai cobbler in a plain apron",
        "object": "รองเท้าหนังคู่เดิมที่เปียกโคลนทุกคืน",
        "object_visual": "one pair of muddy leather shoes on a small shoe repair bench",
        "witness": "แม่ค้าลอตเตอรี่ที่เห็นคนเดินขึ้นสะพานทั้งที่ไม่มีใครอยู่",
    },
    {
        "place": "โรงสีข้าวท้ายตำบล",
        "visual": "an old Thai rice mill at night, wooden grain bins, dusty conveyor belts and one yellow work lamp",
        "role": "คนคุมเครื่องสีข้าว",
        "role_visual": "one adult Thai mill worker holding a lantern",
        "object": "กระสอบข้าวที่มีรอยมือกดจากข้างใน",
        "object_visual": "one rice sack with a single handprint pressed from inside, beside old mill machinery",
        "witness": "เจ้าของโรงสีที่ไม่ยอมชั่งข้าวหลังหกโมงเย็น",
    },
    {
        "place": "ห้องรับยาของคลินิกปิดตัว",
        "visual": "a closed Thai clinic dispensary at night, medicine shelves, a narrow counter and pale fluorescent light",
        "role": "ผู้ช่วยเภสัชที่มารับของคืน",
        "role_visual": "one adult Thai pharmacy assistant carrying a small medicine box",
        "object": "ซองยาที่มีชื่อคนไข้ถูกลบออกหมด",
        "object_visual": "one medicine envelope with its label completely scratched blank on a clinic counter",
        "witness": "เภสัชกรเก่าที่ไม่รับโทรศัพท์จากคลินิกนี้",
    },
    {
        "place": "หอสมุดประชาชนริมกำแพงเมือง",
        "visual": "an old Thai public library beside historic city walls at night, tall bookshelves, reading lamps and rain-dark windows",
        "role": "บรรณารักษ์อาสา",
        "role_visual": "one adult Thai librarian carrying a closed book",
        "object": "บัตรยืมหนังสือที่มีลายเซ็นเพิ่มเอง",
        "object_visual": "one old library borrowing card on a wooden desk, writing hidden and unreadable",
        "witness": "ลุงยามที่ไม่เคยตรวจชั้นหนังสือด้านใน",
    },
    {
        "place": "คลังหลักฐานของสถานีตำรวจเก่า",
        "visual": "a dusty Thai police evidence store at night, metal shelves, sealed boxes and one bare fluorescent lamp",
        "role": "เจ้าหน้าที่ธุรการที่มารับแฟ้ม",
        "role_visual": "one adult Thai office clerk holding an evidence folder",
        "object": "ถุงหลักฐานที่มีโทรศัพท์สั่นอยู่ข้างใน",
        "object_visual": "one sealed evidence bag with a softly vibrating mobile phone inside, no readable screen",
        "witness": "สิบเวรเก่าที่ไม่เข้าคลังหลังเปลี่ยนเวร",
    },
    {
        "place": "ลานจอดรถชั้นใต้ดินของอาคารสำนักงาน",
        "visual": "a dim Thai office building basement car park at night, concrete columns, puddles and empty parking spaces",
        "role": "คนเฝ้าลานจอดรถ",
        "role_visual": "one adult Thai parking attendant holding a flashlight",
        "object": "บัตรจอดรถที่มีเวลาออกเป็นวันพรุ่งนี้",
        "object_visual": "one blank parking ticket lying on a wet concrete parking booth counter",
        "witness": "แม่บ้านกะเย็นที่ไม่ใช้ลิฟต์ลงชั้นใต้ดิน",
    },
    {
        "place": "ห้องเก็บฉากท้ายโรงละครท้องถิ่น",
        "visual": "a Thai local theatre prop storage room at night, painted backdrops, old masks and wooden costume racks",
        "role": "ช่างไฟเวที",
        "role_visual": "one adult Thai stage electrician carrying a work light",
        "object": "หน้ากากละครที่หันมามองคนละทางทุกครั้ง",
        "object_visual": "one old Thai theatre mask turned toward camera on a prop shelf",
        "witness": "ผู้กำกับเก่าที่สั่งห้ามเปิดม่านหลังเวที",
    },
    {
        "place": "ท่าเรือข้ามฟากหน้าตลาดเก่า",
        "visual": "a Thai river ferry pier in front of an old market at night, empty wooden benches, river mist and one tied boat",
        "role": "คนเก็บตั๋วเรือ",
        "role_visual": "one adult Thai ferry ticket clerk in a plain shirt",
        "object": "ตั๋วเรือฉีกครึ่งที่กลับมาติดกันเอง",
        "object_visual": "one rejoined torn ferry ticket on a damp wooden ticket counter, no readable text",
        "witness": "ลุงขายกาแฟที่ไม่รับลูกค้าหลังเรือเที่ยวสุดท้าย",
    },
]


EXPERIENCE_MOTIFS = [
    {
        "id": "last_return",
        "title": "{object_title}จาก{place}",
        "hook": "คนแถวนั้นบอกว่า ถ้าเห็น{object}วางอยู่ที่เดิมทั้งที่ไม่มีใครเอามาคืน ห้ามแตะมันเป็นอันขาด",
        "manifestation": "มันไม่ขยับต่อหน้าตา แต่ทุกครั้งที่{name}หันกลับมา มันจะอยู่ใกล้กว่าเดิม",
        "reveal": "ของชิ้นนั้นไม่ได้ถูกส่งคืนให้สถานที่ แต่มันกำลังส่งเจ้าของคนใหม่กลับไปแทนคนเก่า",
        "ghost": "เงาของคนที่ยืนรอรับของโดยไม่ยอมเผยหน้า",
    },
    {
        "id": "wrong_voice",
        "title": "เสียงสุดท้ายจาก{place}",
        "hook": "มีคนเคยเตือนว่า ถ้าได้ยินเสียงคนรู้จักเรียกจากใน{place} อย่าตอบรับ แม้เสียงนั้นจะรู้ทุกอย่างเกี่ยวกับเรา",
        "manifestation": "เสียงนั้นเริ่มเรียกชื่อ{name}จากมุมที่ไม่ควรมีใครยืนอยู่",
        "reveal": "เสียงที่เรียกมาตลอดคืนไม่ใช่เสียงของผี แต่เป็นเสียงของ{name}เองจากคืนที่เขาไม่ได้กลับออกไป",
        "ghost": "ร่างผู้ใหญ่ที่ยืนหันหลังและพูดด้วยเสียงของคนรู้จัก",
    },
    {
        "id": "missing_record",
        "title": "ชื่อที่หายไปใน{place}",
        "hook": "เรื่องเริ่มจากข้อมูลชิ้นเล็ก ๆ ที่ไม่ควรมีอยู่ เพราะมันยืนยันว่ามีใครบางคนทำงานอยู่ที่นี่ทั้งที่ไม่มีชื่อในทะเบียน",
        "manifestation": "หลักฐานทุกชิ้นค่อย ๆ เปลี่ยนเป็นชื่อของ{name}ทั้งที่เขาไม่เคยมา{place}มาก่อน",
        "reveal": "ชื่อที่หายไปไม่ใช่ของคนอื่นเลย แต่เป็นชื่อเดิมของ{name}ก่อนเหตุการณ์ที่เขาจำไม่ได้",
        "ghost": "เงาคนในชุดทำงานเก่าที่ยืนอยู่หลังกระจก",
    },
    {
        "id": "future_frame",
        "title": "ภาพก่อนกลับจาก{place}",
        "hook": "คนที่เคยเฝ้าที่นี่เชื่อว่า บางคืนสถานที่จะทิ้งภาพของเหตุการณ์ที่ยังไม่เกิดไว้ให้คนที่กำลังจะเจอเอง",
        "manifestation": "ภาพสะท้อนและเงาบนพื้นเริ่มแสดงท่าทางของ{name}ก่อนที่เขาจะขยับจริง",
        "reveal": "สิ่งที่เห็นไม่ใช่ลางเตือน แต่เป็นภาพหลังจากที่{name}ทำตามทุกอย่างครบแล้ว",
        "ghost": "ร่างเงาในภาพสะท้อนที่ขยับช้ากว่าคนจริงหนึ่งจังหวะ",
    },
    {
        "id": "unlisted_shift",
        "title": "กะที่ไม่มีใครรับที่{place}",
        "hook": "ไม่มีใครยอมรับเวรกะสุดท้ายของที่นี่ เพราะคนที่เคยรับกะนั้นมักพูดว่ามีคนมาส่งงานต่อ ทั้งที่ในตารางไม่มีชื่อใคร",
        "manifestation": "มีเสียงขอให้{name}เซ็นรับเวรจากด้านใน ทั้งที่ไฟทุกดวงถูกปิดไปแล้ว",
        "reveal": "คนที่รอส่งเวรไม่ต้องการให้{name}ช่วยทำงาน แต่ต้องการให้เขาอยู่แทนจนกว่าจะมีคนใหม่มา",
        "ghost": "พนักงานเวรกะดึกที่ยืนถือสมุดลงเวลาตรงปลายทางเดิน",
    },
    {
        "id": "impossible_exit",
        "title": "ทางกลับที่หายไปของ{place}",
        "hook": "คนที่ผ่าน{place}ตอนดึกมักจำไม่ได้ว่าตัวเองออกมาได้อย่างไร เพราะทางเดิมจะไม่อยู่ที่เดิมเสมอ",
        "manifestation": "ประตูทุกบานพา{name}กลับมาที่จุดเดิม แต่ของชิ้นนั้นขยับเข้ามาใกล้มือมากขึ้น",
        "reveal": "ทางออกไม่ได้หายไป มันถูกปิดจากฝั่งที่{name}เคยอยู่ตั้งแต่ต้นเรื่องแล้ว",
        "ghost": "เงาคนเปียกน้ำที่ยืนกั้นประตูโดยไม่แตะพื้น",
    },
    {
        "id": "counting",
        "title": "คนสุดท้ายของ{place}",
        "hook": "มีธรรมเนียมแปลก ๆ ว่า หลังปิดที่นี่ห้ามนับจำนวนคนออกเสียง เพราะมักจะมีคนตอบกลับมาจากจุดที่ว่างเปล่า",
        "manifestation": "เสียงนับช้า ๆ ดังขึ้นใกล้{name}ทุกครั้งที่เขาพยายามหันหาเจ้าของเสียง",
        "reveal": "จำนวนที่เสียงนั้นนับไม่ได้หมายถึงคนในสถานที่ แต่มันหมายถึงจำนวนคืนที่{name}เคยหายไปจากโลกนี้",
        "ghost": "หญิงชราที่นับเลขเบา ๆ อยู่หลังประตูครึ่งบาน",
    },
    {
        "id": "borrowed_memory",
        "title": "คืนที่{place}จำได้",
        "hook": "คนเก่าบอกว่า สถานที่นี้ไม่เคยลืมสิ่งที่เกิดขึ้นกับมัน และบางคืนมันจะคืนความทรงจำนั้นให้คนที่ไม่เกี่ยวข้องเลย",
        "manifestation": "{name}เริ่มเห็นภาพเหตุการณ์เก่าปรากฏตรงมุมเดิมของสถานที่ ราวกับกำลังยืนอยู่ในความทรงจำของคนอื่น",
        "reveal": "ความทรงจำที่ถูกยัดเข้ามาไม่ใช่ของคนตาย แต่เป็นของ{name}ที่เคยอยู่ในเหตุการณ์และเลือกจะลืมมัน",
        "ghost": "เงาเงียบ ๆ ที่ยืนมองจากจุดเกิดเหตุเดิม",
    },
    {
        "id": "next_recipient",
        "title": "ผู้รับคนต่อไปของ{place}",
        "hook": "ของทุกชิ้นที่ถูกเก็บไว้ที่นี่มีเจ้าของ แต่มีชิ้นหนึ่งที่ไม่เคยมีใครกล้ารับ เพราะมันมักกลับมาเองหลังจากถูกเอาออกไป",
        "manifestation": "เมื่อ{name}พยายามวาง{object}คืน มันกลับไปอยู่ตรงหน้าเขาพร้อมรอยเปียกที่ไม่เคยมีมาก่อน",
        "reveal": "ไม่มีใครเอาของชิ้นนั้นมาให้{name}เก็บ มันเลือกเขาเป็นผู้รับคนต่อไปตั้งแต่ก่อนเขามาถึง",
        "ghost": "หญิงผมเปียกที่ยืนอยู่ไกล ๆ ราวกับกำลังรอให้ใครรับของจากมือ",
    },
    {
        "id": "stopped_time",
        "title": "เวลาสุดท้ายของ{place}",
        "hook": "นาฬิกาใน{place}เคยหยุดพร้อมกันในคืนเกิดเหตุ และตั้งแต่นั้น คนที่เข้ามาหลังเวลานั้นมักกลับออกไปพร้อมเวลาที่หายไปจากชีวิต",
        "manifestation": "เสียงทุกอย่างรอบตัว{name}ช้าลง ยกเว้นเสียงหายใจที่ดังขึ้นจากด้านหลัง",
        "reveal": "เวลาที่หายไปไม่ได้ถูกขโมยไปไหน มันคือช่วงเวลาที่{name}เคยอยู่ในที่นี้มาก่อนโดยไม่รู้ตัว",
        "ghost": "ร่างคนที่ยืนอยู่ใต้แสงนิ่งสนิทราวกับไม่เดินตามเวลา",
    },
]


# These are original narrative frames inspired by the pacing of Thai
# experience-based ghost stories: normal life first, local detail, a gradual
# anomaly, then a restrained aftermath.  They never reuse source plots or text.
REFERENCE_NARRATIVE_FRAMES = [
    {
        "id": "direct_experience",
        "opening": "เรื่องนี้{name}เป็นคนเล่าเอง ตอนแรกผมยังนึกว่าเขาเล่าธรรมดา ๆ แต่พอได้ฟังจริง ๆ น้ำเสียงมันเหมือนคนที่ยังติดคืนนั้นอยู่",
        "ordinary": "ตอนนั้น{name}มีธุระธรรมดามาก แค่แวะ{place}เพื่อไปดู{object}ที่ยังค้างอยู่ แล้วคิดว่าเดี๋ยวก็กลับ ไม่มีอะไรน่ากังวลเลย",
        "local": "แต่พอไปถึง {witness}ก็มองหน้าแล้วพูดสั้น ๆ ว่า \"อย่าอยู่นาน\" ก่อนย้ำอีกทีว่า {rule} แบบคนที่พูดเหมือนรู้อยู่ก่อนแล้ว",
        "response": "ตอนแรก{name}ก็ยังคิดว่าเป็นคำเตือนทั่ว ๆ ไปจากคนพื้นที่ เลยทำเหมือนทุกอย่างปกติ แต่พออยู่ต่ออีกนิดเดียว ความเงียบใน{place}มันเริ่มกดลงมาจนรู้สึกได้",
        "ending": "หลังคืนนั้น{name}ไม่เคยกลับไป{place}คนเดียวอีกเลย และทุกครั้งที่มีคนถาม เขาจะหยุดกลางประโยคเหมือนยังไม่อยากนึกถึงรายละเอียดทั้งหมด",
    },
    {
        "id": "retold_by_friend",
        "opening": "ผมได้ฟังเรื่องนี้ต่อมาจากเพื่อนของ{name} อีกที เพราะหลังคืนที่{place} ทุกคนพูดเหมือนกันว่า{name}เปลี่ยนไปจริง ๆ แบบคนที่ไม่ค่อยอยากเล่าเรื่องตัวเองแล้ว",
        "ordinary": "จริง ๆ แล้ว{name}ไม่ได้อยากไปเจออะไรลึกลับด้วยซ้ำ วันนั้นแค่ต้องไป{place}ตามงานของ{role} แล้วคิดว่าจะกลับไว ๆ เหมือนทุกครั้ง",
        "local": "ก่อนเข้าไป {witness}ยังเรียกไว้เบา ๆ ว่า \"ถ้าจะไปก็รีบไป\" แล้วทิ้งคำเตือนสั้น ๆ ว่า {rule} เหมือนคนที่ไม่อยากให้ใครต้องลองผิดเอง",
        "response": "พอเริ่มเจอเรื่องแปลก {name}ยังพยายามโทรเล่าให้เพื่อนฟังแบบติดตลก เหมือนยังไม่อยากยอมรับว่าตัวเองกำลังติดอยู่ในสถานการณ์ที่อธิบายไม่ได้",
        "ending": "หลังจากนั้นทุกครั้งที่มีใครพูดถึง{place} {name}จะเงียบไปก่อนเสมอ เหมือนถ้าพูดต่ออีกนิด เรื่องทั้งหมดจะย้อนกลับมาอีกครั้ง",
    },
    {
        "id": "night_shift",
        "opening": "คืนเวรของ{name}ควรจะเป็นคืนธรรมดามาก ๆ แต่เรื่องนี้กลับกลายเป็นคืนที่{name}เล่าแล้วต้องหยุดหายใจไปก่อนทุกครั้ง",
        "ordinary": "{name}ไป{place}ในฐานะ{role} เพื่อจัดการ{object} ให้เสร็จก่อนเช้า และตั้งใจไว้ชัดเจนว่าทำงานเสร็จก็จะกลับทันที",
        "local": "ตอนเตรียมเข้าพื้นที่ {witness}ถามย้ำสั้น ๆ ว่าได้ยินคำเตือนหรือยัง แล้วพูดเบามากว่า {rule} เหมือนคนที่รู้ว่าคืนนี้ไม่ควรฝืนอยู่ต่อ",
        "response": "แต่เพราะคิดว่าเป็นเรื่องแซวกันในที่ทำงาน {name}จึงอยู่ต่อ ตรวจต่อ และพยายามทำเหมือนไม่มีอะไร ทั้งที่ตั้งแต่นาทีแรกก็เริ่มรู้สึกว่าไม่ปกติแล้ว",
        "ending": "หลังคืนนั้นไม่มีใครอยากรับเวรแทน{place}ง่าย ๆ อีก และคำที่{name}ยอมพูดออกมามีแค่ประโยคเดียวว่า อย่ารอให้มันเรียกชื่อก่อน",
    },
    {
        "id": "ordinary_errand",
        "opening": "เรื่องนี้เริ่มจากธุระเล็กมาก ๆ จน{name}บอกเองว่าถ้าย้อนกลับไปได้ ก็คงไม่เข้า{place}ตั้งแต่วันนั้น",
        "ordinary": "หลังจากทำอย่างอื่นเสร็จ {name}แวะ{place}เพื่อดู{object} ที่ค้างอยู่ และคิดจริง ๆ ว่าจะอยู่แค่ไม่กี่นาทีแล้วกลับ",
        "local": "แต่พอจะเดินเข้าไป {witness}กลับมองหน้าอยู่นานผิดปกติ ก่อนจะเตือนแค่ว่า \"อย่าหยุดอยู่ตรงนั้น\" และย้ำอีกทีว่า {rule} โดยไม่ยอมขยายความต่อ",
        "response": "ตอนนั้น{name}ยังคิดว่าเรื่องที่คนแถวนั้นเล่าคงถูกเติมสีให้ดูน่ากลัวเกินจริง เลยเดินเข้าไปเหมือนไม่มีอะไร และไม่ได้บอกใครเลย",
        "ending": "หลังจากนั้น{name}ยังกลับไปแถวนั้นได้เหมือนเดิม แต่จะเลือกอ้อมทุกครั้งที่ต้องผ่านหน้า{place} เหมือนร่างกายจำทางหนีเองได้ก่อนสมอง",
    },
    {
        "id": "quiet_return",
        "opening": "เรื่องนี้ไม่มีอะไรเริ่มต้นยิ่งใหญ่เลย มันเริ่มจากคืนธรรมดา ๆ ที่{name}คิดว่าแค่แวะไปเอาของแล้วกลับบ้าน",
        "ordinary": "วันนั้น{name}มีธุระกับ{place}อยู่แล้ว เพราะต้องเอา{object}ไปส่งหรือไปดูให้เรียบร้อย และคิดว่าคงใช้เวลาไม่นาน",
        "local": "แต่พอเดินเข้าไป {witness}ก็พูดเหมือนคนที่รู้มาก่อนแล้วว่า {rule} จากนั้นก็ไม่ยอมพูดต่ออีก",
        "response": "ตอนนั้น{name}ยังไม่เชื่อมากนัก คิดแค่ว่าคนแถวนั้นอาจพูดขู่กันเล่น แต่พอยิ่งอยู่ใน{place}นาน ความเงียบมันกลับยิ่งเหมือนมีน้ำหนัก",
        "ending": "หลังจากนั้น{name}จะเลี่ยง{place}ทุกครั้งที่ผ่าน และไม่เคยเล่าเรื่องนี้แบบละเอียดให้ใครฟังอีกเลย",
    },
    {
        "id": "local_warning",
        "opening": "ถ้าถาม{name}ตรง ๆ ว่าเรื่องนี้น่ากลัวตรงไหน เขาจะบอกว่าไม่ใช่ตัวผี แต่เป็นตอนที่คนพื้นที่พูดเตือนเขานั่นแหละ ที่ทำให้เริ่มรู้สึกแปลก",
        "ordinary": "วันนั้น{name}แค่ต้องไป{place}เพราะงานของ{role}ยังค้างอยู่ และตั้งใจจะจัดการทุกอย่างให้เสร็จในรอบเดียว",
        "local": "พอไปถึง {witness}ก็มองหน้าแล้วบอกสั้น ๆ ว่า \"อย่าอยู่คนเดียว\" ก่อนเตือนอีกทีว่า {rule} เสียงของเขาเรียบมากจนยิ่งน่าคิด",
        "response": "ตอนแรก{name}ยังพยายามหัวเราะกลบเกลื่อน แต่พอเข้าไปลึกขึ้นและเริ่มเจอ{object}กับร่องรอยแปลก ๆ ความมั่นใจก็หายไปทีละนิด",
        "ending": "สุดท้าย{name}กลับออกมาได้ แต่ทุกครั้งที่มีคนถามถึง{place} เขาจะตอบแค่สั้น ๆ ว่า \"มันไม่ใช่ที่ที่ควรเข้าไปตอนดึก\" แล้วก็หยุด",
    },
    {
        "id": "afterthought",
        "opening": "เรื่องนี้เป็นประเภทที่ยิ่งนึกย้อนกลับไป ยิ่งรู้สึกว่ามีหลายจุดที่ตอนนั้นควรจะสังเกตได้ แต่ไม่มีใครทันคิด",
        "ordinary": "{name}เข้าไป{place}เพราะเรื่องธรรมดาเกี่ยวกับ{object} เท่านั้น ไม่ได้คิดว่าคืนนั้นจะกลายเป็นเรื่องที่จำไปอีกนาน",
        "local": "{witness}ไม่ได้ห้ามตรง ๆ แค่พูดทิ้งไว้ว่า {rule} แล้วเดินหนีไปเหมือนไม่อยากเป็นคนเล่าต่อ",
        "response": "{name}จึงยังทำธุระต่อเหมือนไม่มีอะไร แต่พอเห็น{object}หรือได้ยินเสียงแปลก ๆ ซ้ำ ๆ ก็เริ่มรู้สึกว่าบางอย่างมันไม่พอดีตั้งแต่แรกแล้ว",
        "ending": "หลังคืนดังกล่าว{name}ไม่กล้าพูดว่าตัวเองเห็นอะไรชัด ๆ แต่ทุกคนที่รู้เรื่องต่างบอกตรงกันว่าเขาเปลี่ยนไปมากตั้งแต่นั้น",
    },
    {
        "id": "community_memory",
        "opening": "คนในละแวกนั้นพูดถึง{place}แบบมีพิรุธมานาน แต่เรื่องของ{name}เป็นครั้งแรกที่มีคนยอมเล่าลำดับเหตุการณ์ทั้งหมดออกมา",
        "ordinary": "{time} {name}ซึ่งเป็น{role}ต้องไป{place}เพราะมีคนแจ้งว่าเห็น{object}ถูกทิ้งไว้ในจุดที่ผิดปกติ และไม่มีใครคนอื่นว่างไปดู",
        "local": "ก่อนหน้านั้น {witness}เคยบอกว่าเคยมีเหตุไม่ดีเกิดขึ้นแถวนั้น แต่ขอเพียงอย่างเดียวว่า {rule}",
        "response": "{name}พยายามจำรายละเอียดทุกอย่างเพื่อกลับมาเล่าให้คนอื่นฟัง เพราะตอนนั้น{name}ยังเชื่อว่าเรื่องผิดปกติต้องมีคำอธิบาย",
        "ending": "หลังเรื่องแพร่ออกไป คนในละแวกนั้นไม่ได้พูดมากขึ้น กลับเงียบกว่าเดิม เหมือนทุกคนรู้เรื่องนี้อยู่แล้วแต่ไม่อยากเป็นคนยืนยัน",
    },
    {
        "id": "late_return",
        "opening": "เป็นคืนที่{name}กลับช้ากว่าปกติเพียงนิดเดียว แต่ความต่างเพียงนิดนั้นทำให้{name}เจอสิ่งที่ไม่ควรเจอที่{place}",
        "ordinary": "ระหว่างทางกลับ{name}ต้องหยุดที่{place}เพราะมีคนขอให้ช่วยดู{object} ซึ่งดูเป็นเหตุผลธรรมดาจนไม่คิดจะโทรบอกใคร",
        "local": "{witness}เคยเล่าให้ฟังว่าหลังเวลาหนึ่ง อย่าอยู่แถวนั้นนาน และโดยเฉพาะ {rule}",
        "response": "ตอนแรก{name}เร่งทำทุกอย่างให้เสร็จ แต่เมื่อสิ่งผิดปกติเกิดขึ้น {name}กลับลังเลว่าควรหนีหรือควรช่วยคนที่เหมือนกำลังเดือดร้อน",
        "ending": "นับจากนั้น{name}พยายามกลับบ้านให้เร็วขึ้นเสมอ และไม่เคยตอบคำถามว่าในคืนนั้น{name}เห็นใครที่{place}",
    },
]


VISUAL_PROFILES = [
    "observational Thai night-film realism with neutral natural colors and restrained handheld energy",
    "precise architectural suspense with practical fluorescent light and deep layered backgrounds",
    "rain-soaked Thai location realism with wet reflections, controlled contrast and natural skin tones",
    "quiet rural nocturne with available moonlight, warm practical lamps and realistic exposure",
    "claustrophobic workplace realism with foreground machinery, narrow sightlines and practical work lights",
    "pre-dawn documentary realism with soft mist, subdued natural color and clear environmental detail",
    "old tungsten interior realism with dusty air, selective focus and believable low-light exposure",
    "surveillance-informed thriller realism with high corners and long-lens layers, without screen overlays",
]


CAMERA_GRAMMAR = {
    "eye_wide": "24mm eye-level wide shot",
    "low_wide": "28mm low-angle wide shot with strong foreground depth",
    "high_wide": "35mm high-corner wide shot looking diagonally across the real space",
    "profile": "50mm side-profile medium shot with the face visible in profile",
    "three_quarter": "65mm three-quarter medium close shot with a natural adult face",
    "object_insert": "85mm object-level insert close-up with the location still identifiable behind it",
    "overhead": "top-down evidence composition",
    "door_frame": "frame-within-a-frame shot through a doorway, service window or structural opening",
    "reflection": "layered reflection shot through wet glass or a dull reflective surface",
    "pov": "subjective point-of-view shot from the protagonist's eye line",
    "long_lens": "85mm long-lens shot with foreground obstruction and a deep background clue",
    "floor_level": "floor-level 28mm shot with the clue large in the foreground",
}


SCENE_CAMERA_OPTIONS = [
    ("eye_wide", "low_wide", "high_wide", "profile", "three_quarter", "object_insert", "door_frame", "reflection"),
    ("profile", "three_quarter", "door_frame", "low_wide", "pov"),
    ("object_insert", "profile", "three_quarter", "reflection", "long_lens"),
    ("eye_wide", "high_wide", "door_frame", "long_lens", "pov"),
    ("object_insert", "overhead", "floor_level", "pov", "long_lens"),
    ("profile", "three_quarter", "long_lens", "door_frame", "reflection"),
    ("object_insert", "floor_level", "overhead", "long_lens", "pov"),
    ("profile", "three_quarter", "reflection", "door_frame", "object_insert"),
    ("reflection", "profile", "three_quarter", "long_lens", "door_frame"),
    ("pov", "high_wide", "long_lens", "floor_level", "door_frame"),
    ("eye_wide", "high_wide", "object_insert", "floor_level", "long_lens"),
    ("overhead", "object_insert", "profile", "three_quarter", "door_frame"),
    ("three_quarter", "profile", "long_lens", "low_wide", "reflection"),
    ("profile", "low_wide", "door_frame", "high_wide", "pov"),
    ("overhead", "object_insert", "eye_wide", "floor_level", "high_wide"),
    ("eye_wide", "low_wide", "high_wide", "long_lens", "reflection", "object_insert"),
]


def build_experience_visuals(seed):
    setting = seed["_setting"]
    motif = seed["_motif"]
    place_visual = setting["visual"]
    role_visual = setting["role_visual"]
    object_visual = setting["object_visual"]
    ghost = motif["ghost"]
    visual_profile = seed["_visual_profile"]
    rng = random.Random(seed["_visual_nonce"])
    recent_cameras = []
    camera_counts = {}

    def choose_camera(scene_index, override_options=None):
        options = list(override_options or SCENE_CAMERA_OPTIONS[scene_index])
        eligible = [
            camera for camera in options
            if camera not in recent_cameras[-3:] and camera_counts.get(camera, 0) < 2
        ]
        if not eligible:
            eligible = [
                camera for camera in options
                if camera not in recent_cameras[-2:] and camera_counts.get(camera, 0) < 2
            ]
        if not eligible:
            eligible = [camera for camera in options if camera_counts.get(camera, 0) < 2]
        if not eligible:
            eligible = [camera for camera in options if camera not in recent_cameras[-2:]] or options
        camera = rng.choice(eligible)
        recent_cameras.append(camera)
        camera_counts[camera] = camera_counts.get(camera, 0) + 1
        return CAMERA_GRAMMAR[camera]

    opening_modes = [
        (
            "human_action",
            f"exactly one {role_visual} paused beside {object_visual} at {place_visual}; "
            "the adult face is visible in three-quarter profile and the person is reacting to the object, not walking",
        ),
        (
            "object_hook",
            f"{object_visual} dominates the foreground while the architecture of {place_visual} is unmistakable behind it; no people",
        ),
        (
            "location_hook",
            f"the distinctive entrance and working details of {place_visual} fill the frame; {object_visual} sits under one practical light; no people",
        ),
        (
            "threshold_hook",
            f"exactly one {role_visual} at the threshold of {place_visual}, face and both eyes readable in a three-quarter angle while looking toward {object_visual}",
        ),
        (
            "reflection_hook",
            f"a reflection in wet glass reveals {place_visual} and {object_visual}; no people and no human silhouette",
        ),
    ]
    blocked_opening_modes = set(seed.get("_blocked_opening_modes", ()))
    opening_candidates = [item for item in opening_modes if item[0] not in blocked_opening_modes]
    opening_mode, opening_action = rng.choice(opening_candidates or opening_modes)
    seed["_opening_mode"] = opening_mode
    opening_camera_options = {
        "human_action": ("profile", "three_quarter", "low_wide", "door_frame"),
        "object_hook": ("object_insert", "overhead", "floor_level", "long_lens"),
        "location_hook": ("eye_wide", "low_wide", "high_wide", "door_frame"),
        "threshold_hook": ("profile", "three_quarter", "door_frame", "long_lens"),
        "reflection_hook": ("reflection",),
    }

    actions = [
        opening_action,
        f"exactly one {role_visual} arriving at the identifiable entrance of {place_visual}, pausing in side or three-quarter view with face visible and a flashlight held low",
        f"exactly one {role_visual} listening to a phone beside the entrance of {place_visual}; {object_visual} remains visible; screen blank and unreadable",
        f"the empty interior of {place_visual} with {object_visual} at the exact work area described; environmental details dominate; no people",
        f"{object_visual} beside one fresh physical clue on the correct counter or floor inside {place_visual}; no people, no writing",
        f"exactly one {role_visual} checking the room from a side or three-quarter angle inside {place_visual}; one faint human-like shadow only in the far background",
        f"{object_visual} has moved closer within the same identifiable part of {place_visual}; no people and no unrelated props",
        f"exactly one {role_visual} taking a tense phone call inside {place_visual}, face visible in profile; empty space behind and no readable screen",
        f"exactly one {role_visual} facing a dirty reflective surface in {place_visual}; {ghost} appears only in the reflection, not as a second normal person",
        f"a repeating passage inside {place_visual} seen as a subjective or side-on composition; {object_visual} marks the far end; the passage itself is the subject",
        f"one practical light failing inside the clearly identifiable {place_visual}; {object_visual} unnaturally close in the foreground; no people",
        f"exactly one {role_visual} discovering old physical evidence beside {object_visual} inside {place_visual}; adult face in profile or three-quarter view; all papers blank",
        f"exactly one {role_visual} frozen in fear inside {place_visual}; {ghost} is a restrained distant background presence and not another living person",
        f"exactly one {role_visual} crossing the exit of {place_visual} laterally in full side profile with the face outline visible; {object_visual} remains in the interior",
        f"morning aftermath at the exact work area in {place_visual}; {object_visual} beside one abandoned personal belonging; no people",
        f"final haunting view of the distinctive {place_visual}; {ghost} is a tiny distant clue and {object_visual} is visible in a different foreground plane; no living people",
    ]

    visuals = []
    for index, action in enumerate(actions):
        opening_options = opening_camera_options[opening_mode] if index == 0 else None
        camera = choose_camera(index, opening_options)
        visuals.append(
            f"{camera}; {action}; {visual_profile}; single cinematic frame, natural colors, exact character count"
        )
    return visuals


def setting_title_object(setting):
    value = setting["object"].split("ที่", 1)[0].strip()
    return value[:18] or setting["object"][:18]


def short_place_reference(place):
    for token in ("ของ", "บน", "ใต้", "หลัง", "ริม", "ข้าง", "ท้าย", "หน้า", "เที่ยว", "จุด", "สถานี", "ห้อง", "ท่า", "ปั๊ม", "บ้าน", "คลัง", "หอ", "โรง", "ร้าน", "อู่"):
        if place.startswith(token):
            break
    candidates = [
        place.replace("ของที่ทำการไปรษณีย์เก่า", "ไปรษณีย์เก่า"),
        place.replace("บนถนนสายเก่า", ""),
        place.replace("ของโรงพยาบาลอำเภอเก่า", "โรงพยาบาลเก่า"),
        place.replace("ท้ายหมู่บ้าน", ""),
        place.replace("ของโรงภาพยนตร์ปิดกิจการ", "โรงหนังเก่า"),
        place.replace("หลังตลาดเช้า", ""),
        place.replace("ริมแม่น้ำ", ""),
    ]
    for candidate in candidates:
        candidate = candidate.strip()
        if candidate and len(candidate) < len(place):
            return candidate
    return place


def short_object_reference(object_name):
    aliases = {
        "ตั๋วเที่ยวสุดท้ายที่ยังเปียกอยู่": "ตั๋วเที่ยวสุดท้าย",
        "เหรียญโดยสารที่เย็นจัดเหมือนแช่น้ำแข็ง": "เหรียญโดยสาร",
        "ป้ายชื่อผู้ป่วยที่ไม่มีชื่อพิมพ์อยู่": "ป้ายชื่อผู้ป่วย",
        "มาตรวัดน้ำที่เข็มหมุนถอยหลังเอง": "มาตรวัดน้ำ",
        "ฟิล์มม้วนสุดท้ายที่ไม่มีชื่อเรื่อง": "ฟิล์มม้วนสุดท้าย",
        "สมุดส่งของที่หน้ากระดาษเปียกทั้งเล่ม": "สมุดส่งของ",
        "เชือกตีระฆังที่เปียกเหมือนเพิ่งถูกจับ": "เชือกตีระฆัง",
        "บัตรลงเวลาที่เจาะรูเพิ่มขึ้นทุกคืน": "บัตรลงเวลา",
        "กุญแจเรือที่มีเชือกผูกด้วยผมเปียก": "กุญแจเรือ",
        "กล่องพัสดุที่จ่าหน้าถึงคนตาย": "กล่องพัสดุ",
        "ปุ่มลิฟต์สำรองที่มีรอยนิ้วมือเปียก": "ปุ่มลิฟต์สำรอง",
        "นาฬิกาพกที่หยุดตรงเวลาขบวนสุดท้าย": "นาฬิกาพก",
        "ใบเสร็จเติมน้ำมันที่ยังอุ่นอยู่": "ใบเสร็จเติมน้ำมัน",
        "กุญแจห้องพักที่ไม่มีหมายเลข": "กุญแจห้องพัก",
        "เทปบันทึกเสียงที่มีลมหายใจอยู่ท้ายม้วน": "เทปบันทึกเสียง",
        "รองเท้าหนังคู่เดิมที่เปียกโคลนทุกคืน": "รองเท้าหนัง",
        "กระสอบข้าวที่มีรอยมือกดจากข้างใน": "กระสอบข้าว",
        "ซองยาที่มีชื่อคนไข้ถูกลบออกหมด": "ซองยา",
        "บัตรยืมหนังสือที่มีลายเซ็นเพิ่มเอง": "บัตรยืมหนังสือ",
        "ถุงหลักฐานที่มีโทรศัพท์สั่นอยู่ข้างใน": "ถุงหลักฐาน",
        "บัตรจอดรถที่มีเวลาออกเป็นวันพรุ่งนี้": "บัตรจอดรถ",
        "หน้ากากละครที่หันมามองคนละทางทุกครั้ง": "หน้ากากละคร",
        "ตั๋วเรือฉีกครึ่งที่กลับมาติดกันเอง": "ตั๋วเรือ",
    }
    if object_name in aliases:
        return aliases[object_name]
    replacements = [
        ("ที่ยังอุ่นอยู่", ""),
        ("ที่ยังค้างอยู่", ""),
        ("ที่ไม่มีชื่อพิมพ์อยู่", ""),
        ("ที่จ่าหน้าถึงคนตาย", "พัสดุนั้น"),
        ("ที่เข็มหมุนถอยหลังเอง", "มาตรวัดน้ำ"),
        ("ที่มีลมหายใจอยู่ท้ายม้วน", "เทปบันทึกเสียง"),
        ("ที่มีรอยมือเปียก", "ผ้าคลุมกระจก"),
    ]
    value = object_name
    for old, new in replacements:
        value = value.replace(old, new)
    value = re.sub(r"\s+", " ", value).strip()
    return compact_object_title(value)


def derive_setting_details(setting):
    place = setting["place"]
    if "โรงละคร" in place:
        return {
            "sensory": "กลิ่นฝุ่นผสมกลิ่นผ้าเก่าที่อับอยู่หลังฉาก",
            "clue": "เศษสีฉากหลุดเป็นทางไปถึงมุมมืด",
            "rule": "ห้ามเปิดม่านหลังเวทีคนเดียว",
            "time": "หลังโรงละครปิดได้ไม่นาน",
        }
    if "ปั๊มน้ำมัน" in place:
        return {
            "sensory": "กลิ่นน้ำมันเก่าปนลมอับจากห้องเก็บของ",
            "clue": "ใบเสร็จยับ ๆ ที่พิมพ์เวลาเกินจากที่ปั๊มปิด",
            "rule": "ห้ามหันไปดูหัวจ่ายที่ไม่มีรถจอด",
            "time": "หลังปั๊มปิดไปนานแล้ว",
        }
    if "ไปรษณีย์" in place or "พัสดุ" in place:
        return {
            "sensory": "กลิ่นกระดาษชื้นกับผ้าใบกระสอบเก่า",
            "clue": "พัสดุหล่นอยู่ใบหนึ่งทั้งที่ไม่มีชื่อผู้ส่ง",
            "rule": "ห้ามตอบถ้ามีคนเรียกจากด้านในห้องคัดแยก",
            "time": "หลังที่ทำการปิดเงียบไปแล้ว",
        }
    if "แพ" in place or "ท่าเรือ" in place:
        return {
            "sensory": "กลิ่นน้ำค้างแม่น้ำกับเชือกเปียกที่ชื้นค้างอยู่",
            "clue": "รอยน้ำเป็นทางเหมือนมีใครเดินขึ้นมาจากท่า",
            "rule": "ห้ามเรียกชื่อใครตรงท่าน้ำหลังเที่ยงคืน",
            "time": "หลังเรือเที่ยวสุดท้ายออกไปแล้ว",
        }
    if "โรงพยาบาล" in place or "คลินิก" in place:
        return {
            "sensory": "กลิ่นยาฆ่าเชื้อจาง ๆ ปนลมเย็นจากห้องปิด",
            "clue": "ป้ายชื่อคนไข้ตกอยู่ทั้งที่ไม่ควรมีใครเข้ามาแล้ว",
            "rule": "ห้ามตอบถ้ามีคนเรียกจากเตียงที่ว่างอยู่",
            "time": "หลังเวรดึกเริ่มเงียบลง",
        }
    if "วัด" in place or "หอระฆัง" in place:
        return {
            "sensory": "กลิ่นธูปเก่ากับลมเย็นจากลานวัดที่ไม่มีคน",
            "clue": "คราบน้ำเป็นรอยมืออยู่ตรงเสาไม้",
            "rule": "ห้ามขานชื่อคนที่ได้ยินจากในวัด",
            "time": "คืนวันพระใหญ่",
        }
    if "รถไฟ" in place:
        return {
            "sensory": "กลิ่นสนิมกับเสียงเหล็กกระทบกันเบา ๆ จากทางมืด",
            "clue": "เศษกรวดถูกเขี่ยเป็นทางไปถึงรางเก่า",
            "rule": "ห้ามเดินตามเสียงหวีดที่ไม่มีขบวนรถ",
            "time": "หลังขบวนสุดท้ายผ่านไปแล้ว",
        }
    if "ตลาด" in place:
        return {
            "sensory": "กลิ่นของค้างคืนกับพื้นเปียกที่ยังไม่แห้ง",
            "clue": "รอยเท้าเปียกเดินสวนทางกับทางออก",
            "rule": "ห้ามตอบถ้ามีคนถามหาของที่ไม่มีร้านไหนขายแล้ว",
            "time": "หลังตลาดวายไปนานแล้ว",
        }
    if "โรงสี" in place or "โรงน้ำแข็ง" in place or "สูบน้ำ" in place:
        return {
            "sensory": "เสียงเครื่องเก่าที่เหมือนยังเดินอยู่ทั้งที่ปิดไฟหมดแล้ว",
            "clue": "คราบเปียกใหม่ ๆ อยู่ตรงพื้นแห้ง",
            "rule": "ห้ามเปิดสวิตช์ตัวสุดท้ายในห้องเครื่อง",
            "time": "ดึกมากจนไม่มีคนงานเหลืออยู่แล้ว",
        }
    if "หอสมุด" in place:
        return {
            "sensory": "กลิ่นกระดาษเก่ากับฝุ่นอับจากชั้นในสุด",
            "clue": "บัตรยืมเก่าถูกเสียบค้างอยู่ในเล่มที่ไม่มีใครแตะ",
            "rule": "ห้ามอ่านชื่อคนยืมคนสุดท้ายออกเสียง",
            "time": "หลังห้องอ่านหนังสือปิดไฟหมดแล้ว",
        }
    return {
        "sensory": "ลมเย็นแปลก ๆ กับความเงียบที่กดลงมาจนได้ยินแต่เสียงตัวเอง",
        "clue": "รอยเปียกใหม่ ๆ อยู่ในจุดที่ไม่ควรมีใครผ่านมา",
        "rule": "ห้ามหันกลับไปมองหลังได้ยินเสียงครั้งที่สาม",
        "time": "เกือบตีสาม",
    }


def experience_scene_specs(seed):
    existing = seed.get("_scene_specs")
    if existing:
        return existing

    setting = seed["_setting"]
    motif = seed["_motif"]
    frame = seed["_frame"]
    name = seed["name"]
    place = setting["place"]
    place_short = short_place_reference(place)
    place_visual = setting["visual"]
    role = setting["role"]
    role_visual = setting["role_visual"]
    object_name = setting["object"]
    object_short = short_object_reference(object_name)
    object_visual = setting["object_visual"]
    witness = setting["witness"]
    ghost = motif["ghost"]
    time_text = seed["time"]
    sensory = seed["sensory"]
    clue = seed["clue"]
    rule = seed["rule"]

    lines = [
        frame["opening"].format(name=name, place=place_short, object=object_short, role=role, time=time_text, witness=witness, rule=rule),
        frame["ordinary"].format(name=name, place=place_short, object=object_short, role=role, time=time_text, witness=witness, rule=rule),
        frame["local"].format(name=name, place=place_short, object=object_short, role=role, time=time_text, witness=witness, rule=rule),
        f"พอ{name}เข้าไปถึง{place_short} ที่นั่นเงียบผิดปกติ จน{sensory}ชัดขึ้นเหมือนมีใครคอยฟังทุกก้าว",
        f"ใกล้{object_short}มี{clue} เหมือนถูกวางไว้ให้{name}เห็นโดยตั้งใจ",
        f"{motif['manifestation'].format(place=place_short, object=object_short, name=name)} คราวนี้{name}รู้แล้วว่าไม่ใช่เรื่องแกล้งกัน",
        frame["response"].format(name=name, place=place_short, object=object_short, role=role, time=time_text, witness=witness, rule=rule),
        f"เมื่อ{name}มองกระจกอีกด้าน {ghost}ยืนอยู่ในเงาสะท้อน ทั้งที่ตรงนั้นไม่มีใคร",
        f"{name}วาง{object_short}แล้วรีบออก แต่ทางเดิมกลับพาวนมาที่จุดเดิมทุกครั้ง",
        f"ทุกครั้งที่วนกลับมา ไฟดับเพิ่มหนึ่งดวง และ{object_short}ขยับเข้ามาใกล้มือเอง",
        f"{witness}ยอมบอกว่าเคยมีคนพยายามเอา{object_short}ออกจาก{place_short} แล้วคนนั้นไม่เคยกลับมา",
        f"{motif['reveal'].format(place=place_short, object=object_short, name=name)} นั่นคือเหตุผลที่มันเลือก{name}",
        f"{name}ทำตามคำเตือนว่า {rule} แล้วเดินออกไปโดยไม่หันกลับ แม้เสียงเรียกชื่อจะดังอยู่ข้างหลัง",
        f"เช้าวันต่อมา {witness}พบ{object_short}อยู่ที่เดิม แต่ข้างกันมีของใช้ของ{name}เพิ่มมาอีกชิ้น",
        frame["ending"].format(name=name, place=place_short, object=object_short, role=role, time=time_text, witness=witness, rule=rule),
    ]
    visuals = build_experience_visuals(seed)
    specs = [
        {"narration": narration, "visual": visual, "imagePrompt": visual}
        for narration, visual in zip(lines, visuals)
    ]
    seed["_scene_specs"] = specs
    return specs


def make_coherent_seed(server, original_make_seed, brief, avoid=None):
    seed = original_make_seed(brief, avoid=avoid)
    avoid = avoid or {}
    blocked_places = avoid.get("places", set())
    blocked_patterns = avoid.get("patterns", set())
    blocked_frames = avoid.get("frames", set())
    blocked_profiles = avoid.get("profiles", set())
    blocked_opening_modes = avoid.get("openingModes", set())
    setting_candidates = [item for item in EXPERIENCE_SETTINGS if item["place"] not in blocked_places]
    if brief.strip():
        matched = [item for item in EXPERIENCE_SETTINGS if item["place"] in brief]
        setting_candidates = matched or setting_candidates
    setting = random.choice(setting_candidates or EXPERIENCE_SETTINGS)
    motif_candidates = [item for item in EXPERIENCE_MOTIFS if item["id"] not in blocked_patterns]
    motif = random.choice(motif_candidates or EXPERIENCE_MOTIFS)
    frame_candidates = [item for item in REFERENCE_NARRATIVE_FRAMES if item["id"] not in blocked_frames]
    frame = random.choice(frame_candidates or REFERENCE_NARRATIVE_FRAMES)
    name = random.choice(THAI_NAMES)
    details = derive_setting_details(setting)
    visual_profile_candidates = [item for item in VISUAL_PROFILES if item not in blocked_profiles]
    visual_profile = random.choice(visual_profile_candidates or VISUAL_PROFILES)
    visual_nonce = f"{random.getrandbits(64):016x}"
    title = motif["title"].format(place=setting["place"], object_title=setting_title_object(setting))
    pattern = {"name": motif["id"]}

    seed.update({
        "title": title,
        "name": name,
        "place": (setting["place"], setting["visual"]),
        "protagonist": setting["role"],
        "object": setting["object"],
        "ghost": motif["ghost"],
        "event": motif["manifestation"].format(place=setting["place"], object=setting["object"], name=name),
        "twist": motif["reveal"].format(place=setting["place"], object=setting["object"], name=name),
        "witness": setting["witness"],
        "sensory": details["sensory"],
        "clue": details["clue"],
        "rule": details["rule"],
        "time": details["time"],
        "final_image": setting["object"],
        "pattern": pattern,
        "_experience": True,
        "_setting": setting,
        "_motif": motif,
        "_frame": frame,
        "_visual_profile": visual_profile,
        "_visual_nonce": visual_nonce,
        "_blocked_opening_modes": blocked_opening_modes,
    })
    return seed


def story_lines(server, original_story_lines, seed, mode):
    if seed.get("_experience"):
        return [scene["narration"] for scene in experience_scene_specs(seed)]

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
        target_seconds = 148 if mode == "short" else 420
        if seed.get("_experience"):
            specs = experience_scene_specs(seed)
            duration = max(6, round(target_seconds / len(specs)))
            scenes = [
                {
                    "number": index,
                    "beat": "เสียงเล่าเรื่องต่อเนื่อง",
                    "duration": duration,
                    "narration": clean_story_line(spec["narration"], seed),
                    "visual": spec["visual"],
                    "imagePrompt": spec["imagePrompt"],
                }
                for index, spec in enumerate(specs, start=1)
            ]
        else:
            lines = server.story_lines(seed, mode)
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
                "narrativeFrame": seed.get("_frame", {}).get("id", ""),
                "visualProfile": seed.get("_visual_profile", "natural Thai horror realism"),
                "visualNonce": seed.get("_visual_nonce", f"{random.getrandbits(64):016x}"),
                "openingMode": seed.get("_opening_mode", "location_hook"),
            },
            "targetSeconds": target_seconds,
            "scenes": scenes,
            "script": "\n\n".join(scene["narration"] for scene in scenes),
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
            "follow the camera angle and composition specified for this scene, location and story action dominate, "
            "one adult person at most unless the scene explicitly says none, use profile or three-quarter faces when a person appears, "
            "keep the specified face angle and action, hands mostly hidden, realistic body proportions"
        )
        return f"{visual}, {stability}"

    def stable_ai_image_prompt(scene, story, size):
        if scene.get("imagePrompt"):
            width, height = size
            aspect = "vertical 9:16 composition, 1080x1920" if height > width else "wide horizontal 16:9 composition, 1920x1080"
            seed = story.get("seed", {})
            return " ".join([
                "Photorealistic Thai supernatural horror movie still.",
                aspect + ".",
                "Depict this exact scene only:", scene["imagePrompt"] + ".",
                f"Story-specific visual language: {seed.get('visualProfile', 'natural Thai horror realism')}.",
                "Real Thai horror film frame, natural colors, restrained practical lighting, realistic adult body proportions.",
                "Keep the exact location, object, action and character count from the scene description.",
                "Honor the specified lens, viewpoint, face angle and subject action exactly.",
                "No children, no unrelated people, no duplicate people, no unrelated house or hospital, no readable writing.",
                "One continuous image only, no collage. No text, subtitles, letters, numbers, watermark, logo, cartoon, anime, distorted faces or deformed bodies.",
            ])
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
