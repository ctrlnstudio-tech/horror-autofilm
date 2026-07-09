from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import asyncio
import hashlib
import html
import os
import json
import math
import random
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"
PORT = int(os.environ.get("PORT", "4200"))
HOST = os.environ.get("HOST", "0.0.0.0")
try:
    import imageio_ffmpeg
except Exception:
    imageio_ffmpeg = None

FFMPEG = shutil.which("ffmpeg") or (imageio_ffmpeg.get_ffmpeg_exe() if imageio_ffmpeg else "/opt/homebrew/bin/ffmpeg")
FFPROBE = shutil.which("ffprobe") or FFMPEG
SAY = shutil.which("say") or "/usr/bin/say"
EDGE_TTS = shutil.which("edge-tts") or shutil.which("python3")
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Thonburi.ttc")
FONT_FALLBACKS = [
    FONT_PATH,
    Path("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
VOICE = "Kanya (Enhanced)"

PLACES = [
    ("คลังของหายใต้ทางด่วน", "old warehouse of lost belongings under a Thai expressway"),
    ("ห้องพักท้ายรีสอร์ต", "old Thai resort room at the end of a narrow walkway"),
    ("คลินิกกะดึก", "closed Thai night clinic with empty waiting chairs"),
    ("ร้านวิดีโอเก่า", "old Thai VHS rental store with dusty shelves"),
    ("ลิฟต์โรงพยาบาล", "old hospital elevator with flickering floor numbers"),
    ("ห้องเก็บแฟ้มเทศบาล", "municipal archive room filled with dusty case files"),
    ("บ้านเช่าข้างทางรถไฟ", "old rental house beside a railway track"),
    ("โรงหนังปิดตาย", "abandoned cinema with torn red seats"),
    ("ตู้โทรศัพท์หน้าวัด", "abandoned public phone booth in front of a Thai temple"),
    ("ห้องเช่าเหนือร้านยา", "rental room above an old pharmacy"),
    ("บันไดหนีไฟชั้นสิบสาม", "fire escape stairwell on the thirteenth floor"),
    ("ห้องเก็บชุดไทย", "storage room full of old Thai traditional costumes"),
]

PROTAGONISTS = [
    "พนักงานกะดึก",
    "ไรเดอร์ส่งของ",
    "ช่างซ่อมกล้องวงจรปิด",
    "พยาบาลเวรดึก",
    "แม่บ้านโรงแรม",
    "คนเฝ้าโกดัง",
    "เจ้าหน้าที่เวชระเบียน",
    "ยามหมู่บ้าน",
    "นักศึกษาฝึกงาน",
    "คนขับรถตู้",
]

OBJECTS = [
    "กุญแจที่ไม่มีหมายเลข",
    "เทปวิดีโอที่ถูกเขียนว่าอย่ากรอกลับ",
    "รูปถ่ายที่มีเงาเพิ่มขึ้นทุกครั้ง",
    "สมุดลงชื่อที่มีชื่อคนตาย",
    "กล่องยาเก่าที่ฉลากถูกขูดออก",
    "พวงกุญแจที่มีกลิ่นธูปติดอยู่",
    "แฟ้มคดีที่หน้าสุดท้ายหายไป",
    "บัตรคิวที่ออกเป็นเลขเดิมทุกครั้ง",
]

GHOSTS = [
    "ผู้หญิงผมเปียกที่พูดด้วยเสียงของคนรู้จัก",
    "ชายแก่ที่เห็นได้เฉพาะในกระจก",
    "เงาคนไข้ที่ลากสายน้ำเกลือไปตามพื้น",
    "คนขายตั๋วที่ตายก่อนโรงหนังปิด",
    "หญิงใส่ชุดไทยที่หันหลังตลอดเวลา",
    "เสียงผู้ชายที่อยู่ในลำโพงแต่ไม่มีตัว",
    "เงาคนเฝ้าศพที่เดินตามเสียงกุญแจ",
]

EVENTS = [
    "ไฟทั้งชั้นดับพร้อมกัน แต่มีห้องเดียวที่ยังสว่าง",
    "กล้องวงจรปิดย้อนหลังไปเห็นเหตุการณ์ที่ยังไม่เกิด",
    "ประตูล็อกจากด้านใน ทั้งที่ไม่มีใครอยู่ในห้อง",
    "เสียงเคาะดังมาจากผนังแทนที่จะดังจากประตู",
    "ชื่อของตัวเอกไปปรากฏในสมุดลงชื่อเมื่อสิบปีก่อน",
    "ลิฟต์ขึ้นไปชั้นที่ไม่มีอยู่จริง",
    "โทรศัพท์โทรเข้ามาจากเบอร์ของสถานที่เดียวกัน",
]

TWISTS = [
    "สุดท้ายพบว่าสถานที่นั้นปิดตายมาตั้งแต่ก่อนวันที่ตัวเอกจำได้",
    "ชื่อผู้แจ้งเหตุคนแรกคือชื่อเดียวกับตัวเอก",
    "ภาพวงจรปิดเผยว่าตัวเอกเดินเข้าไปคนเดียว แต่ตอนออกมามีใครบางคนเดินตามหลัง",
    "ของต้องห้ามไม่ได้ถูกเก็บไว้เพื่อกันคนเข้า แต่เพื่อกันบางอย่างไม่ให้ออกมา",
    "เสียงที่คอยเตือนมาตลอดคือเสียงของตัวเอกจากคืนสุดท้าย",
    "พอทุกอย่างจบ ตัวเอกพบว่าตัวเองกลายเป็นชื่อถัดไปในแฟ้มคดี",
]

PLACE_ROOTS = [
    ("ห้องล้างฟิล์ม", "old photo darkroom"),
    ("ห้องจ่ายยา", "old pharmacy dispensing room"),
    ("ห้องเก็บหุ่นลองเสื้อ", "old mannequin storage room"),
    ("ห้องซักผ้า", "deserted laundry room"),
    ("ห้องดับจิต", "old morgue room"),
    ("ห้องรับฝากของ", "lost property counter"),
    ("ห้องเครื่องเสียง", "old sound equipment room"),
    ("ห้องฉายหนัง", "abandoned projection room"),
    ("ห้องเก็บบัตรคิว", "old queue ticket storage room"),
    ("ห้องเก็บรองเท้า", "old shoe storage room"),
    ("ห้องพักครู", "old teacher lounge"),
    ("ห้องบัญชี", "old accounting room"),
    ("ห้องน้ำชั้นลอย", "mezzanine restroom"),
    ("ทางเดินหลังร้าน", "service corridor behind a shop"),
    ("โกดังลังไม้", "wooden crate warehouse"),
    ("ศาลารอรถ", "deserted roadside bus shelter"),
    ("ป้อมยาม", "old security guard booth"),
    ("ห้องเช่าใต้หลังคา", "attic rental room"),
    ("ห้องเก็บผ้าปูเตียง", "linen storage room"),
    ("ประตูเหล็กท้ายอาคาร", "rear metal door of an old building"),
    ("บ่อน้ำปิดตาย", "sealed old water well"),
    ("โรงอาหารร้าง", "abandoned cafeteria"),
    ("แผงพระเก่า", "old amulet stall"),
    ("ร้านถ่ายเอกสาร", "old copy shop"),
    ("ร้านซ่อมนาฬิกา", "old watch repair shop"),
    ("ตู้ล็อกเกอร์", "old locker room"),
    ("บ้านพักคนงาน", "worker dormitory"),
    ("หอพักริมคลอง", "canal-side dormitory"),
    ("คลังเวชภัณฑ์", "medical supply storage"),
    ("ห้องเก็บของวัด", "temple storage room"),
]

PLACE_CONTEXTS = [
    ("หลังตลาดเก่า", "behind an old Thai market"),
    ("ใต้สะพานลอย", "under a pedestrian bridge"),
    ("ข้างทางรถไฟ", "beside a railway track"),
    ("ในซอยตัน", "inside a dead-end alley"),
    ("หลังโรงพยาบาล", "behind an old hospital"),
    ("ชั้นใต้ดินของตึกพาณิชย์", "in the basement of a commercial building"),
    ("ริมคลองน้ำดำ", "beside a dark canal"),
    ("ท้ายรีสอร์ตปิดกิจการ", "at the back of a closed resort"),
    ("ข้างเมรุวัด", "near a temple crematorium"),
    ("บนชั้นลอยที่ไม่มีป้ายบอกทาง", "on an unsigned mezzanine floor"),
    ("หลังสถานีขนส่ง", "behind an old bus station"),
    ("ในโรงงานที่หยุดเดินเครื่อง", "inside a closed factory"),
    ("ข้างลานจอดรถร้าง", "beside an abandoned parking lot"),
    ("ใต้แฟลตเก่า", "under an old apartment block"),
    ("หลังคลินิกเวรดึก", "behind a late-night clinic"),
]

PROTAGONISTS += [
    "เจ้าหน้าที่รับฝากของ", "ช่างไฟฉุกเฉิน", "คนล้างฟิล์ม", "พนักงานโรงรับจำนำ",
    "คนคุมห้องเครื่อง", "คนเก็บค่าเช่า", "พนักงานร้านสะดวกซื้อ", "เจ้าของร้านซ่อมนาฬิกา",
    "คนจัดชั้นเอกสาร", "ช่างแอร์", "พนักงานล้างรถ", "คนเฝ้าลานจอดรถ",
    "พนักงานเคาน์เตอร์โรงแรม", "ช่างทำกุญแจ", "คนส่งเวชภัณฑ์", "เจ้าหน้าที่ธุรการ",
]

OBJECTS += [
    "ม้วนฟิล์มที่ถ่ายรูปหลังจากเจ้าของตายแล้ว",
    "นาฬิกาข้อมือที่เดินถอยหลัง",
    "เสื้อกันฝนที่เปียกตลอดเวลา",
    "ตลับเทปเสียงที่อัดเสียงคนหลับ",
    "ใบเสร็จที่ออกวันที่พรุ่งนี้",
    "ตุ๊กตาไม้ที่หันหน้าเองได้",
    "กุญแจห้องที่ไม่มีอยู่ในแปลนอาคาร",
    "ซองจดหมายที่ไม่มีชื่อผู้ส่ง",
    "ไฟฉายที่ส่องเห็นคนละทางกับสายตา",
    "กล่องรับฝากที่มีเสียงหายใจอยู่ข้างใน",
    "ผ้าคลุมกระจกที่มีรอยมือเปียก",
    "บัตรพนักงานของคนที่หายตัวไป",
]

GHOSTS += [
    "ร่างผู้ใหญ่ตัวเล็กผิดรูปที่เดินถอยหลังในเงามืด",
    "หญิงชราที่นับเลขซ้ำอยู่หลังประตู",
    "เงาคนใส่เสื้อกันฝนยืนเปียกทั้งที่ไม่มีฝน",
    "คนไม่มีหน้าในชุดพนักงานเก่า",
    "เสียงแม่ที่เรียกชื่อคนผิดซ้ำๆ",
    "ชายในรูปถ่ายที่ค่อยๆ หันหน้ามามอง",
    "ผู้หญิงที่เห็นแค่ครึ่งตัวตรงบานกระจก",
    "เงาดำที่เดินตามไฟฉายแต่ไม่แตะพื้น",
    "คนไข้เก่าที่ถามหาห้องของตัวเองทุกคืน",
]

EVENTS += [
    "ไฟฉายส่องไปทางหนึ่ง แต่เงาของตัวเอกหันไปอีกทาง",
    "เสียงประกาศเรียกชื่อคนที่ยังไม่เข้ามาในอาคาร",
    "กล่องรับฝากสั่นเหมือนมีคนเคาะจากข้างใน",
    "กลิ่นธูปแรงขึ้นทุกครั้งที่เดินเข้าใกล้ของชิ้นนั้น",
    "พื้นเปียกเป็นรอยเท้าเดินสวนทางกับตัวเอก",
    "เสียงลิ้นชักเปิดปิดเองตามจังหวะหายใจ",
    "นาฬิกาทุกเรือนหยุดพร้อมกันที่เวลาตายของใครบางคน",
    "กระจกสะท้อนห้องเดิมแต่ไม่มีตัวเอกอยู่ในนั้น",
    "วิทยุเก่าพูดประโยคเดียวกับที่ตัวเอกกำลังคิด",
]

TWISTS += [
    "คนที่โทรมาขอความช่วยเหลือไม่เคยมีตัวตนในทะเบียนคนเป็น",
    "ของที่คิดว่าเก็บมาได้ ความจริงเป็นของที่ตัวเอกเคยเอาไปทิ้งเองเมื่อหลายปีก่อน",
    "สถานที่นั้นไม่ได้หลอกคนแปลกหน้า แต่มันเลือกเฉพาะคนที่เคยลืมความผิดของตัวเอง",
    "ภาพสุดท้ายจากกล้องไม่ได้ถ่ายอดีตหรืออนาคต แต่มันถ่ายช่วงเวลาหลังจากตัวเอกตายไปแล้ว",
    "ทุกคนที่บอกว่าไม่รู้เรื่อง ความจริงเคยรอดออกมาได้ด้วยการส่งคนใหม่เข้าไปแทน",
    "ประตูที่ห้ามเปิดไม่ได้พาเข้าไปเจอผี แต่มันพาออกไปยังคืนที่ไม่มีใครควรรอดกลับมา",
]

TIMES = ["ตีหนึ่งสิบเจ็ดนาที", "เกือบตีสาม", "หลังร้านปิดสิบห้านาที", "คืนฝนตกหนัก", "คืนไฟดับทั้งซอย", "เช้ามืดก่อนฟ้าสาง", "คืนวันพระใหญ่", "คืนที่ลมแรงผิดปกติ"]
WITNESSES = ["ลุงยามหน้าอาคาร", "แม่ค้าข้าวแกงฝั่งตรงข้าม", "คนขับวินที่ไม่กล้าดับเครื่อง", "พนักงานเก่าที่ลาออกไปแล้ว", "พระเวรหน้าวัด", "แม่บ้านที่ไม่ยอมขึ้นชั้นบน"]
SENSORY_DETAILS = ["กลิ่นธูปเก่าปนกลิ่นน้ำขัง", "เสียงน้ำหยดเหมือนมีใครนับเวลา", "ลมเย็นที่พัดออกมาจากห้องปิด", "กลิ่นยาฆ่าเชื้อจางๆ เหมือนโรงพยาบาลเก่า", "เสียงรองเท้าลากช้าๆ หลังผนัง", "เสียงวิทยุแตกพร่าที่ไม่มีใครเปิด"]
CLUES = ["รอยนิ้วมือเปียกบนฝุ่นแห้ง", "รูปถ่ายที่มีเงาเพิ่มขึ้นหนึ่งคน", "เลขห้องที่ถูกขูดทิ้งจากแผนผัง", "ใบเสร็จที่พิมพ์เวลาหลังจากเหตุการณ์จบ", "รอยเท้าที่หยุดตรงหน้ากล้อง", "ชื่อคนตายในสมุดลงเวลา"]
RULES = ["ห้ามตอบถ้ามีคนเรียกจากด้านใน", "ห้ามหันกลับไปมองหลังได้ยินเสียงครั้งที่สาม", "ห้ามเอาของชิ้นนั้นออกจากอาคาร", "ห้ามเปิดไฟดวงสุดท้ายในทางเดิน", "ห้ามอ่านข้อความที่อยู่หลังรูปถ่าย", "ห้ามพูดชื่อสถานที่หลังเที่ยงคืน"]
FINAL_IMAGES = ["ไฟดวงเดียวที่ติดอยู่ลึกสุดทางเดิน", "ประตูที่เปิดแง้มไว้แค่พอเห็นเงาคนยืนรอ", "กล้องวงจรปิดที่ยังบันทึกภาพทั้งที่ไม่มีไฟ", "รอยเท้าเปียกคู่ใหม่หน้าห้อง", "เสียงประกาศเรียกชื่อเดิมซ้ำจนเช้า", "ของต้องห้ามที่กลับมาอยู่บนโต๊ะตัวเดิม"]

STORY_PATTERNS = [
    {
        "name": "ของต้องห้ามเลือกเจ้าของ",
        "beats": [
            "ก่อนจะเล่าเรื่องนี้ ต้องบอกไว้ก่อนว่า {place} ไม่ใช่ที่ที่คนแถวนั้นชอบพูดถึงตอนกลางคืน เพราะทุกครั้งที่มีคนเอ่ยชื่อ มักจะมีเสียงบางอย่างตอบกลับมาจากที่ว่างเปล่า",
            "{time} {protagonist} ถูกเรียกให้เข้าไปเอา {object} ออกมา โดยมีเหตุผลธรรมดามากจนไม่มีใครคิดว่ามันจะกลายเป็นเรื่องใหญ่",
            "ทันทีที่เปิดประตูเข้าไป สิ่งแรกที่สัมผัสได้คือ {sensory} และความเงียบที่เหมือนมีคนทั้งอาคารกำลังกลั้นหายใจอยู่พร้อมกัน",
            "ของชิ้นนั้นวางอยู่ตรงจุดที่ไม่ควรอยู่ได้เลย ข้างๆ มี {clue} เหมือนมีใครตั้งใจทิ้งไว้ให้รู้ว่าคืนนี้ไม่ใช่ครั้งแรก",
            "{event} ทำให้ตัวเอกเริ่มเข้าใจว่าที่นี่ไม่ได้เงียบเพราะไม่มีคน แต่เงียบเพราะทุกคนรู้ว่าห้ามส่งเสียง",
            "ตอนจะหยิบของออกมา เสียงของ {ghost} ดังขึ้นเบามากจากด้านหลัง เหมือนพูดติดปากว่าอย่าเอากลับไป",
            "พอถาม {witness} กลับได้คำเตือนสั้นๆ ว่า {rule} แล้วคืนนั้นห้ามกลับไปคนเดียวเด็ดขาด",
            "แต่ของต้องห้ามกลับมาอยู่ในมือของตัวเอกอีกครั้ง ทั้งที่เพิ่งวางทิ้งไว้ และคราวนี้มันมีรอยอุ่นเหมือนเพิ่งถูกใครกำไว้",
            "{twist} ตัวเอกถึงรู้ว่าตัวเองไม่ได้เจอของต้องห้ามโดยบังเอิญ แต่ถูกเลือกไว้ตั้งแต่ก่อนเดินเข้าไปแล้ว",
            "หลังจากคืนนั้น {final_image} ยังปรากฏอยู่ที่ {place} เสมอ และไม่มีใครกล้าถามอีกเลยว่าเจ้าของของชิ้นนั้นเป็นใครกันแน่",
        ],
        "middles": [
            "ระหว่างทางกลับ ตัวเอกได้ยินเสียงวัตถุในกระเป๋าขยับเองช้าๆ ทุกครั้งที่รถผ่านไฟแดง และเมื่อเปิดดู มันกลับวางอยู่ในท่าเดิมเหมือนมีคนจัดไว้",
            "วันถัดมา ตัวเอกพยายามเอาของไปคืน แต่ถนนทุกเส้นวนกลับมาที่ {place} เหมือนเมืองทั้งเมืองถูกพับให้เหลือทางออกทางเดียว",
            "{witness} เล่าว่าเมื่อหลายปีก่อนเคยมีคนเก็บของชิ้นเดียวกันกลับบ้าน และหลังจากนั้นบ้านทั้งหลังได้ยินเสียงคนเดินวนรอบเตียงทุกคืน",
            "พอเอา {object} ไปวางไว้หน้าพระ เสียงเคาะก็ดังขึ้นจากในกล่องพระแทนที่จะดังจากประตู เหมือนของชิ้นนั้นไม่กลัวอะไรที่คนเป็นใช้ป้องกันตัว",
            "ในกล้องมือถือมีภาพเพิ่มขึ้นมาเอง เป็นภาพตัวเอกยืนอยู่ใน {place} ทั้งที่ตอนนั้นตัวเอกนั่งอยู่ที่บ้าน และภาพนั้นค่อยๆ ซูมเข้าหาใบหน้า",
            "ยิ่งพยายามลืม รายละเอียดกลับยิ่งชัดขึ้น ทั้งกลิ่น ทั้งเสียง และความรู้สึกเหมือนมีมือเย็นๆ แตะอยู่ตรงหลังคอทุกครั้งที่หลับตา",
            "เมื่อกลับไปดู {clue} อีกครั้ง มันไม่อยู่ที่เดิมแล้ว แต่ย้ายมาอยู่ในจุดที่ตัวเอกเพิ่งยืนเมื่อไม่กี่นาทีก่อน",
            "ก่อนฟ้าสาง เสียงของ {ghost} ไม่ได้อยู่ในที่มืดอีกต่อไป แต่มันดังออกมาจากปากของคนใกล้ตัวที่กำลังหลับอยู่ข้างๆ",
        ],
    },
    {
        "name": "กล้องเห็นสิ่งที่ยังไม่เกิด",
        "beats": [
            "เรื่องนี้เริ่มจาก {place} สถานที่ที่คนส่วนใหญ่เดินผ่านโดยไม่สังเกต แต่คนที่เคยเฝ้ากล้องที่นั่นรู้ดีว่าบางคืนภาพในจอไม่ได้มาจากเวลาปัจจุบัน",
            "{protagonist} เข้าไปตรวจระบบตอน {time} เพราะมีรายงานว่าเครื่องบันทึกภาพเสีย ทั้งที่ไฟสถานะทุกดวงยังติดปกติ",
            "ในห้องควบคุมมีกลิ่นแปลกๆ คือ {sensory} และมี {clue} วางอยู่หน้าเครื่องบันทึก เหมือนใครเพิ่งลุกออกไป",
            "ภาพจากกล้องตัวหนึ่งแสดงให้เห็น {event} แต่เมื่อหันไปดูพื้นที่จริง กลับยังไม่มีอะไรเกิดขึ้นเลย",
            "ตัวเอกลองกรอภาพย้อนหลัง แล้วเห็นตัวเองเดินเข้ามาในห้องอีกครั้งจากมุมกล้องที่ไม่มีอยู่ในแผนผังอาคาร",
            "ภาพถัดมา {ghost} ยืนอยู่ข้างหลังตัวเอกในจอ แต่พอหันกลับไป ด้านหลังมีแค่ผนังเปล่าและเสียงหายใจเบามาก",
            "{witness} บอกว่าเครื่องนี้เคยถูกถอดทิ้งไปแล้ว เพราะมันชอบบันทึกภาพคนที่จะหายตัวไปในคืนนั้นล่วงหน้าหลายนาที",
            "คำเตือนเดียวที่เหลืออยู่ในสมุดเวรคือ {rule} และลายมือในบรรทัดนั้นคล้ายกับลายมือของตัวเอกอย่างน่าขนลุก",
            "{twist} ทำให้ตัวเอกเข้าใจว่ากล้องไม่ได้บันทึกผี แต่มันบันทึกทางที่คนเป็นกำลังถูกพาไป",
            "หลังเรื่องจบ หน้าจอกล้องตัวเดิมยังค้างอยู่ที่ {final_image} และทุกคนที่เห็นภาพนั้นจะรีบปิดจอทันทีโดยไม่พูดอะไร",
        ],
        "middles": [
            "เมื่อซูมภาพเข้าไปใกล้ๆ ตัวเอกเห็น {object} อยู่ในมือของตัวเอง ทั้งที่ตอนนั้นของชิ้นนั้นยังวางอยู่บนโต๊ะด้านหลัง",
            "เสียงจากลำโพงกล้องดังช้ากว่าภาพไปสองสามวินาที และประโยคที่ออกมาคือเสียงของตัวเอกกำลังขอให้ใครบางคนหยุดตามมา",
            "ตัวเอกลองดึงปลั๊กเครื่องบันทึก แต่ภาพในจอยังเดินต่อไป และคราวนี้ภาพแสดงเวลาที่เร็วกว่าโลกจริงขึ้นเรื่อยๆ",
            "ในจอเห็น {witness} เดินผ่านทางเดิน แต่เมื่อตัวเอกโทรหา เขาบอกว่าเขาออกจากอาคารไปตั้งแต่หัวค่ำแล้ว",
            "กล้องมุมหนึ่งแพนตามเองช้าๆ ทั้งที่เป็นกล้องนิ่ง และหยุดที่ประตูบานหนึ่งซึ่งในแปลนอาคารระบุว่าไม่มีประตูตรงนั้น",
            "ทุกครั้งที่ภาพข้ามเฟรม จะมีเงาของ {ghost} ใกล้ตัวเอกขึ้นอีกนิด เหมือนมันไม่ได้เดิน แต่มันถูกตัดต่อให้เข้ามาใกล้",
            "ตัวเอกพิมพ์คำสั่งลบไฟล์ แต่ชื่อไฟล์ใหม่ปรากฏขึ้นแทน เป็นวันที่และเวลาหลังจากนั้นเพียงไม่กี่นาที",
            "ก่อนเครื่องดับเอง ภาพสุดท้ายแสดงให้เห็นตัวเอกนั่งอยู่หน้าจอเหมือนเดิม แต่ด้านหลังมีมือหนึ่งค่อยๆ ปิดประตูจากด้านใน",
        ],
    },
    {
        "name": "คนที่โทรมาจากสถานที่ปิดตาย",
        "beats": [
            "ถ้าใครได้รับสายจาก {place} หลังเที่ยงคืน คนแถวนั้นจะบอกเหมือนกันหมดว่าอย่ารับ เพราะปลายสายไม่เคยต้องการให้ช่วยออกมา",
            "{time} โทรศัพท์ของ {protagonist} ดังขึ้นจากเบอร์แปลก และเสียงปลายสายพูดชื่อ {object} เหมือนรู้ว่ามันอยู่กับใคร",
            "เมื่อตามเสียงไปถึงที่นั่น ตัวเอกเจอ {sensory} ลอยออกมาจากประตูที่ปิดสนิท และมี {clue} อยู่ตรงพื้น",
            "ปลายสายบอกให้เดินเข้าไปอีกนิดเดียว แต่ในเวลาเดียวกัน {event} ก็เกิดขึ้นตรงหน้า เหมือนสถานที่กำลังยืนยันคำพูดนั้น",
            "เสียงในโทรศัพท์เริ่มเปลี่ยนเป็นเสียงของคนรู้จัก ก่อนจะค่อยๆ กลายเป็นเสียงของ {ghost} ที่เรียกชื่อจริงของตัวเอก",
            "{witness} เคยเตือนว่า {rule} เพราะถ้าตอบกลับไป เสียงนั้นจะจำลมหายใจของคนตอบได้ตลอดชีวิต",
            "ตัวเอกพยายามวางสาย แต่หน้าจอไม่ยอมดับ และเสียงปลายสายเริ่มเล่าเหตุการณ์ที่ตัวเอกกำลังจะทำก่อนที่ตัวเอกจะตัดสินใจ",
            "เมื่อเดินถึงจุดที่เสียงบอกให้หยุด ตัวเอกเห็น {object} วางอยู่บนเก้าอี้ พร้อมรอยนิ้วมือเปียกเหมือนมีคนเพิ่งปล่อยมือ",
            "{twist} และความจริงนั้นทำให้ตัวเอกรู้ว่าสายโทรนี้ไม่ได้มาจากคนที่ติดอยู่ข้างใน แต่มาจากสิ่งที่กำลังหาทางออกมา",
            "ตั้งแต่นั้นมา ถ้าโทรศัพท์ดังขึ้นใกล้ {place} จะมี {final_image} ปรากฏพร้อมเสียงปลายสายที่ถามเบาๆ ว่าได้ยินแล้วใช่ไหม",
        ],
        "middles": [
            "ครั้งแรกที่ตัวเอกลองเปิดลำโพง เสียงในสายไม่ได้ดังออกจากมือถือ แต่ดังออกมาจากเพดานเหนือหัวช้าๆ",
            "ปลายสายบอกตำแหน่งของตัวเอกได้ละเอียดเกินไป ทั้งจำนวนก้าว กลิ่นในอากาศ และมือข้างที่กำลังถือไฟฉาย",
            "เมื่อเอามือถือให้คนอื่นฟัง ทุกคนได้ยินคนละประโยค บางคนได้ยินคำขอโทษ บางคนได้ยินเสียงร้องไห้ และบางคนได้ยินชื่อตัวเอง",
            "สัญญาณโทรศัพท์หายไปหมด ยกเว้นสายเดิมที่ยังค้างอยู่ และเวลาคุยบนหน้าจอเดินถอยหลังกลับไปเรื่อยๆ",
            "ตรงมุมหนึ่งของ {place} มีโทรศัพท์บ้านเก่าตั้งอยู่ทั้งที่ไม่มีสายต่อ และมันกำลังยกหูเองทีละนิด",
            "เสียงปลายสายหัวเราะเบาๆ ตอนตัวเอกพูดว่ากำลังจะออกไป เหมือนมันรู้ว่าประตูทุกบานถูกเปลี่ยนที่ไปแล้ว",
            "ในเสียงรบกวนแทรกอยู่ข้างหลัง มีเสียงคนจำนวนมากกระซิบคำเดียวกันซ้ำๆ ว่าอย่ารับแทนเขา",
            "ก่อนสายจะตัด ตัวเอกได้ยินเสียงตัวเองจากปลายสาย พูดประโยคเดียวกับที่กำลังคิดอยู่ในหัวทุกคำ",
        ],
    },
    {
        "name": "ห้องที่ไม่มีอยู่ในแปลน",
        "beats": [
            "{place} มีเรื่องเล่าแปลกอยู่อย่างหนึ่ง คือบางคืนจะมีทางเดินเพิ่มขึ้นมาเอง และคนที่เดินเข้าไปมักจำไม่ได้ว่าเริ่มหลงตั้งแต่ตอนไหน",
            "{protagonist} เข้าไปตอน {time} เพื่อจัดการเรื่องเล็กๆ เกี่ยวกับ {object} โดยคิดว่าตัวเองรู้ทางออกทั้งหมดของอาคารนี้ดี",
            "แต่ทางเดินคืนนั้นมีกลิ่น {sensory} และมี {clue} อยู่ตรงมุมที่เมื่อวานยังเป็นผนังทึบ",
            "ไม่นาน {event} ก็เกิดขึ้น ทำให้ตัวเอกเริ่มรู้ว่าพื้นที่ตรงนี้ไม่ได้อยู่ในอาคารเดิมอีกต่อไป",
            "ประตูบานหนึ่งเปิดออกเองช้าๆ ด้านในมี {object} วางอยู่กลางห้อง และทุกอย่างเงียบเหมือนถูกห้ามไม่ให้มีเสียง",
            "เงาของ {ghost} ปรากฏอยู่ตรงขอบประตู แต่ไม่ยอมเข้ามา เหมือนกำลังรอให้ตัวเอกเป็นฝ่ายเดินข้ามเส้นเข้าไปเอง",
            "{witness} เคยเล่าว่า {rule} เพราะห้องนั้นไม่ได้พาคนเข้าไปหลง แต่มันจำคนที่เคยเข้ามาได้",
            "เมื่อจะถอยกลับ ทางเดินด้านหลังกลายเป็นทางใหม่ทั้งหมด และบนผนังมีรอยขีดนับวันที่เหมือนมีคนติดอยู่มานาน",
            "{twist} ทำให้ห้องที่ไม่มีอยู่ในแปลนกลายเป็นหลักฐานว่าบางสถานที่ไม่ได้ถูกสร้างขึ้นมาเพื่อให้คนอยู่ แต่เพื่อเก็บคนไว้",
            "หลังจากคืนนั้น แปลนอาคารถูกเปลี่ยนใหม่หลายครั้ง แต่ยังมีคนเห็น {final_image} อยู่ในตำแหน่งที่ไม่มีห้องใดควรอยู่",
        ],
        "middles": [
            "ตัวเอกลองนับก้าวจากประตูถึงมุมทางเดิน แต่ทุกครั้งที่นับใหม่ จำนวนก้าวเพิ่มขึ้นเหมือนพื้นยืดออกเอง",
            "ฝุ่นบนพื้นไม่มีรอยเท้าของใครนอกจากตัวเอก แต่เสียงรองเท้าคู่ที่สองดังตามมาในระยะเดียวกันตลอด",
            "ที่ผนังมีรูปเก่าแขวนอยู่ รูปนั้นถ่ายจากมุมเดียวกับที่ตัวเอกยืน และในรูปมีคนยืนอยู่ด้านหลังมากกว่าหนึ่งคน",
            "ประตูทุกบานมีลูกบิดเย็นเหมือนเพิ่งแช่น้ำแข็ง แต่เมื่อแตะลงไป กลับมีเสียงถอนหายใจดังจากในห้อง",
            "ตัวเอกพบป้ายบอกทางที่เขียนด้วยลายมือสดใหม่ แต่มันชี้กลับไปทางที่เพิ่งเดินผ่านมาแล้วสามครั้ง",
            "เมื่อเปิดไฟฉายส่องพื้น เห็นเงาของ {ghost} ทาบอยู่ข้างตัว แต่แสงไฟไม่เจอต้นตอของเงานั้นเลย",
            "ห้องหนึ่งมีเก้าอี้วางหันหน้าเข้าผนัง บนเก้าอี้มี {object} และมีรอยนั่งบุ๋มลงไปเหมือนมีคนเพิ่งลุก",
            "ก่อนถึงทางออก ตัวเอกได้ยินเสียงตัวเองเคาะประตูจากอีกฝั่ง ทั้งที่ตัวจริงยังยืนอยู่ในทางเดินเดิม",
        ],
    },
    {
        "name": "ความผิดที่สถานที่จำได้",
        "beats": [
            "บางสถานที่ไม่ได้เฮี้ยนเพราะมีคนตาย แต่เฮี้ยนเพราะมันจำเรื่องที่คนเป็นพยายามลืม และ {place} เป็นหนึ่งในนั้น",
            "{protagonist} กลับไปที่นั่นตอน {time} หลังจากได้รับข่าวเกี่ยวกับ {object} ซึ่งเป็นของที่ไม่ควรกลับมาอยู่ในชีวิตอีก",
            "สิ่งที่รอต้อนรับไม่ใช่คน แต่เป็น {sensory} กับ {clue} ที่ชี้ไปยังคืนหนึ่งในอดีตที่ตัวเอกไม่เคยเล่าให้ใครฟัง",
            "{event} ทำให้ตัวเอกเริ่มแน่ใจว่าสถานที่นี้ไม่ได้ต้องการหลอก แต่ต้องการให้จำ",
            "{ghost} ปรากฏตัวไม่ชัดเจน เหมือนเศษความทรงจำที่ถูกกดไว้ แต่ทุกครั้งที่เข้าใกล้ ภาพในหัวกลับชัดขึ้น",
            "{witness} บอกเพียงว่า {rule} เพราะคนที่ฝืนมักออกมาพร้อมความทรงจำที่ไม่ใช่ของตัวเอง",
            "ตัวเอกพบ {object} ในจุดที่เคยเกิดเรื่อง และคราวนี้มีคราบใหม่เพิ่มขึ้น เหมือนอดีตเพิ่งเกิดซ้ำเมื่อไม่กี่นาทีก่อน",
            "ยิ่งพยายามปฏิเสธ เสียงจากกำแพงยิ่งเล่ารายละเอียดที่ไม่มีใครควรรู้ รวมถึงคำสุดท้ายของคนที่หายไป",
            "{twist} และคืนนั้นตัวเอกจึงเข้าใจว่าผีที่ตามมาอาจไม่ใช่คนตาย แต่อาจเป็นความจริงที่ถูกทิ้งไว้ในที่มืด",
            "ทุกวันนี้ {place} ยังมี {final_image} ให้เห็นเป็นบางคืน เหมือนสถานที่กำลังรอให้ใครอีกคนกลับมายอมรับเรื่องของตัวเอง",
        ],
        "middles": [
            "ทุกครั้งที่ตัวเอกกะพริบตา ภาพตรงหน้าจะเปลี่ยนเป็นคืนเก่าเพียงเสี้ยววินาที แล้วกลับมาเป็นปัจจุบันเหมือนไม่มีอะไรเกิดขึ้น",
            "เสียงในหัวเริ่มไม่ใช่ความคิดของตัวเอง แต่เป็นเสียงคนอื่นที่บอกว่าจำได้แล้วใช่ไหม",
            "ตรงพื้นมีรอยลากยาวไปถึงมุมห้อง พอเอาไฟส่องตาม รอยนั้นกลับหยุดตรงรองเท้าของตัวเอกพอดี",
            "กระจกบานหนึ่งสะท้อนตัวเอกในวัยที่ต่างออกไป และคนในกระจกกำลังร้องไห้โดยไม่ส่งเสียง",
            "{witness} ยอมรับภายหลังว่าคนแถวนั้นรู้เรื่องทั้งหมด แต่ไม่มีใครกล้าพูด เพราะกลัวสถานที่จะจำเสียงของตัวเองได้",
            "ใน {object} มีเศษหลักฐานเล็กๆ ที่ทำให้ตัวเอกจำได้ว่าเรื่องที่คิดว่าเป็นฝัน ความจริงเคยเกิดขึ้นตรงนี้",
            "เมื่อเสียงของ {ghost} ดังใกล้ขึ้น มันไม่ได้ถามหาความช่วยเหลือ แต่มันทวงคำขอโทษที่ไม่เคยถูกพูดออกมา",
            "ก่อนทุกอย่างจะจบ ตัวเอกเห็นตัวเองในอดีตยืนอยู่ตรงหน้า และคนคนนั้นยกนิ้วแตะปากเหมือนสั่งให้เงียบอีกครั้ง",
        ],
    },
    {
        "name": "พิธีเก่าที่ถูกเปิดซ้ำ",
        "beats": [
            "คนแก่ในละแวก {place} เคยพูดไว้ว่า บางประตูไม่ได้ล็อกไว้กันขโมย แต่ล็อกไว้กันพิธีบางอย่างไม่ให้เริ่มใหม่",
            "{protagonist} เข้าไปที่นั่นตอน {time} เพราะต้องจัดการกับ {object} ที่ถูกทิ้งไว้เหมือนของไม่มีค่า",
            "ด้านในมี {sensory} และ {clue} เรียงอยู่ตรงพื้นคล้ายร่องรอยของพิธีที่ถูกหยุดกลางคัน",
            "ทันทีที่แตะของชิ้นนั้น {event} ก็เกิดขึ้นพร้อมเสียงสวดแผ่วๆ จากมุมที่ไม่มีคนยืนอยู่",
            "{ghost} ค่อยๆ ปรากฏในระยะไกล ไม่ได้พุ่งเข้าหา แต่ยืนรอเหมือนกำลังดูว่าตัวเอกจะทำขั้นตอนต่อไปถูกหรือไม่",
            "{witness} เตือนว่า {rule} เพราะพิธีนี้ไม่ต้องการคนเชื่อ แค่ต้องการคนทำตามครบก็พอ",
            "ตัวเอกเริ่มพบว่าทุกอย่างในห้องถูกจัดไว้ให้บังคับเดินตามลำดับ ทั้งเก้าอี้ ประตู ไฟ และ {object}",
            "เมื่อทำผิดเพียงครั้งเดียว เสียงรอบตัวหยุดพร้อมกัน แล้วเริ่มนับหนึ่งใหม่จากในความมืด",
            "{twist} ทำให้ตัวเอกเข้าใจว่าคนที่เคยหายไปไม่ได้ถูกฆ่า แต่ถูกใช้เป็นส่วนหนึ่งของพิธีที่ยังไม่จบ",
            "หลังจากคืนนั้น {final_image} ยังอยู่ที่ {place} เหมือนสัญญาณว่าพิธีหยุดลงชั่วคราว แต่ยังรอคนเปิดต่อ",
        ],
        "middles": [
            "เส้นฝุ่นบนพื้นไม่ได้กระจายมั่วๆ แต่วาดเป็นวงที่พอดีกับระยะก้าวของตัวเอกอย่างประหลาด",
            "ไฟทุกดวงดับเรียงกันทีละดวงเหมือนมีใครเดินเป่ามันจากด้านใน และทุกครั้งที่ไฟดับ เสียงสวดจะชัดขึ้น",
            "ตัวเอกเห็นเงาคนหลายเงานั่งล้อมวงอยู่ในกระจก แต่ในห้องจริงมีเพียงเก้าอี้ว่างเปล่า",
            "{object} เริ่มอุ่นขึ้นเรื่อยๆ จนจับแทบไม่ได้ แต่พอวางลง กลับมีรอยมือเย็นเฉียบประทับอยู่บนผิวของมัน",
            "{witness} เคยเห็นพิธีนี้ครั้งหนึ่งเมื่อนานมาแล้ว และพูดเพียงว่าเสียงสุดท้ายในพิธีไม่ใช่เสียงผี แต่เป็นเสียงคนเป็นที่ยอมแพ้",
            "กลางห้องมีประตูเล็กๆ ที่ไม่เคยมีมาก่อน พอเปิดออก กลับเห็นทางเดินของ {place} จากมุมที่เหมือนมองผ่านตาคนอื่น",
            "เสียงของ {ghost} เริ่มสอนทีละประโยคเหมือนครูใจเย็น แต่ทุกประโยคลงท้ายด้วยคำว่าอีกคนหนึ่ง",
            "ก่อนถึงขั้นสุดท้าย ตัวเอกเห็นเงาของตัวเองนั่งอยู่ในวงพิธีแล้ว ทั้งที่ร่างจริงยังยืนถือไฟฉายอยู่ข้างประตู",
        ],
    },
]

ROLE_VISUALS = {
    "พนักงานกะดึก": "one adult Thai night shift clerk in a tired uniform",
    "ไรเดอร์ส่งของ": "one adult Thai delivery rider holding a helmet",
    "ช่างซ่อมกล้องวงจรปิด": "one adult Thai CCTV repair technician with a small tool bag",
    "พยาบาลเวรดึก": "one adult Thai night nurse in a pale uniform",
    "แม่บ้านโรงแรม": "one adult Thai hotel housekeeper holding a key card",
    "คนเฝ้าโกดัง": "one adult Thai warehouse guard with a flashlight",
    "เจ้าหน้าที่เวชระเบียน": "one adult Thai medical records officer carrying folders",
    "ยามหมู่บ้าน": "one adult Thai security guard with a radio",
    "นักศึกษาฝึกงาน": "one adult Thai intern with a canvas bag",
    "คนขับรถตู้": "one adult Thai van driver holding a ring of keys",
}

OBJECT_VISUALS = {
    "กุญแจที่ไม่มีหมายเลข": "an old brass key with no number tag",
    "เทปวิดีโอที่ถูกเขียนว่าอย่ากรอกลับ": "a black VHS tape with a torn warning label, but no readable text",
    "รูปถ่ายที่มีเงาเพิ่มขึ้นทุกครั้ง": "a faded old photograph showing an extra dark silhouette",
    "สมุดลงชื่อที่มีชื่อคนตาย": "an old guest register opened on a stained page, no readable writing",
    "กล่องยาเก่าที่ฉลากถูกขูดออก": "an old medicine box with its label scratched away",
    "พวงกุญแจที่มีกลิ่นธูปติดอยู่": "a keychain with ash marks and old smoke stains",
    "แฟ้มคดีที่หน้าสุดท้ายหายไป": "a dusty case file with its final page torn out",
    "บัตรคิวที่ออกเป็นเลขเดิมทุกครั้ง": "an old queue ticket machine and one repeated ticket, no readable numbers",
}

GHOST_VISUALS = {
    "ผู้หญิงผมเปียกที่พูดด้วยเสียงของคนรู้จัก": "a wet-haired female apparition half hidden in shadow",
    "ชายแก่ที่เห็นได้เฉพาะในกระจก": "an old male apparition visible only as a mirror reflection",
    "เงาคนไข้ที่ลากสายน้ำเกลือไปตามพื้น": "a patient-shaped shadow dragging an IV tube across the floor",
    "คนขายตั๋วที่ตายก่อนโรงหนังปิด": "a dead ticket seller silhouette behind a dusty cinema booth",
    "หญิงใส่ชุดไทยที่หันหลังตลอดเวลา": "a Thai woman in traditional dress standing with her back turned",
    "เสียงผู้ชายที่อยู่ในลำโพงแต่ไม่มีตัว": "an empty speaker crackling in a dark room with no visible person",
    "เงาคนเฝ้าศพที่เดินตามเสียงกุญแจ": "a corpse-room attendant shadow following the sound of keys",
}

EVENT_VISUALS = {
    "ไฟทั้งชั้นดับพร้อมกัน แต่มีห้องเดียวที่ยังสว่าง": "a dark floor where only one room glows with sickly fluorescent light",
    "กล้องวงจรปิดย้อนหลังไปเห็นเหตุการณ์ที่ยังไม่เกิด": "a CCTV monitor showing a future moment in the same hallway",
    "ประตูล็อกจากด้านใน ทั้งที่ไม่มีใครอยู่ในห้อง": "a locked door with a latch closed from the inside in an empty room",
    "เสียงเคาะดังมาจากผนังแทนที่จะดังจากประตู": "a stained wall vibrating as if something is knocking from inside it",
    "ชื่อของตัวเอกไปปรากฏในสมุดลงชื่อเมื่อสิบปีก่อน": "an old register book opened to a page that should be impossible, no readable writing",
    "ลิฟต์ขึ้นไปชั้นที่ไม่มีอยู่จริง": "an old elevator display stopping on a floor that should not exist",
    "โทรศัพท์โทรเข้ามาจากเบอร์ของสถานที่เดียวกัน": "a mobile phone ringing inside the forbidden place, screen glow but no readable text",
}


def run(command):
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail[-1200:] or f"Command failed: {command[0]}")


def unique_download_path(file_name):
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    target = downloads / file_name
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    for index in range(2, 1000):
        candidate = downloads / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Too many duplicate files in Downloads")


def ffprobe_duration(path):
    if Path(FFPROBE).exists() and Path(FFPROBE).name == "ffprobe":
        result = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=duration", "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        for value in result.stdout.splitlines():
            try:
                duration = float(value.strip())
            except ValueError:
                continue
            if duration > 0:
                return max(0.1, duration)

        fallback = subprocess.run([FFPROBE, str(path)], capture_output=True, text=True)
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", fallback.stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return max(0.1, int(hours) * 3600 + int(minutes) * 60 + float(seconds))

    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(path)
        if audio and getattr(audio.info, "length", None):
            return max(0.1, float(audio.info.length))
    except Exception:
        pass
    raise RuntimeError(f"Cannot read media duration: {path}")


def load_font(size):
    for path in FONT_FALLBACKS:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size, index=0)
            except TypeError:
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered_lines(draw, lines, y, font, fill, stroke_width=2, stroke_fill=(0, 0, 0), spacing=10, width=1080):
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        x = (width - (box[2] - box[0])) / 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += (box[3] - box[1]) + spacing
    return y


