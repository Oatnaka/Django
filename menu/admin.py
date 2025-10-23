from django.contrib import admin
from django.contrib import messages
# *** 1. Import โมเดลทั้งหมดที่ต้องการจัดการใน Admin ***
from .models import Category, MenuItem, GalleryImage, Reservation 

# ---------------------------------
# 1. การจัดการหมวดหมู่ (Category)
# ---------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    

# ---------------------------------
# 2. การจัดการรายการอาหาร (MenuItem)
# ---------------------------------
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_special', 'is_available')
    list_filter = ('category', 'is_special', 'is_available') 
    search_fields = ('name', 'description')
    ordering = ('category', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price', 'category', 'image'),
        }),
        ('สถานะ', {
            'fields': ('is_special', 'is_available'), 
            'classes': ('collapse',), 
        })
    )

# ---------------------------------
# *** 3. การจัดการรูปภาพแกลเลอรี (GalleryImage) ***
# ---------------------------------
@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_visible')
    list_filter = ('is_visible',)
    search_fields = ('title',)
    ordering = ('order', 'title')

# ---------------------------------
# *** 4. การจัดการการจองโต๊ะ (Reservation) ***
# ---------------------------------
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    # คอลัมน์ที่แสดงในหน้ารายการ: เพิ่ม assigned_table และ is_takeaway
    list_display = ('name', 'phone', 'date', 'time', 'party_size', 'is_takeaway', 'is_confirmed', 'assigned_table', 'reserved_at')
    
    # ตัวกรอง: เพิ่ม is_takeaway และ assigned_table
    list_filter = ('date', 'is_confirmed', 'is_takeaway', 'assigned_table')
    
    search_fields = ('name', 'phone', 'email')
    ordering = ('-date', '-time')
    
    # list_editable สำหรับการจอง/สั่ง ไม่ควรแก้ไข is_confirmed ตรงๆ
    # (เพราะต้องมีการเลือก assigned_table ก่อน) จึงแนะนำให้ลบ list_editable ออก
    # list_editable = ('is_confirmed',) 
    
    fieldsets = (
        ('ข้อมูลลูกค้า', {
            'fields': ('name', 'phone', 'email'),
        }),
        ('รายละเอียดการจอง/สั่ง', {
            'fields': ('date', 'time', 'party_size', 'is_takeaway', 'special_requests'), # เพิ่ม is_takeaway
        }),
        ('สถานะการจัดการ (สำหรับร้าน)', {
            # *** เพิ่ม assigned_table เข้าไปในส่วนที่ Admin จัดการ ***
            'fields': ('is_confirmed', 'assigned_table'), 
        })
    )
    
    # *** (Optional) เพิ่ม Logic ตรวจสอบการเลือกโต๊ะเมื่อยืนยัน ***
    def save_model(self, request, obj, form, change):
        # 1. หากกดยืนยัน (is_confirmed) และไม่ใช่รายการสั่งกลับบ้าน (not is_takeaway)
        # 2. แต่ไม่ได้มีการเลือก assigned_table
        if obj.is_confirmed and not obj.is_takeaway and not obj.assigned_table:
             # การยกเลิกการบันทึกทำได้ยากใน save_model แต่เราสามารถส่งข้อความแจ้งเตือนได้
             # ในสถานการณ์จริง การบังคับใช้ควรทำผ่านฟอร์ม/Clean Method 
             # แต่ใน admin เราใช้ messages แจ้งเตือนเพื่อให้ Admin รับทราบ
            messages.warning(request, "⚠️ การจองโต๊ะได้รับการยืนยันแล้ว กรุณาเลือก 'หมายเลขโต๊ะที่จัดสรร' เพื่อให้สถานะโต๊ะว่างถูกต้อง.")
            
        super().save_model(request, obj, form, change)