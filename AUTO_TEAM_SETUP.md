# Horror AutoFilm Auto Team

ระบบนี้ทำงานแบบทีมงานอัตโนมัติ:

1. สุ่มเรื่องผี
2. สร้างภาพ AI
3. ทำเสียงเล่า
4. ตัดต่อวิดีโอ
5. บันทึก log
6. อัปโหลด YouTube ได้หลังเชื่อม OAuth

## ไฟล์สำคัญ

- `auto_worker.py` รันงานอัตโนมัติ
- `auto_config.json` ตั้งค่าโหมด จำนวนคลิป และ YouTube
- `youtube_uploader.py` อัปโหลด YouTube
- `requirements-youtube.txt` dependencies สำหรับ YouTube API
- `automation_log.jsonl` log ที่จะถูกสร้างเมื่อรันงาน

## รันสร้างวิดีโออัตโนมัติ 1 รอบ

```bash
python3 auto_worker.py --once --no-upload
```

ค่าเริ่มต้นใน `auto_config.json` คือสร้าง 1 วิดีโอแบบ `short`

## เปิด YouTube Upload

ต้องทำครั้งแรก:

1. สร้าง OAuth Client ใน Google Cloud
2. เปิด YouTube Data API v3
3. ดาวน์โหลดไฟล์ OAuth แล้ววางในโปรเจกต์ชื่อ `client_secrets.json`
4. ติดตั้ง dependency:

```bash
pip install -r requirements-youtube.txt
```

5. รันครั้งแรก:

```bash
python3 auto_worker.py --once --upload
```

ระบบจะเปิดหน้า login Google เพื่ออนุญาตอัปโหลด YouTube ครั้งแรก แล้วจะสร้าง `youtube_token.json` ไว้ใช้รอบถัดไป

## รันตามเวลาอัตโนมัติ

ระบบตั้งค่าไว้ใน `auto_config.json` ให้สร้างและอัปโหลดวันละ 3 รอบตามเวลาไทย:

- `06:00`
- `11:00`
- `18:00`

คำสั่งรันตามตาราง:

```bash
python3 auto_worker.py --schedule --upload
```

## ค่าปลอดภัย

ค่าเริ่มต้นของ YouTube ตั้งไว้เป็น `public` และติ๊ก `containsSyntheticMedia` เพื่อให้ระบบอัปโหลดคลิป AI แบบอัตโนมัติ

เปลี่ยนใน `auto_config.json` ได้:

```json
"privacyStatus": "public"
```

ค่าที่ใช้ได้คือ `private`, `unlisted`, `public`

## Deploy บน Render

มี `render.yaml` สำหรับแยกเป็น 2 service:

- web service: เปิดเว็บ UI และ API สร้างวิดีโอ
- worker service: รันงานออโต้และอัปโหลด YouTube

ทั้งสอง service ใช้ `requirements.txt` ร่วมกัน

### ค่าลับที่ต้องใส่ใน Render Environment

อย่า commit `client_secrets.json` หรือ `youtube_token.json` ขึ้น GitHub ให้เปิดไฟล์ในเครื่องแล้วคัดลอกเนื้อหาทั้งไฟล์ไปใส่เป็น Environment Variable:

- `YOUTUBE_CLIENT_SECRETS_JSON` = เนื้อหาใน `client_secrets.json`
- `YOUTUBE_TOKEN_JSON` = เนื้อหาใน `youtube_token.json`

ระบบจะสร้างไฟล์ลับสองไฟล์นี้ขึ้นในเครื่อง Render เองตอนเริ่มทำงาน

### หลัง deploy

worker จะรันคำสั่งนี้เอง:

```bash
python3 auto_worker.py --schedule --upload
```

ค่าเริ่มต้นคือสร้างคลิป `short` รอบละ 1 คลิป วันละ 3 รอบ เวลา `06:00`, `11:00`, `18:00` ตามเวลาไทย แล้วอัปโหลด YouTube เป็น `public` พร้อมระบุว่าเป็น AI video

## ใช้ GitHub Actions แบบไม่ต้องใส่บัตร

ถ้าไม่อยากใช้ Render paid worker ให้ใช้ GitHub Actions แทน ไฟล์ตั้งเวลาอยู่ที่ `.github/workflows/auto-youtube.yml`

GitHub Actions จะรันวันละ 3 รอบตามเวลาไทย:

- `06:00`
- `11:00`
- `18:00`

และยังมีปุ่ม `Run workflow` ให้กดทดสอบเองได้

### ตั้งค่า Secrets ใน GitHub

ไปที่ GitHub repo > `Settings` > `Secrets and variables` > `Actions` > `New repository secret`

เพิ่ม 2 ค่า:

- `YOUTUBE_CLIENT_SECRETS_JSON` = เนื้อหาใน `client_secrets.json`
- `YOUTUBE_TOKEN_JSON` = เนื้อหาใน `youtube_token.json`

workflow จะรันคำสั่งนี้ทุกครั้ง:

```bash
python3 auto_worker.py --once --upload
```

แปลว่ารอบละ 1 คลิปใหม่ ไม่ใช้วิดีโอเดิมซ้ำ