def random_place():
    if random.random() < 0.7:
        root_th, root_en = random.choice(PLACE_ROOTS)
        context_th, context_en = random.choice(PLACE_CONTEXTS)
        return (f"{root_th}{context_th}", f"{root_en} {context_en}")
    return random.choice(PLACES)


def story_context(seed):
    return {
        "place": seed["place"][0],
        "place_visual": seed["place"][1],
        "protagonist": seed["protagonist"],
        "object": seed["object"],
        "ghost": seed["ghost"],
        "event": seed["event"],
        "twist": seed["twist"],
        "time": seed["time"],
        "witness": seed["witness"],
        "sensory": seed["sensory"],
        "clue": seed["clue"],
        "rule": seed["rule"],
        "final_image": seed["final_image"],
    }


def fill_story_template(template, seed):
    return template.format(**story_context(seed))


def make_seed(brief, avoid=None):
    avoid = avoid or {}
    cleaned = brief.strip()
    matched_place = next((candidate for candidate in PLACES if candidate[0] in cleaned), None)
    for _ in range(80):
        place = matched_place or random_place()
        protagonist = random.choice(PROTAGONISTS)
        object_name = random.choice(OBJECTS)
        ghost = random.choice(GHOSTS)
        event = random.choice(EVENTS)
        twist = random.choice(TWISTS)
        pattern = random.choice(STORY_PATTERNS)
        title = cleaned[:44] if cleaned.startswith("อย่าเปิด") else f"อย่าเปิด...{place[0]}"
        if (
            title not in avoid.get("titles", set())
            and place[0] not in avoid.get("places", set())
            and pattern["name"] not in avoid.get("patterns", set())
        ):
            break
    else:
        place = matched_place or random_place()
        protagonist = random.choice(PROTAGONISTS)
        object_name = random.choice(OBJECTS)
        ghost = random.choice(GHOSTS)
        event = random.choice(EVENTS)
        twist = random.choice(TWISTS)
        pattern = random.choice(STORY_PATTERNS)
        title = cleaned[:44] if cleaned.startswith("อย่าเปิด") else f"อย่าเปิด...{place[0]}"

    if cleaned.startswith("อย่าเปิด"):
        title = cleaned[:44]
    else:
        title = f"อย่าเปิด...{place[0]}"
    return {
        "title": title,
        "place": place,
        "protagonist": protagonist,
        "object": object_name,
        "ghost": ghost,
        "event": event,
        "twist": twist,
        "time": random.choice(TIMES),
        "witness": random.choice(WITNESSES),
        "sensory": random.choice(SENSORY_DETAILS),
        "clue": random.choice(CLUES),
        "rule": random.choice(RULES),
        "final_image": random.choice(FINAL_IMAGES),
        "pattern": pattern,
    }


