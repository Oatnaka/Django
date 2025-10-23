from django.db import models
from django.conf import settings
# ⭐️ เปลี่ยนจากการ import requests เป็น line-bot-sdk ⭐️
from linebot import LineBotApi
from linebot.models import TextMessage
from datetime import datetime

# -------------------------------------------------------------
# 1. โมเดลเมนูและแกลเลอรี (โค้ดเดิม)
# -------------------------------------------------------------

class Category(models.Model):
    """
    โมเดลสำหรับหมวดหมู่หลักของเมนูอาหาร (เช่น อาหารจานหลัก, ของหวาน)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='ชื่อหมวดหมู่')
    description = models.TextField(blank=True, null=True, verbose_name='คำอธิบายหมวดหมู่')

    class Meta:
        verbose_name = 'หมวดหมู่'
        verbose_name_plural = 'หมวดหมู่'

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    """
    โมเดลสำหรับรายการอาหารแต่ละรายการ
    """
    # เชื่อมโยงกับโมเดล Category แบบ One-to-Many
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='หมวดหมู่'
    )
    name = models.CharField(max_length=200, verbose_name='ชื่ออาหาร')
    description = models.TextField(verbose_name='คำอธิบาย')
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='ราคา (บาท)')
    
    # คุณสมบัติเพิ่มเติม
    is_available = models.BooleanField(default=True, verbose_name='พร้อมจำหน่าย')
    is_special = models.BooleanField(default=False, verbose_name='เมนูแนะนำพิเศษ')
    image = models.ImageField(
        upload_to='menu_images/', 
        blank=True, 
        null=True,
        verbose_name='รูปภาพอาหาร'
    )

    class Meta:
        verbose_name = 'รายการอาหาร'
        verbose_name_plural = 'รายการอาหาร'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name
    
class GalleryImage(models.Model):
    """
    โมเดลสำหรับจัดเก็บรูปภาพในหน้าแกลเลอรี
    """
    title = models.CharField(
        max_length=100,
        verbose_name='ชื่อรูปภาพ/คำบรรยายสั้น'
    )
    image = models.ImageField(
        upload_to='gallery_images/', 
        verbose_name='รูปภาพแกลเลอรี'
    )
    # ใช้สำหรับจัดเรียงรูปภาพ
    order = models.IntegerField(
        default=0,
        verbose_name='ลำดับการแสดงผล'
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name='แสดงผลในหน้าเว็บ'
    )

    class Meta:
        verbose_name = 'รูปภาพแกลเลอรี'
        verbose_name_plural = 'รูปภาพแกลเลอรี'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

# -------------------------------------------------------------
# 2. โมเดลการจอง (Reservation) พร้อมฟังก์ชัน LINE Messaging API
# -------------------------------------------------------------

class Reservation(models.Model):
    """
    โมเดลสำหรับจัดเก็บข้อมูลการจองโต๊ะและการสั่งกลับบ้าน พร้อมแจ้งเตือน LINE
    """
    # 1. ข้อมูลลูกค้า
    name = models.CharField(max_length=100, verbose_name='ชื่อผู้จอง')
    phone = models.CharField(max_length=15, verbose_name='เบอร์โทรศัพท์')
    email = models.EmailField(blank=True, null=True, verbose_name='อีเมล (ถ้ามี)')
    
    # 2. รายละเอียดการจอง/สั่ง
    date = models.DateField(verbose_name='วันที่')
    time = models.TimeField(verbose_name='เวลา')
    
    party_size = models.IntegerField(
        verbose_name='จำนวนคน (ถ้าจองโต๊ะ)', 
        blank=True, 
        null=True
    ) 
    
    special_requests = models.TextField(blank=True, null=True, verbose_name='คำขอพิเศษ')
    
    is_takeaway = models.BooleanField(default=False, verbose_name='สั่งกลับบ้าน')
    
    # หมายเลขโต๊ะที่จัดสรร (ใช้เพื่อบันทึกการจัดสรรโดย Admin)
    TABLE_CHOICES = [(f'T{i}', f'โต๊ะที่ {i}') for i in range(1, 16)]
    
    assigned_table = models.CharField(
        max_length=5,
        choices=TABLE_CHOICES,
        null=True, 
        blank=True, 
        unique=False, 
        verbose_name="หมายเลขโต๊ะที่จัดสรร"
    )
    
    # 3. สถานะการจัดการ
    is_confirmed = models.BooleanField(default=False, verbose_name='ยืนยันแล้ว')
    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name='สร้างรายการเมื่อ')

    class Meta:
        verbose_name = 'การจอง/สั่ง'
        verbose_name_plural = 'การจอง/สั่ง'
        ordering = ['date', 'time']

    def __str__(self):
        type_label = "สั่งกลับบ้าน 🥡" if self.is_takeaway else "จองโต๊ะ 🍽️"
        return f"{type_label} ของ {self.name} ({self.date.strftime('%d/%m/%Y')} {self.time.strftime('%H:%M')})"

    def send_line_notification(self, message):
        """ฟังก์ชันสำหรับส่งข้อความไปยัง LINE Official Account (Messaging API)"""
        
        # ⭐️ ดึงค่าจาก settings.py ที่แก้ไขไว้ ⭐️
        token = settings.LINE_CHANNEL_ACCESS_TOKEN
        target_id = settings.LINE_NOTIFICATION_TARGET_ID
        
        # ใช้ค่า placeholder จาก settings.py ที่ปลอดภัยกว่า
        if token and target_id and token != 'YOUR_LONG_LIVED_CHANNEL_ACCESS_TOKEN_HERE':
            try:
                # 1. เริ่มต้นใช้งาน LINE BOT API
                line_bot_api = LineBotApi(token)
                
                # 2. สร้างข้อความ
                line_message = TextMessage(text=message)
                
                # 3. ส่งข้อความไปยังเป้าหมาย (User ID หรือ Group ID)
                line_bot_api.push_message(target_id, line_message)
                
            except Exception as e:
                # ใน Production ควรมีการบันทึก Log ข้อผิดพลาด เช่น logging.error(f"LINE API Error: {e}")
                pass


    def save(self, *args, **kwargs):
        is_new = self.pk is None  # ตรวจสอบว่าเป็นการสร้างใหม่หรือไม่
        super().save(*args, **kwargs) # บันทึกข้อมูลการจองก่อน
        
        # ⭐️ ส่งแจ้งเตือน LINE เฉพาะเมื่อมีการสร้างรายการใหม่เท่านั้น ⭐️
        if is_new:
            type_label = "สั่งกลับบ้าน 🥡" if self.is_takeaway else "จองโต๊ะ 🍽️"
            
            # เตรียมข้อความ
            message = (
                f"\n🔔 {type_label} รายการใหม่!"
                f"\n----------------------------------------"
                f"\n👤 ลูกค้า: {self.name}"
                f"\n📞 โทร: {self.phone}"
                f"\n📅 วันที่: {self.date.strftime('%d/%m/%Y')}"
                f"\n⏱️ เวลา: {self.time.strftime('%H:%M น.')}"
            )
            
            if not self.is_takeaway:
                message += f"\n👨‍👩‍👧‍👦 จำนวน: {self.party_size} ท่าน"
            
            if self.special_requests:
                message += f"\n📝 คำขอพิเศษ: {self.special_requests}"
                
            message += (
                f"\n----------------------------------------"
                f"\n🔗 ตรวจสอบ: http://127.0.0.1:8000/admin/menu/reservation/{self.pk}/change/"
            )
            
            # ⭐️ เรียกฟังก์ชันที่ถูกแก้ไขแล้ว ⭐️
            self.send_line_notification(message)


# -------------------------------------------------------------
# 3. โมเดลสถานะโต๊ะ (Table Status) (โค้ดเดิม)
# -------------------------------------------------------------

class Table(models.Model):
    # ... (โค้ดเดิม) ...
    STATUS_CHOICES = [
        ('A', 'ว่าง (Available)'),
        ('O', 'ไม่ว่าง (Occupied)'),
        ('R', 'จองแล้ว (Reserved)'),
        ('C', 'ปิดปรับปรุง (Closed)'),
    ]
    
    # โต๊ะ 1-15 
    TABLE_CHOICES = [(f'T{i}', f'โต๊ะที่ {i}') for i in range(1, 16)]
    
    table_number = models.CharField(
        max_length=5,
        choices=TABLE_CHOICES,
        unique=True,
        verbose_name='หมายเลขโต๊ะ'
    )
    capacity = models.IntegerField(
        default=4,
        verbose_name='ความจุสูงสุด (คน)'
    )
    current_status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='A',
        verbose_name='สถานะปัจจุบัน'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name='อัปเดตล่าสุด'
    )

    class Meta:
        verbose_name = 'สถานะโต๊ะ'
        verbose_name_plural = 'สถานะโต๊ะ'
        ordering = ['table_number']

    def __str__(self):
        return f"{self.table_number} ({self.get_current_status_display()})"