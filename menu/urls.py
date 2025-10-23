from django.urls import path
from . import views

app_name = 'menu'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('menu/', views.menu_view, name='menu'),
    # 1. URL สำหรับหน้าติดต่อ (แสดงข้อมูลร้าน)
    path('contact/', views.contact_view, name='contact'), 
    # 2. URL สำหรับหน้าจองโต๊ะ/สั่งกลับบ้าน (ใช้ฟังก์ชันใหม่)
    path('reservation/', views.reservation_view, name='reservation'), 
    path('gallery/', views.gallery_view, name='gallery'),
    path('table-status/', views.table_status_view, name='table_status'),
]