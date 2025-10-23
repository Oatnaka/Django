# RestaurantProject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. URL สำหรับหน้า Admin
    path('admin/', admin.site.urls),

    # 2. การรวม (Include) URL จากแอปพลิเคชัน 'menu' 
    #    เมื่อผู้ใช้เข้าถึงพาธหลัก ('') Django จะส่งต่อการจัดการ URL ไปยัง menu/urls.py
    path('', include('menu.urls')), 
]

# การตั้งค่าเพื่อเสิร์ฟไฟล์ Static และ Media (สำหรับโหมดพัฒนาเท่านั้น)
if settings.DEBUG:
    # 3. สำหรับไฟล์ Media (รูปภาพที่ผู้ใช้อัปโหลด)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 4. สำหรับไฟล์ Static (CSS, JS, รูปภาพดีไซน์)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)