def story_lines(seed, mode):
    pattern = seed["pattern"]
    base = [fill_story_template(template, seed) for template in pattern["beats"]]
    if mode == "short":
        return base

    middle = [fill_story_template(template, seed) for template in pattern["middles"]]
    selected_middle = random.sample(middle, k=min(8, len(middle)))
    lines = [base[0], base[1], base[2], base[3], *selected_middle, base[4], base[5], base[6], base[7], base[8], base[9]]
    return [expand_long_line(line, seed, index, len(lines)) for index, line in enumerate(lines, start=1)]


def expand_long_line(line, seed, index, total):
    details = [
        "ความน่ากลัวของช่วงนี้ไม่ได้มาแบบโผล่ให้ตกใจ แต่มันค่อยๆ กดอากาศให้หนักขึ้น จนตัวเอกรู้สึกว่าทุกอย่างรอบตัวกำลังจับตามองอยู่เงียบๆ",
        f"สิ่งที่ทำให้ใจเสียที่สุดคือรายละเอียดเล็กๆ อย่าง {seed['sensory']} เพราะมันชัดขึ้นทุกครั้งที่พยายามคิดว่าเป็นเรื่องปกติ",
        f"ตัวเอกพยายามหาเหตุผลให้ตัวเองใจเย็น แต่ {seed['clue']} ทำให้ทุกคำอธิบายธรรมดาดูอ่อนแรงลงทันที",
        "ยิ่งเดินต่อไป เวลาเหมือนยืดออก เสียงฝีเท้าของตัวเองดังแปลกๆ ราวกับมีอีกคู่หนึ่งก้าวตามหลังด้วยจังหวะเดียวกันพอดี",
        f"ในตอนนั้นคำเตือนที่ว่า {seed['rule']} กลับดังขึ้นในหัวซ้ำๆ ทั้งที่ก่อนหน้านี้ตัวเอกแทบไม่เชื่อคำพูดนั้นเลย",
        "ไม่มีใครกระโจนออกมา ไม่มีเสียงกรีดร้อง มีเพียงความรู้สึกว่าถ้าหันไปผิดจังหวะ สิ่งที่ยืนรออยู่จะไม่ปล่อยให้กลับออกไปเหมือนเดิม",
        f"และทุกครั้งที่ชื่อของ {seed['place'][0]} ผ่านเข้ามาในความคิด ภาพบางอย่างก็แวบขึ้นเหมือนความทรงจำของคนอื่นที่ถูกยัดเข้ามาในหัว",
        "สิ่งที่น่ากลัวกว่าการเห็นผี คือการเริ่มไม่แน่ใจว่าตัวเองยังควบคุมสิ่งที่กำลังทำอยู่จริงหรือเปล่า",
    ]
    ending = (
        "เรื่องนี้จบลงตรงนั้น ไม่ใช่เพราะทุกอย่างถูกอธิบายได้ แต่เพราะตัวเอกไม่เหลือแรงจะพิสูจน์อะไรอีกแล้ว "
        f"และภาพสุดท้ายที่จำได้คือ {seed['final_image']} ที่ยังเหมือนกำลังรอให้ใครสักคนกลับไปเปิดมันอีกครั้ง"
    )
    if index == total:
        return f"{line} {ending}"
    return f"{line} {random.choice(details)}"


