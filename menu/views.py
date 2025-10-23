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

# -------------------------------------------------------------------------
# *** ค่าคงที่ใหม่สำหรับการคำนวณโต๊ะว่างตามความจุที่นั่ง (Seating Capacity) ***
# -------------------------------------------------------------------------
# โต๊ะ T1 ถึง T10 (10 โต๊ะ) ความจุ 4 ที่นั่ง
TABLE_SMALL_COUNT = 10
TABLE_SMALL_CAPACITY = 4 

# โต๊ะ T11 ถึง T15 (5 โต๊ะ) ความจุ 10 ที่นั่ง
TABLE_LARGE_COUNT = 5
TABLE_LARGE_CAPACITY = 10

# จำนวนโต๊ะทั้งหมด (ยังคงเป็น 15)
MAX_TABLES = TABLE_SMALL_COUNT + TABLE_LARGE_COUNT 

# คำนวณความจุที่นั่งรวมทั้งหมดของร้าน
TOTAL_SEATING_CAPACITY = (TABLE_SMALL_COUNT * TABLE_SMALL_CAPACITY) + \
                         (TABLE_LARGE_COUNT * TABLE_LARGE_CAPACITY) 
# TOTAL_SEATING_CAPACITY จะเท่ากับ (10 * 4) + (5 * 10) = 40 + 50 = 90 ที่นั่ง

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
# 2. MODIFIED: reservation_view (จัดการฟอร์มจองโต๊ะและสถานะ)
# ----------------------------------------------------
def reservation_view(request):
    """
    แสดงหน้าฟอร์มจองโต๊ะ/สั่งกลับบ้าน พร้อมประมวลผลฟอร์ม
    และแสดงสถานะที่นั่งว่าง (ใช้การคำนวณจากความจุรวม)
    """
    form = ReservationForm()
    
    # ----------------------------------------------------
    # 1. Logic การจัดการฟอร์มจองโต๊ะ/สั่งกลับบ้าน (POST)
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
    # 2. Logic การคำนวณสถานะที่นั่งว่าง (GET) - **คำนวณจากจำนวนที่นั่งรวม**
    # ----------------------------------------------------
    
    today = timezone.localdate()
    
    # ดึงรายการจองที่ได้รับการยืนยันและไม่ใช่สั่งกลับบ้าน สำหรับวันนี้
    confirmed_reservations_today = Reservation.objects.filter(
        date=today, 
        is_confirmed=True, # นับเฉพาะที่ยืนยันแล้ว
        is_takeaway=False  # ไม่นับรายการสั่งกลับบ้าน
    )
    
    # รวมจำนวนคนทั้งหมดที่จองแล้ว (Sum of party_size)
    total_party_size_reserved = confirmed_reservations_today.filter(
        party_size__isnull=False
    ).aggregate(Sum('party_size'))['party_size__sum'] or 0
    
    # คำนวณจำนวนที่นั่งที่ว่าง
    remaining_seating_capacity = TOTAL_SEATING_CAPACITY - total_party_size_reserved
    
    # คำนวณจำนวนโต๊ะที่ถูกจองแล้ว (ใช้ในการแสดงผลในหน้าฟอร์ม)
    # เรายังใช้ AVG_PARTY_SIZE สำหรับการประมาณ "จำนวนโต๊ะ" เพื่อแสดงผลให้ผู้ใช้เห็นภาพรวม
    # **แต่ค่าสำคัญจริงๆ คือ remaining_seating_capacity**
    AVG_PARTY_SIZE_FOR_DISPLAY = 4
    tables_reserved = math.ceil(total_party_size_reserved / AVG_PARTY_SIZE_FOR_DISPLAY) if total_party_size_reserved > 0 else 0
    tables_available_for_display = MAX_TABLES - tables_reserved
    
    # ป้องกันไม่ให้ตัวเลขติดลบ
    if tables_available_for_display < 0:
        tables_available_for_display = 0

    context = {
        'form': form, 
        'tables_available': tables_available_for_display, # ใช้แสดงผลในหน้าฟอร์ม (ยังใช้การประมาณจำนวนโต๊ะ)
        'max_tables': MAX_TABLES,
        'current_date': today,
        # *** NEW: เพิ่มข้อมูลความจุที่นั่งทั้งหมด/ที่เหลือ เพื่อความแม่นยำในการแสดงผล ***
        'remaining_capacity': remaining_seating_capacity, 
        'total_capacity': TOTAL_SEATING_CAPACITY,
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
# 4. MODIFIED: table_status_view (ปรับปรุงการแสดงสถานะโต๊ะตามประเภท)
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
    
    # สร้างรายการ ID โต๊ะตามประเภทใหม่
    TABLE_IDS_SMALL = [f'T{i}' for i in range(1, TABLE_SMALL_COUNT + 1)] # T1-T10
    TABLE_IDS_LARGE = [f'T{i}' for i in range(TABLE_SMALL_COUNT + 1, MAX_TABLES + 1)] # T11-T15
    TABLE_IDS = TABLE_IDS_SMALL + TABLE_IDS_LARGE
    
    # สร้าง Map สำหรับความจุของโต๊ะแต่ละ ID
    table_capacity_map = {}
    for table_id in TABLE_IDS_SMALL:
        table_capacity_map[table_id] = TABLE_SMALL_CAPACITY
    for table_id in TABLE_IDS_LARGE:
        table_capacity_map[table_id] = TABLE_LARGE_CAPACITY
    
    table_status_list = []
    reserved_count = 0
    reserved_capacity = 0

    for table_id in TABLE_IDS:
        reservation = reserved_tables_map.get(table_id)
        is_reserved = reservation is not None
        capacity = table_capacity_map.get(table_id, 0)
        
        if is_reserved:
            reserved_count += 1
            reserved_capacity += capacity

        table_status_list.append({
            'table_id': table_id,
            'is_reserved': is_reserved,
            'reservation': reservation, # ข้อมูล Reservation (ถ้าถูกจอง)
            'capacity': capacity, # NEW: ความจุของโต๊ะ
            'type': 'Large' if table_id in TABLE_IDS_LARGE else 'Small'
        })
        
    tables_available = MAX_TABLES - reserved_count
    remaining_seating_capacity = TOTAL_SEATING_CAPACITY - reserved_capacity

    context = {
        'tables_available': tables_available,
        'max_tables': MAX_TABLES,
        'current_date': today, 
        'table_status_list': table_status_list, 
        'reserved_count': reserved_count,
        'remaining_capacity': remaining_seating_capacity, # NEW: ที่นั่งที่เหลือจริง
        'total_capacity': TOTAL_SEATING_CAPACITY,
    }
    return render(request, 'menu/table_status.html', context)
