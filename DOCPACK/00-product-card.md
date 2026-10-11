---
title: solo-time — Product Card
doc_id: CARD-solo-time
doc_type: product-card
verdict: showcase
version: 0.1
date: 2026-10-11
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# solo-time — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ช่วยเจ้าของ Solo Empire บันทึกเวลาที่ใช้ต่องาน (task) ผ่าน API ของ cell เอง

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ปัญหา: ตาราง time_entries/time_logs เดิมอยู่ใน SQLite ส่วนกลาง
- ผู้ใช้: เจ้าของคนเดียว (internal)

## 3. สิ่งที่ทำได้จริงตอนนี้

- API `/v1/time-entries` (กรอง `task_id`; มี `started_at`, `ended_at`, `duration_seconds`) และ `/v1/time-logs`
- ไม่มี publisher

## 4. หลักฐานสถานะ

| รายการ | ค่า (ตรวจจาก repository) |
|---|---|
| Stack | FastAPI, Python |
| Commits | 2 (แรก 2026-10-11 → ล่าสุด 2026-10-11) |
| Source | ประมาณ 2,208 บรรทัดใน 15 ไฟล์ (ไม่รวมเทสต์) — ส่วนใหญ่มาจาก template cellkit ร่วมกัน |
| Tests | 2 ไฟล์ |
| CI | ไม่มี |
| Deploy config | Dockerfile + Railway (ตาม README); ไม่ได้ตรวจ deploy จริงในรอบนี้ |
| Live URL | ไม่มี (ไม่ได้ตรวจ) |
| README | 35 บรรทัด |

## 5. คุณค่าและจุดต่าง

- แยกเป็น 1 cell = 1 repo / 1 backend / 1 Neon database ตามแนว decentralize ของ Solo Empire; ใช้ identity, authorization, executions และ audit ของ `empire-platform` ผ่าน HTTP ด้วย token ของผู้เรียก ไม่เก็บ provider token เอง
- มุมรายได้: ไม่มี — เป็นโครงสร้างภายในของเจ้าของ แต่ pattern สร้าง cell จาก `cell.yaml` ด้วย `solo-cell-kit` ใช้ซ้ำได้ **[สมมติฐาน]**

## 6. ช่องว่างสำคัญ

- `cell.yaml` ระบุว่าโดเมนนี้ไม่มีข้อมูลเลยตอนออกจาก control plane (2026-10-11) — ยังไม่มีการใช้งานจริง
- ไม่มี CI
- ยังไม่มีเอกสารนอกจาก README

## 7. คำตัดสิน

**`showcase`** — Cell ว่างที่มี schema พร้อม แต่ยังไม่มีข้อมูลหรือผู้ใช้ ไม่ใช่ผลิตภัณฑ์ จะเปลี่ยนเป็น `archive` ถ้าไม่มีแผนติดตามเวลา หรือเป็น `invest` ถ้าเริ่มใช้จริงต่อเนื่อง

## 8. ขั้นต่อไป

1. ตัดสินใจว่าจะใช้ติดตามเวลาจริงหรือไม่ — ถ้าไม่ ให้เสนอ archive
2. เพิ่ม CI รัน `pytest` หากเก็บไว้

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `cell.yaml`
- `tests/test_contract.py`, `migrations/`, `Dockerfile`