def scene_visual_detail(seed, line, number):
    place_th, place_en = seed["place"]
    role = ROLE_VISUALS.get(seed["protagonist"], f"one adult Thai {seed['protagonist']}")
    object_visual = OBJECT_VISUALS.get(seed["object"], seed["object"])
    ghost_visual = GHOST_VISUALS.get(seed["ghost"], seed["ghost"])
    event_visual = EVENT_VISUALS.get(seed["event"], seed["event"])

    if number == 1:
        return f"opening shot of {place_en}, the forbidden place clearly visible, {object_visual} in the foreground, no people yet"
    if "ถูกเรียก" in line or "เก็บ" in line:
        return f"{role} entering {place_en} at night, reaching toward {object_visual}, tense but realistic"
    if "ประตูเปิด" in line or "ลมเย็น" in line:
        return f"a half-open door inside {place_en}, cold mist spilling out, {role} hesitating at the threshold"
    if "สิ่งแรก" in line or seed["event"] in line:
        return f"{event_visual} inside {place_en}, {role} frozen in fear, cinematic practical lighting"
    if "วางอยู่กลาง" in line or "ของต้องห้าม" in line:
        return f"close shot of {object_visual} placed alone in the center of {place_en}, ominous empty space around it"
    if "เงา" in line or seed["ghost"] in line:
        return f"{ghost_visual} appearing at the dark edge of {place_en}, {role} in the same frame but only one living person"
    if "โทร" in line or "มือถือ" in line:
        return f"{role} holding a glowing mobile phone inside {place_en}, the room behind them unnaturally dark, no readable text"
    if "ชื่อ" in line or "บันทึก" in line or "เอกสาร" in line:
        return f"{role} discovering an old file or register beside {object_visual}, a terrible clue implied without readable text"
    if "กระจก" in line:
        return f"{role} staring into a dirty mirror where {ghost_visual} appears behind them as a reflection only"
    if "รอยเท้า" in line:
        return f"wet footprints circling on the floor of {place_en}, {role} standing inside the circle with a flashlight"
    if "นาฬิกา" in line:
        return f"old clocks on the wall of {place_en}, all hands pointing wrong, {role} looking terrified"
    if "ประตูสุดท้าย" in line or "ทางเดินเดิม" in line:
        return f"the same dark corridor inside {place_en} repeating impossibly, {role} trapped in a loop"
    if "กระซิบ" in line or "ลมหายใจ" in line:
        return f"extreme tense close shot, {role} sensing a whisper beside their ear, {ghost_visual} barely visible behind"
    if "สุดท้าย" in line or "ตั้งแต่นั้น" in line:
        return f"final haunting shot of {place_en} after the event, one lonely light left on, {ghost_visual} hidden in the background"
    return f"{role} inside {place_en}, {object_visual} nearby, {ghost_visual} suggested in the shadows, realistic horror scene"


