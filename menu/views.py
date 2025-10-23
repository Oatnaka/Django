from django.shortcuts import render, redirect 
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
import math 
from datetime import date 

# *** Import โมเดลและฟอร์มที่เกี่ยวข้องกับการจอง ***
from .models import Category, MenuItem, GalleryImage, Reservation 
from .forms import ReservationForm # *สำคัญ: ตรวจสอบว่าไฟล์ forms.py มี ReservationForm จริงๆ เพื่อแก้ ModuleNotFoundError*

# *** ค่าคงที่สำหรับการคำนวณโต๊ะว่าง ***
MAX_TABLES = 15 # จำนวนโต๊ะทั้งหมดของร้าน
AVG_PARTY_SIZE = 4 # จำนวนคนเฉลี่ยต่อ 1 โต๊ะ (ใช้ในการประมาณการ)

def home_view(request):
    """
    แสดงหน้าแรก (index.html)
    """
    return render(request, 'menu/index.html') 

def menu_view(request):
    """
    แสดงหน้าเมนูอาหาร โดยดึงข้อมูลจากฐานข้อมูล
    """
    categories = Category.objects.all().prefetch_related('items') 
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'menu/menu.html', context)

# ----------------------------------------------------
# 1. NEW: contact_view (แสดงข้อมูลติดต่อเท่านั้น)
# ----------------------------------------------------
def contact_view(request):
    """
    แสดงหน้าติดต่อเรา (map, address, phone)
    """
    # ใช้ template สำหรับหน้าติดต่อเท่านั้น
    return render(request, 'menu/contact.html')

# ----------------------------------------------------
# 2. RENAMED/MODIFIED: reservation_view (จัดการฟอร์มจองโต๊ะและสถานะ)
# ----------------------------------------------------
def reservation_view(request):
    """
    แสดงหน้าฟอร์มจองโต๊ะ/สั่งกลับบ้าน พร้อมประมวลผลฟอร์ม
    และแสดงสถานะโต๊ะว่าง (ใช้การประมาณการ)
    """
    form = ReservationForm()
    
    # ----------------------------------------------------
    # 1. Logic การจัดการฟอร์มจองโต๊ะ/สั่งกลับบ้าน (POST)
    # *Logic นี้ถูกย้ายมาจาก contact_view เดิม*
    # ----------------------------------------------------
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            is_takeaway = form.cleaned_data.get('is_takeaway')
            party_size = form.cleaned_data.get('party_size')
            
            # ตรวจสอบความถูกต้องของข้อมูล
            if not is_takeaway and (party_size is None or party_size == 0):
                 messages.error(request, 'กรุณาระบุจำนวนคนสำหรับการจองโต๊ะ')
            else:
                 form.save()
                 
                 action_type = "สั่งอาหารกลับบ้านสำเร็จ" if is_takeaway else "จองโต๊ะสำเร็จ"
                 messages.success(request, f'{action_type}! ทางร้านจะติดต่อกลับเพื่อยืนยัน')
                 
                 # Redirect ไปหน้าจอง (reservation) เพื่อป้องกันการส่งฟอร์มซ้ำ
                 return redirect('menu:reservation') 
        else:
            messages.error(request, 'การทำรายการไม่สำเร็จ! โปรดตรวจสอบข้อมูลที่กรอก')
    
    # ----------------------------------------------------
    # 2. Logic การคำนวณสถานะโต๊ะว่าง (GET) - สำหรับหน้าจอง (ใช้การประมาณการ)
    # *Logic นี้ถูกย้ายมาจาก contact_view เดิม*
    # ----------------------------------------------------
    
    today = timezone.localdate()
    
    # ดึงรายการจองที่ได้รับการยืนยันและไม่ใช่สั่งกลับบ้าน สำหรับวันนี้
    confirmed_reservations_today = Reservation.objects.filter(
        date=today, 
        is_confirmed=True, # นับเฉพาะที่ยืนยันแล้ว
        is_takeaway=False  # ไม่นับรายการสั่งกลับบ้าน
    )
    
    # รวมจำนวนคนทั้งหมดที่จองแล้ว (Sum of party_size)
    total_party_size_reserved = confirmed_reservations_today.filter(party_size__isnull=False).aggregate(Sum('party_size'))['party_size__sum'] or 0
    
    # คำนวณจำนวนโต๊ะที่ถูกจองแล้ว (โดยประมาณ)
    tables_reserved = math.ceil(total_party_size_reserved / AVG_PARTY_SIZE) if total_party_size_reserved > 0 else 0
    
    # คำนวณจำนวนโต๊ะที่ว่าง
    tables_available = MAX_TABLES - tables_reserved
    
    # ป้องกันไม่ให้ตัวเลขติดลบ
    if tables_available < 0:
        tables_available = 0

    context = {
        'form': form, 
        'tables_available': tables_available,
        'max_tables': MAX_TABLES,
        'current_date': today,
    }
    
    # ใช้ template ใหม่สำหรับหน้าจอง
    return render(request, 'menu/reservation.html', context)
    
# ----------------------------------------------------
# 3. gallery_view (โค้ดเดิม)
# ----------------------------------------------------
def gallery_view(request):
    """
    แสดงหน้าแกลเลอรี (gallery.html) โดยดึงรูปภาพจากฐานข้อมูล
    """
    images = GalleryImage.objects.filter(is_visible=True).order_by('order')
    
    context = {
        'images': images,
    }
    
    return render(request, 'menu/gallery.html', context)

# ----------------------------------------------------
# 4. table_status_view (โค้ดเดิม)
# ----------------------------------------------------
def table_status_view(request):
    """
    แสดงหน้าสถานะโต๊ะว่าง โดยใช้ข้อมูลจริงจากการจัดสรรหมายเลขโต๊ะใน Admin
    """
    today = timezone.localdate() 
    
    confirmed_reservations = Reservation.objects.filter(
        date=today, 
        is_confirmed=True, 
        is_takeaway=False,
        assigned_table__isnull=False # ต้องมีโต๊ะจัดสรรแล้ว
    ).order_by('assigned_table')

    reserved_tables_map = {res.assigned_table: res for res in confirmed_reservations}
    
    TABLE_IDS = [f'T{i}' for i in range(1, MAX_TABLES + 1)]
    
    table_status_list = []
    for table_id in TABLE_IDS:
        reservation = reserved_tables_map.get(table_id)
        
        table_status_list.append({
            'table_id': table_id,
            'is_reserved': reservation is not None,
            'reservation': reservation, # ข้อมูล Reservation (ถ้าถูกจอง)
        })
        
    tables_available = MAX_TABLES - len(confirmed_reservations)

    context = {
        'tables_available': tables_available,
        'max_tables': MAX_TABLES,
        'current_date': today, 
        'table_status_list': table_status_list, 
    }
    return render(request, 'menu/table_status.html', context)