def make_story(mode, brief, avoid=None):
    seed = make_seed(brief, avoid=avoid)
    lines = story_lines(seed, mode)
    target_seconds = 124 if mode == "short" else 420
    duration = max(6, round(target_seconds / len(lines)))
    scenes = []
    for index, line in enumerate(lines, start=1):
        scenes.append({
            "number": index,
            "beat": "เสียงเล่าเรื่องต่อเนื่อง",
            "duration": duration,
            "narration": line,
            "visual": scene_visual_detail(seed, line, index),
        })
    return {
        "mode": mode,
        "title": seed["title"],
        "seed": {
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
        "script": "\n\n".join(lines),
    }


def draw_horror_background(path, scene, story, size):
    width, height = size
    seed = story.get("seed", {})
    place = seed.get("placeTitle", story["title"])
    object_name = seed.get("object", "")
    event = seed.get("event", "")
    scene_no = scene["number"]
    image = Image.new("RGB", size, (13, 22, 22))
    draw = ImageDraw.Draw(image)

    def box(x1, y1, x2, y2):
        return (int(width * x1), int(height * y1), int(width * x2), int(height * y2))

    def point(x, y):
        return (int(width * x), int(height * y))

    def line(points, fill, line_width=3):
        draw.line([point(x, y) for x, y in points], fill=fill, width=max(1, int(line_width * width / 1080)))

    for y in range(height):
        tone = int(26 + 84 * (y / height))
        draw.line((0, y, width, y), fill=(tone // 2, tone, max(0, tone - 12)))

    random.seed(f"{story['title']}-{scene['number']}")
    for _ in range(180):
        x = random.randint(0, width)
        y = random.randint(0, height)
        alpha = random.randint(12, 36)
        color = (42 + alpha, 59 + alpha, 54 + alpha)
        draw.rectangle((x, y, x + random.randint(1, 5), y + random.randint(1, 5)), fill=color)

    # Perspective floor and ceiling guide the eye behind the subtitles.
    draw.polygon([point(0.12, 0.28), point(0.88, 0.28), point(1.05, 0.84), point(-0.05, 0.84)], fill=(18, 29, 29), outline=(62, 77, 72))
    line([(0.18, 0.32), (0.02, 0.84)], (53, 69, 66), 4)
    line([(0.82, 0.32), (0.98, 0.84)], (53, 69, 66), 4)
    for yy in [0.34, 0.45, 0.58, 0.72]:
        line([(0.18, yy), (0.82, yy)], (38, 53, 50), 2)

    def draw_shelves():
        for side in [(0.02, 0.19, 0.25, 0.78), (0.75, 0.19, 0.98, 0.78)]:
            draw.rectangle(box(*side), fill=(43, 54, 50), outline=(95, 112, 99), width=max(3, width // 360))
            for yy in [0.27, 0.36, 0.45, 0.54, 0.63, 0.72]:
                line([(side[0], yy), (side[2], yy)], (116, 125, 104), 3)
                for x in [side[0] + 0.03, side[0] + 0.08, side[0] + 0.14, side[0] + 0.19]:
                    draw.rectangle(box(x, yy - 0.055, x + 0.035, yy - 0.006), fill=random.choice([(138, 126, 92), (96, 120, 112), (112, 88, 72), (68, 86, 84)]))

    def draw_phone_booth():
        draw.polygon([point(0.38, 0.18), point(0.50, 0.10), point(0.62, 0.18)], fill=(46, 58, 52), outline=(119, 120, 96))
        draw.rectangle(box(0.46, 0.18, 0.54, 0.28), fill=(57, 70, 62))
        draw.rectangle(box(0.34, 0.31, 0.67, 0.73), fill=(68, 26, 24), outline=(153, 66, 50), width=max(5, width // 180))
        draw.rectangle(box(0.39, 0.37, 0.62, 0.66), fill=(25, 43, 43), outline=(180, 194, 162), width=max(3, width // 300))
        draw.rectangle(box(0.43, 0.43, 0.58, 0.49), fill=(36, 37, 33))
        draw.arc(box(0.43, 0.49, 0.59, 0.61), 190, 350, fill=(180, 190, 160), width=max(4, width // 280))

    def draw_elevator():
        draw.rectangle(box(0.25, 0.17, 0.75, 0.78), fill=(38, 47, 48), outline=(112, 124, 119), width=max(8, width // 150))
        line([(0.50, 0.18), (0.50, 0.78)], (72, 84, 84), 5)
        draw.rectangle(box(0.65, 0.29, 0.72, 0.45), fill=(21, 31, 32), outline=(132, 143, 135), width=3)
        draw.ellipse(box(0.675, 0.34, 0.705, 0.37), fill=(197, 61, 47))
        draw.rectangle(box(0.39, 0.11, 0.61, 0.15), fill=(148, 29, 30))

    def draw_cinema():
        draw.rectangle(box(0.15, 0.16, 0.85, 0.38), fill=(27, 29, 33), outline=(92, 76, 61), width=4)
        for row in range(4):
            y = 0.46 + row * 0.075
            for col in range(6):
                x = 0.18 + col * 0.115
                draw.rounded_rectangle(box(x, y, x + 0.08, y + 0.045), radius=10, fill=(83, 28, 31), outline=(128, 52, 45), width=2)

    def draw_clinic():
        draw.rectangle(box(0.18, 0.18, 0.82, 0.70), fill=(30, 48, 52), outline=(103, 128, 126), width=5)
        draw.rectangle(box(0.44, 0.22, 0.56, 0.27), fill=(186, 206, 188))
        draw.rectangle(box(0.485, 0.19, 0.515, 0.30), fill=(186, 206, 188))
        for x in [0.25, 0.39, 0.53, 0.67]:
            draw.rounded_rectangle(box(x, 0.56, x + 0.10, 0.62), radius=8, fill=(52, 72, 76), outline=(115, 130, 124), width=3)

    def draw_rail_house():
        draw.polygon([point(0.22, 0.35), point(0.43, 0.24), point(0.65, 0.35)], fill=(55, 43, 34), outline=(117, 91, 67))
        draw.rectangle(box(0.27, 0.35, 0.60, 0.65), fill=(54, 47, 39), outline=(118, 95, 72), width=4)
        line([(0.08, 0.80), (0.46, 0.48)], (124, 120, 100), 5)
        line([(0.92, 0.80), (0.54, 0.48)], (124, 120, 100), 5)

    def draw_stairs():
        for i in range(9):
            y = 0.25 + i * 0.055
            draw.rectangle(box(0.22 + i * 0.018, y, 0.78 - i * 0.018, y + 0.028), fill=(37, 49, 50), outline=(86, 98, 93), width=2)
        line([(0.22, 0.24), (0.08, 0.78)], (117, 121, 104), 5)
        line([(0.78, 0.24), (0.92, 0.78)], (117, 121, 104), 5)

    def draw_costumes():
        for x, color in [(0.28, (105, 72, 49)), (0.42, (72, 91, 86)), (0.56, (117, 88, 62)), (0.70, (70, 62, 84))]:
            line([(x, 0.22), (x, 0.64)], (150, 130, 88), 2)
            draw.polygon([point(x - 0.055, 0.34), point(x + 0.055, 0.34), point(x + 0.09, 0.66), point(x - 0.09, 0.66)], fill=color, outline=(169, 144, 91))

    if "โทรศัพท์" in place or "วัด" in place:
        draw_phone_booth()
    elif "ลิฟต์" in place or "โรงพยาบาล" in place:
        draw_elevator()
    elif "โรงหนัง" in place:
        draw_cinema()
    elif "คลินิก" in place:
        draw_clinic()
    elif "รถไฟ" in place:
        draw_rail_house()
    elif "บันได" in place:
        draw_stairs()
    elif "ชุดไทย" in place:
        draw_costumes()
    else:
        draw_shelves()

    def draw_object(cx=0.50, cy=0.61, scale=1.0):
        if "กุญแจ" in object_name:
            draw.ellipse(box(cx - 0.035 * scale, cy - 0.04 * scale, cx + 0.025 * scale, cy + 0.02 * scale), outline=(216, 178, 93), width=max(4, width // 230))
            line([(cx + 0.02 * scale, cy), (cx + 0.12 * scale, cy + 0.06 * scale)], (216, 178, 93), 7)
            line([(cx + 0.08 * scale, cy + 0.035 * scale), (cx + 0.07 * scale, cy + 0.08 * scale)], (216, 178, 93), 5)
        elif "เทป" in object_name:
            draw.rounded_rectangle(box(cx - 0.12 * scale, cy - 0.055 * scale, cx + 0.12 * scale, cy + 0.055 * scale), radius=10, fill=(29, 29, 30), outline=(188, 179, 145), width=4)
            draw.ellipse(box(cx - 0.08 * scale, cy - 0.03 * scale, cx - 0.035 * scale, cy + 0.015 * scale), outline=(170, 170, 150), width=3)
            draw.ellipse(box(cx + 0.035 * scale, cy - 0.03 * scale, cx + 0.08 * scale, cy + 0.015 * scale), outline=(170, 170, 150), width=3)
        elif "รูป" in object_name:
            draw.rectangle(box(cx - 0.105 * scale, cy - 0.08 * scale, cx + 0.105 * scale, cy + 0.08 * scale), fill=(202, 197, 175), outline=(72, 50, 42), width=4)
            draw.rectangle(box(cx - 0.075 * scale, cy - 0.05 * scale, cx + 0.075 * scale, cy + 0.045 * scale), fill=(42, 55, 54))
            draw.ellipse(box(cx - 0.018 * scale, cy - 0.03 * scale, cx + 0.018 * scale, cy + 0.006 * scale), fill=(18, 20, 20))
        elif "ยา" in object_name:
            draw.rectangle(box(cx - 0.10 * scale, cy - 0.06 * scale, cx + 0.10 * scale, cy + 0.06 * scale), fill=(190, 197, 174), outline=(108, 85, 70), width=4)
            draw.rectangle(box(cx - 0.02 * scale, cy - 0.045 * scale, cx + 0.02 * scale, cy + 0.045 * scale), fill=(143, 33, 35))
            draw.rectangle(box(cx - 0.06 * scale, cy - 0.015 * scale, cx + 0.06 * scale, cy + 0.015 * scale), fill=(143, 33, 35))
        else:
            draw.rectangle(box(cx - 0.115 * scale, cy - 0.07 * scale, cx + 0.115 * scale, cy + 0.07 * scale), fill=(112, 91, 66), outline=(199, 174, 112), width=4)
            for i in range(4):
                line([(cx - 0.08 * scale, cy - 0.035 * scale + i * 0.022 * scale), (cx + 0.08 * scale, cy - 0.035 * scale + i * 0.022 * scale)], (51, 42, 35), 2)

    if scene_no in (2, 5, 8, 10):
        draw_object(0.50, 0.61, 1.25)
    else:
        draw_object(0.68, 0.62, 0.75)

    if "กล้อง" in event and scene_no == 4:
        draw.rectangle(box(0.26, 0.18, 0.74, 0.34), fill=(17, 24, 25), outline=(120, 139, 130), width=4)
        draw.rectangle(box(0.30, 0.21, 0.48, 0.31), fill=(34, 75, 69), outline=(95, 130, 117), width=2)
        draw.rectangle(box(0.52, 0.21, 0.70, 0.31), fill=(55, 34, 36), outline=(116, 86, 84), width=2)
    if "โทรศัพท์" in scene["narration"] or scene_no == 7:
        draw.rounded_rectangle(box(0.70, 0.45, 0.83, 0.68), radius=18, fill=(13, 18, 19), outline=(130, 150, 140), width=4)
        draw.rectangle(box(0.72, 0.49, 0.81, 0.62), fill=(36, 75, 70))
    if "ประตู" in event and scene_no == 4:
        draw.rectangle(box(0.38, 0.24, 0.62, 0.74), fill=(36, 31, 28), outline=(124, 91, 66), width=5)
        draw.ellipse(box(0.57, 0.49, 0.59, 0.51), fill=(215, 176, 83))

    floor_y = int(height * 0.76)
    draw.ellipse((width * 0.32, floor_y - 30, width * 0.68, floor_y + 90), fill=(8, 12, 12))

    person_x = int(width * 0.52 + random.randint(-60, 60))
    person_y = int(height * 0.59)
    draw.ellipse((person_x - 34, person_y - 132, person_x + 34, person_y - 64), fill=(38, 33, 29))
    draw.rectangle((person_x - 42, person_y - 70, person_x + 42, person_y + 85), fill=(52, 48, 39))
    draw.line((person_x - 38, person_y + 84, person_x - 58, person_y + 170), fill=(30, 28, 26), width=16)
    draw.line((person_x + 35, person_y + 84, person_x + 55, person_y + 170), fill=(30, 28, 26), width=16)

    ghost_x = int(width * 0.18 + random.randint(-25, 50))
    ghost_y = int(height * 0.44)
    ghost_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    ghost = ImageDraw.Draw(ghost_layer)
    ghost.ellipse((ghost_x - 35, ghost_y - 105, ghost_x + 35, ghost_y - 35), fill=(195, 220, 205, 45))
    ghost.rectangle((ghost_x - 48, ghost_y - 40, ghost_x + 48, ghost_y + 130), fill=(180, 205, 190, 35))
    ghost_layer = ghost_layer.filter(ImageFilter.GaussianBlur(8))
    image = Image.alpha_composite(image.convert("RGBA"), ghost_layer).convert("RGB")
    draw = ImageDraw.Draw(image)

    fog = Image.new("RGBA", size, (0, 0, 0, 0))
    fog_draw = ImageDraw.Draw(fog)
    for _ in range(12):
        cx = random.randint(int(width * 0.05), int(width * 0.95))
        cy = random.randint(int(height * 0.16), int(height * 0.76))
        radius = random.randint(int(width * 0.08), int(width * 0.22))
        fog_draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(130, 170, 150, random.randint(10, 24)))
    fog = fog.filter(ImageFilter.GaussianBlur(55))
    image = Image.alpha_composite(image.convert("RGBA"), fog).convert("RGB")

    light_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    light = ImageDraw.Draw(light_layer)
    light.ellipse(box(0.20, 0.18, 0.80, 0.70), fill=(80, 110, 92, 38))
    light_layer = light_layer.filter(ImageFilter.GaussianBlur(80))
    image = Image.alpha_composite(image.convert("RGBA"), light_layer).convert("RGB")

    vignette = Image.new("L", size, 0)
    vg = ImageDraw.Draw(vignette)
    vg.ellipse((-width * 0.28, -height * 0.12, width * 1.28, height * 1.08), fill=210)
    vignette = vignette.filter(ImageFilter.GaussianBlur(95))
    dark = Image.new("RGB", size, (0, 0, 0))
    image = Image.composite(image, dark, vignette.point(lambda p: min(255, p + 35)))
    image = ImageEnhance.Contrast(image).enhance(1.22)
    image = ImageEnhance.Color(image).enhance(0.72)
    image = ImageEnhance.Sharpness(image).enhance(1.25)
    grain = Image.effect_noise(size, 18).convert("L")
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    image = Image.blend(image, grain_rgb, 0.045)
    image = image.filter(ImageFilter.GaussianBlur(0.25))
    draw = ImageDraw.Draw(image)

    image.save(path, quality=95)


def ai_image_prompt(scene, story, size):
    width, height = size
    aspect = "vertical 9:16 composition, 1080x1920" if height > width else "wide horizontal 16:9 composition, 1920x1080"
    narration = scene["narration"][:260]
    return " ".join([
        "Photorealistic Thai supernatural horror movie still.",
        aspect + ".",
        "Looks like a real film frame, realistic adult Thai people, natural body proportions, cinematic lens, practical lighting, detailed location.",
        f"Scene must show: {scene['visual']}.",
        f"Story narration context: {narration}.",
        "Mysterious, frightening, suspenseful, no gore.",
        "All documents, labels, signs, screens, tickets and pages must be blank, turned away, or unreadably blurred.",
        "No children, no extra unrelated people, no cartoon, no illustration, no anime, no text, no subtitles, no letters, no numbers, no watermark, no logo, no stretched faces, no deformed bodies.",
    ])


def image_looks_bad(image):
    small = image.resize((96, 96), Image.Resampling.BILINEAR).convert("RGB")
    pixels = list(small.getdata())
    if not pixels:
        return True

    bright = 0
    saturated = 0
    very_blue_or_magenta = 0
    total_brightness = 0
    for red, green, blue in pixels:
        maximum = max(red, green, blue)
        minimum = min(red, green, blue)
        total_brightness += (red + green + blue) / 3
        if maximum - minimum > 92:
            saturated += 1
        if maximum > 215:
            bright += 1
        if blue > 135 and red > 95 and green < 105:
            very_blue_or_magenta += 1

    total = len(pixels)
    average_brightness = total_brightness / total
    saturated_ratio = saturated / total
    bright_ratio = bright / total
    magenta_ratio = very_blue_or_magenta / total

    # Pollinations sometimes returns abstract neon/error-like frames. Those are
    # valid image files, so catch the visual signature before it reaches video.
    if average_brightness > 150 and saturated_ratio > 0.42:
        return True
    if saturated_ratio > 0.58:
        return True
    if magenta_ratio > 0.28 and bright_ratio > 0.18:
        return True
    return False


def save_previous_background(previous_path, path, size):
    if not previous_path or not Path(previous_path).exists():
        return False
    image = Image.open(previous_path).convert("RGB")
    image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Color(image).enhance(0.92)
    image = ImageEnhance.Sharpness(image).enhance(1.05)
    image.save(path, quality=94)
    return True


def download_ai_background(path, scene, story, size):
    prompt = ai_image_prompt(scene, story, size)
    seed_text = f"{story['title']}|{scene['number']}|{scene['narration']}"
    base_seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:12], 16) % 999999999
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt, safe="")
    for attempt in range(4):
        params = urllib.parse.urlencode({
            "width": size[0],
            "height": size[1],
            "seed": (base_seed + attempt * 104729) % 999999999,
            "model": "flux",
            "nologo": "true",
            "private": "true",
            "enhance": "true",
        })
        request = urllib.request.Request(
            f"{url}?{params}",
            headers={"User-Agent": "Codex-Horror-AutoFilm/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if len(data) < 12000:
                continue
            image = Image.open(BytesIO(data)).convert("RGB")
            image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            if image_looks_bad(image):
                continue
            image = ImageEnhance.Contrast(image).enhance(1.10)
            image = ImageEnhance.Color(image).enhance(0.86)
            image = ImageEnhance.Sharpness(image).enhance(1.08)
            image.save(path, quality=94)
            return True
        except Exception:
            continue
    return False


def create_background(path, scene, story, size, previous_path=None):
    if download_ai_background(path, scene, story, size):
        return "ai"
    if save_previous_background(previous_path, path, size):
        return "previous"
    draw_horror_background(path, scene, story, size)
    return "fallback"


def subtitle_chunks(text, max_chars):
    chunks = []
    current = ""
    normalized = " ".join(text.replace("...", "…").split())
    for word in normalized.split(" "):
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks or [normalized]


def subtitle_durations(chunks, total_duration):
    weights = [max(8, len(chunk)) for chunk in chunks]
    weight_total = sum(weights) or 1
    durations = [max(0.8, total_duration * weight / weight_total) for weight in weights]
    drift = total_duration - sum(durations)
    durations[-1] = max(0.8, durations[-1] + drift)
    return durations


def render_text_frame(base_path, output_path, scene, story, size, work, subtitle_text=None, show_title=False):
    width, height = size
    is_vertical = height > width
    title_size = 58 if is_vertical else 48
    sub_size = 42 if is_vertical else 34
    title_html = f'<div class="title">{html.escape(story["title"])}</div>' if show_title else ""
    subtitle = subtitle_text if subtitle_text is not None else scene["narration"]
    html_path = work / f"frame-{scene['number']:02d}.html"
    html_path.write_text(f"""<!doctype html>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    background: #050807;
    font-family: "Thonburi", "Sarabun", sans-serif;
  }}
  .bg {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }}
  .title {{
    position: absolute;
    top: {185 if is_vertical else 74}px;
    left: {110 if is_vertical else 270}px;
    right: {110 if is_vertical else 270}px;
    color: #f6f0e8;
    font-size: {title_size}px;
    line-height: 1.28;
    font-weight: 700;
    text-align: center;
    text-wrap: balance;
    overflow-wrap: anywhere;
    text-shadow: 0 5px 12px #000, 0 0 4px #000, 0 0 18px rgba(229, 200, 142, .34);
  }}
  .subtitle {{
    position: absolute;
    left: {82 if is_vertical else 180}px;
    right: {82 if is_vertical else 180}px;
    bottom: {118 if is_vertical else 72}px;
    color: #fffdf5;
    font-size: {sub_size}px;
    line-height: 1.35;
    font-weight: 650;
    text-align: center;
    text-wrap: balance;
    overflow-wrap: anywhere;
    text-shadow: 0 5px 12px #000, 0 0 4px #000, 0 0 16px rgba(0, 0, 0, .88);
  }}
  .shade {{
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 48% 42%, transparent 0 34%, rgba(0,0,0,.18) 58%, rgba(0,0,0,.52) 100%),
      linear-gradient(to bottom, rgba(0,0,0,.12), transparent 25%, transparent 62%, rgba(0,0,0,.40));
    mix-blend-mode: multiply;
  }}
  .film {{
    position: absolute;
    inset: 0;
    opacity: .16;
    background:
      repeating-linear-gradient(0deg, rgba(255,255,255,.05) 0, rgba(255,255,255,.05) 1px, transparent 1px, transparent 5px);
    pointer-events: none;
  }}
</style>
<img class="bg" src="{base_path.resolve().as_uri()}">
<div class="shade"></div>
<div class="film"></div>
{title_html}
<div class="subtitle">{html.escape(subtitle)}</div>
""", encoding="utf-8")

    if not CHROME.exists():
        shutil.copyfile(base_path, output_path)
        return

    run([
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--allow-file-access-from-files",
        f"--screenshot={output_path}",
        f"--window-size={width},{height}",
        html_path.resolve().as_uri(),
    ])


def render_overlay_frame(output_path, scene, story, size, work, subtitle_text=None, show_title=False):
    width, height = size
    is_vertical = height > width
    title_size = 58 if is_vertical else 48
    sub_size = 42 if is_vertical else 34
    title_html = f'<div class="title">{html.escape(story["title"])}</div>' if show_title else ""
    subtitle = subtitle_text if subtitle_text is not None else scene["narration"]
    html_path = work / f"overlay-{scene['number']:02d}.html"
    html_path.write_text(f"""<!doctype html>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    background: transparent;
    font-family: "Thonburi", "Sarabun", sans-serif;
  }}
  .wrap {{
    position: relative;
    width: 100%;
    height: 100%;
    background: transparent;
  }}
  .title {{
    position: absolute;
    top: {185 if is_vertical else 74}px;
    left: {110 if is_vertical else 270}px;
    right: {110 if is_vertical else 270}px;
    color: #f6f0e8;
    font-size: {title_size}px;
    line-height: 1.28;
    font-weight: 700;
    text-align: center;
    text-wrap: balance;
    overflow-wrap: anywhere;
    text-shadow: 0 5px 12px #000, 0 0 4px #000, 0 0 18px rgba(229, 200, 142, .34);
  }}
  .subtitle-box {{
    position: absolute;
    left: {62 if is_vertical else 140}px;
    right: {62 if is_vertical else 140}px;
    bottom: {92 if is_vertical else 50}px;
    padding: {16 if is_vertical else 18}px {20 if is_vertical else 24}px;
    border-radius: 20px;
    background: linear-gradient(to bottom, rgba(5, 7, 7, .22), rgba(5, 7, 7, .38));
    box-shadow: 0 20px 48px rgba(0, 0, 0, .2);
    backdrop-filter: blur(2px);
  }}
  .subtitle {{
    color: #fffdf5;
    font-size: {sub_size}px;
    line-height: 1.35;
    font-weight: 650;
    text-align: center;
    text-wrap: balance;
    overflow-wrap: anywhere;
    text-shadow: 0 5px 12px #000, 0 0 4px #000, 0 0 16px rgba(0, 0, 0, .88);
  }}
  .shade {{
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 48% 42%, transparent 0 34%, rgba(0,0,0,.10) 58%, rgba(0,0,0,.24) 100%);
    mix-blend-mode: multiply;
    pointer-events: none;
  }}
</style>
<div class="wrap">
  <div class="shade"></div>
  {title_html}
  <div class="subtitle-box"><div class="subtitle">{html.escape(subtitle)}</div></div>
</div>
""", encoding="utf-8")

    if not CHROME.exists():
        render_pil_overlay_frame(output_path, scene, story, size, subtitle_text=subtitle_text, show_title=show_title)
        return

    run([
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--allow-file-access-from-files",
        "--default-background-color=00000000",
        f"--screenshot={output_path}",
        f"--window-size={width},{height}",
        html_path.resolve().as_uri(),
    ])


def render_pil_overlay_frame(output_path, scene, story, size, subtitle_text=None, show_title=False):
    width, height = size
    is_vertical = height > width
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    subtitle = subtitle_text if subtitle_text is not None else scene["narration"]

    shade = Image.new("RGBA", size, (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    shade_draw.rectangle((0, int(height * 0.68), width, height), fill=(0, 0, 0, 76))
    shade = shade.filter(ImageFilter.GaussianBlur(28))
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image)

    if show_title:
        title_font = load_font(58 if is_vertical else 48)
        title_lines = wrap_text(draw, story["title"], title_font, int(width * (0.78 if is_vertical else 0.66)))
        title_y = 185 if is_vertical else 74
        for line in title_lines[:3]:
            box = draw.textbbox((0, 0), line, font=title_font, stroke_width=3)
            x = (width - (box[2] - box[0])) / 2
            draw.text((x, title_y), line, font=title_font, fill=(246, 240, 232, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
            title_y += (box[3] - box[1]) + 12

    sub_font = load_font(42 if is_vertical else 34)
    max_width = int(width * (0.84 if is_vertical else 0.76))
    lines = wrap_text(draw, subtitle, sub_font, max_width)
    lines = lines[:3 if is_vertical else 2]
    line_heights = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=sub_font, stroke_width=3)
        line_heights.append(box[3] - box[1])
    total_height = sum(line_heights) + max(0, len(lines) - 1) * 10
    y = height - (118 if is_vertical else 72) - total_height
    for line, line_height in zip(lines, line_heights):
        box = draw.textbbox((0, 0), line, font=sub_font, stroke_width=3)
        x = (width - (box[2] - box[0])) / 2
        draw.text((x, y), line, font=sub_font, fill=(255, 253, 245, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
        y += line_height + 10

    image.save(output_path)


def render_motion_video(base_path, output_path, size, duration, seed_text, fps=30, preset="veryfast", crf="22"):
    width, height = size
    frames = max(1, math.ceil(duration * fps))
    fade_out_start = max(0, duration - 0.35)
    rng = random.Random(seed_text)
    zoom_start = 1.024 + rng.random() * 0.020
    zoom_speed = 0.000014 + rng.random() * 0.000014
    x_wave_a = rng.choice([-1, 1]) * (7.5 + rng.randint(0, 7))
    x_wave_b = rng.choice([-1, 1]) * (3.2 + rng.randint(0, 5))
    y_wave_a = rng.choice([-1, 1]) * (5.4 + rng.randint(0, 6))
    y_wave_b = rng.choice([-1, 1]) * (2.2 + rng.randint(0, 4))
    x_freq_a = 26 + rng.randint(0, 28)
    x_freq_b = 16 + rng.randint(0, 18)
    y_freq_a = 30 + rng.randint(0, 30)
    y_freq_b = 18 + rng.randint(0, 18)
    vf = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='{zoom_start}+{zoom_speed}*on':"
        f"x='iw/2-(iw/zoom/2)+{x_wave_a}*sin(on/{x_freq_a})+{x_wave_b}*sin(on/{x_freq_b})':"
        f"y='ih/2-(ih/zoom/2)+{y_wave_a}*cos(on/{y_freq_a})+{y_wave_b}*sin(on/{y_freq_b})':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"scale=w='iw*(1.014+0.0045*sin(n/45))':h='ih*(1.014+0.0035*cos(n/53))':eval=frame,"
        f"crop={width}:{height},"
        "setsar=1,"
        "tmix=frames=4:weights='1 1 1 1',"
        "eq=contrast=1.03:saturation=1.0:brightness=0.0,"
        "vignette=PI/5.2,"
        "noise=alls=3:allf=t+u,"
        "unsharp=5:5:0.22:3:3:0.08,"
        "gblur=sigma=0.28,"
        f"fade=t=in:st=0:d=0.22,fade=t=out:st={fade_out_start:.3f}:d=0.35,"
        "format=yuv420p[vout]"
    )
    run([
        FFMPEG, "-y", "-loop", "1", "-i", str(base_path),
        "-filter_complex", vf, "-map", "[vout]", "-frames:v", str(frames), "-an",
        "-c:v", "libx264", "-preset", preset, "-crf", crf, str(output_path),
    ])


def make_narration(text, output):
    raw_output = output.with_name(f"{output.stem}-raw.aiff")
    if Path(SAY).exists() and Path(SAY).name == "say":
        for voice in (VOICE, "Kanya"):
            raw_output.unlink(missing_ok=True)
            run([SAY, "-v", voice, "-r", "124", "-o", str(raw_output), text])
            if raw_output.exists() and raw_output.stat().st_size > 12000:
                break
        else:
            raise RuntimeError("สร้างเสียงพากย์ไม่สำเร็จ ไฟล์เสียงที่ระบบได้กลับมาว่างหรือเสีย")
        input_audio = raw_output
    else:
        raw_output = output.with_name(f"{output.stem}-raw.mp3")
        raw_output.unlink(missing_ok=True)
        asyncio.run(_make_narration_edge_tts(text, raw_output))
        input_audio = raw_output

    run([
        FFMPEG, "-y", "-i", str(input_audio),
        "-af",
        "highpass=f=70,lowpass=f=6400,"
        "equalizer=f=150:t=q:w=1.0:g=3.0,"
        "equalizer=f=260:t=q:w=1.1:g=2.0,"
        "equalizer=f=3300:t=q:w=1.2:g=-1.2,"
        "acompressor=threshold=-20dB:ratio=2.2:attack=8:release=150,"
        "volume=1.18",
        str(output),
    ])
    if not output.exists() or output.stat().st_size < 12000:
        raise RuntimeError("แปลงเสียงพากย์ไม่สำเร็จ ไฟล์เสียงสั้นหรือเสียผิดปกติ")


async def _make_narration_edge_tts(text, output):
    try:
        import edge_tts
    except Exception as error:
        raise RuntimeError(
            "ไม่พบ edge-tts สำหรับรันบนคลาวด์ "
            "ติดตั้ง requirements.txt ให้ครบก่อน"
        ) from error

    voices = [
        "en-US-GuyNeural",
        "en-US-ChristopherNeural",
        "en-US-EricNeural",
        "th-TH-NiwatNeural",
        "th-TH-PremwadeeNeural",
    ]
    last_error = None
    for voice in voices:
        try:
            communicate = edge_tts.Communicate(text, voice=voice, rate="-8%", pitch="-2Hz")
            await communicate.save(str(output))
            if output.exists() and output.stat().st_size > 12000:
                return
        except Exception as error:
            last_error = error
    raise RuntimeError(f"สร้างเสียงพากย์บนคลาวด์ไม่สำเร็จ: {last_error}")


def render_video(payload, avoid=None, batch_index=None):
    mode = payload.get("mode") if payload.get("mode") in {"short", "long"} else "short"
    brief = payload.get("brief", "")
    story = make_story(mode, brief, avoid=avoid)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    unique_id = random.randint(1000, 9999)
    work = RENDERS / f"job-{stamp}-{unique_id}"
    work.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(exist_ok=True)

    size = (1080, 1920) if mode == "short" else (1600, 900)
    fps = 30 if mode == "short" else 24
    motion_preset = "veryfast" if mode == "short" else "ultrafast"
    segment_preset = "veryfast" if mode == "short" else "ultrafast"
    segment_crf = "22" if mode == "short" else "24"
    segments = []
    audios = []
    durations = []
    last_good_background = work / "last-good-background.jpg"

    for scene in story["scenes"]:
        base_path = work / f"base-{scene['number']:02d}.jpg"
        audio_path = work / f"voice-{scene['number']:02d}.aiff"
        motion_path = work / f"motion-{scene['number']:02d}.mp4"
        overlay_path = work / f"overlay-{scene['number']:02d}.png"
        video_path = work / f"segment-{scene['number']:02d}.mp4"

        background_source = create_background(base_path, scene, story, size, last_good_background)
        if background_source == "ai":
            shutil.copy2(base_path, last_good_background)
        make_narration(scene["narration"], audio_path)
        duration = ffprobe_duration(audio_path)
        durations.append(duration)
        audios.append(audio_path)

        render_motion_video(
            base_path,
            motion_path,
            size,
            duration,
            f"{story['title']}:{scene['number']}",
            fps=fps,
            preset=motion_preset,
            crf=segment_crf,
        )
        render_overlay_frame(
            overlay_path,
            scene,
            story,
            size,
            work,
            subtitle_text=scene["narration"],
            show_title=scene["number"] == 1,
        )
        run([
            FFMPEG, "-y",
            "-i", str(motion_path),
            "-loop", "1",
            "-i", str(overlay_path),
            "-filter_complex",
            "[0:v][1:v]overlay=0:0:format=auto:shortest=1[vout]",
            "-map", "[vout]",
            "-an",
            "-c:v", "libx264", "-preset", segment_preset, "-crf", segment_crf, "-pix_fmt", "yuv420p",
            str(video_path),
        ])
        for temp_path in (base_path, motion_path, overlay_path):
            temp_path.unlink(missing_ok=True)
        segments.append(video_path)

    video_list = work / "videos.txt"
    audio_list = work / "audios.txt"
    video_list.write_text("".join(f"file '{path}'\n" for path in segments), encoding="utf-8")
    audio_list.write_text("".join(f"file '{path}'\n" for path in audios), encoding="utf-8")

    video_track = work / "video-track.mp4"
    narration = work / "narration.aac"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(video_list), "-c", "copy", str(video_track)])
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list), "-c:a", "aac", "-b:a", "160k", str(narration)])
    for path in segments:
        path.unlink(missing_ok=True)

    total_duration = sum(durations)
    music = work / "horror-music.aac"
    sfx = work / "horror-sfx.aac"
    fade_out = max(0, total_duration - 3)
    expression = "0.135*sin(2*PI*43*t)+0.078*sin(2*PI*69*t)+0.052*sin(2*PI*(94+7*sin(2*PI*0.045*t))*t)"
    run([
        FFMPEG, "-y", "-f", "lavfi", "-i",
        f"aevalsrc={expression}:s=44100:d={total_duration:.3f}",
        "-af", f"highpass=f=28,lowpass=f=5200,afade=t=in:st=0:d=2,afade=t=out:st={fade_out:.3f}:d=3",
        "-c:a", "aac", "-b:a", "128k", str(music),
    ])
    sfx_expression = "0.040*sin(2*PI*31*t)+0.034*sin(2*PI*57*t)+0.048*sin(2*PI*(118+11*sin(2*PI*0.038*t))*t)"
    run([
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"aevalsrc={sfx_expression}:s=44100:d={total_duration:.3f}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.055:d={total_duration:.3f}",
        "-filter_complex",
        f"[0:a][1:a]amix=inputs=2:duration=first,highpass=f=45,lowpass=f=3600,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out:.3f}:d=3[aout]",
        "-map", "[aout]", "-c:a", "aac", "-b:a", "128k", str(sfx),
    ])

    story_part = f"story-{batch_index}-" if batch_index else ""
    file_name = f"autofilm-horror-{mode}-{story_part}{stamp}-{unique_id}.mp4"
    output = RENDERS / file_name
    run([
        FFMPEG, "-y",
        "-i", str(video_track),
        "-i", str(narration),
        "-i", str(music),
        "-i", str(sfx),
        "-filter_complex",
        "[1:a]volume=1.28,asplit=3[a_voice][voice_sc_music][voice_sc_sfx];"
        "[2:a]volume=1.25[a_music_raw];"
        "[a_music_raw][voice_sc_music]sidechaincompress=threshold=0.042:ratio=2.8:attack=18:release=420:makeup=1[a_music];"
        "[3:a]volume=0.66[a_sfx_raw];"
        "[a_sfx_raw][voice_sc_sfx]sidechaincompress=threshold=0.042:ratio=4.8:attack=8:release=280:makeup=1[a_sfx];"
        "[a_voice][a_music][a_sfx]amix=inputs=3:duration=first:dropout_transition=0,"
        "acompressor=threshold=-18dB:ratio=1.9:attack=8:release=160,alimiter=limit=0.94[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(output),
    ])

    story["targetSeconds"] = round(ffprobe_duration(output), 1)
    return story, file_name


def render_video_batch(payload):
    count = max(1, min(2, int(payload.get("count", 1) or 1)))
    results = []
    avoid = {
        "titles": set(),
        "places": set(),
        "patterns": set(),
    }
    for index in range(1, count + 1):
        story, file_name = render_video(payload, avoid=avoid, batch_index=index if count > 1 else None)
        seed = story.get("seed", {})
        avoid["titles"].add(story.get("title", ""))
        avoid["places"].add(seed.get("placeTitle", ""))
        avoid["patterns"].add(seed.get("pattern", ""))
        results.append({
            "fileName": file_name,
            "videoUrl": f"/renders/{file_name}",
            "downloadUrl": f"/download/{file_name}",
            "story": story,
        })
    return results


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in {"/api/generate-video", "/api/save-video"}:
            self.send_error(404, "Not found")
            return

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")

            if parsed.path == "/api/save-video":
                file_name = Path(str(payload.get("fileName", ""))).name
                source = RENDERS / file_name
                if not file_name or source.suffix.lower() != ".mp4" or not source.exists():
                    self.send_error(404, "Video not found")
                    return

                target = unique_download_path(file_name)
                shutil.copy2(source, target)
                body = json.dumps({
                    "ok": True,
                    "savedName": target.name,
                    "savedPath": str(target),
                }, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            videos = render_video_batch(payload)
            first = videos[0]
            body = json.dumps({
                "ok": True,
                "fileName": first["fileName"],
                "videoUrl": first["videoUrl"],
                "downloadUrl": first["downloadUrl"],
                "story": first["story"],
                "videos": videos,
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            body = message.encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/download/"):
            name = Path(urllib.parse.unquote(parsed.path.removeprefix("/download/"))).name
            file_path = RENDERS / name
            if not file_path.exists() or file_path.suffix.lower() != ".mp4":
                self.send_error(404, "Video not found")
                return

            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(file_path.stat().st_size))
            self.end_headers()
            with file_path.open("rb") as video:
                shutil.copyfileobj(video, self.wfile)
            return

        super().do_GET()


def main():
    RENDERS.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Horror AutoFilm running at http://127.0.0.1:{PORT}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
