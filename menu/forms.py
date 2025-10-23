# menu/forms.py

from django import forms
from .models import Reservation

# กำหนด CSS class หลักสำหรับทุกฟิลด์ในฟอร์ม
INPUT_CLASSES = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-amber-500 focus:border-amber-500'

class ReservationForm(forms.ModelForm):
    # ปรับแต่ง Widget และ Class
    name = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASSES}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': INPUT_CLASSES}))
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASSES}),
        label='วันที่',
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}),
        label='เวลา',
    )
    
    # *** ปรับ party_size ให้เป็น required=False เพื่อรองรับการสั่งกลับบ้าน ***
    party_size = forms.IntegerField(
        required=False, # ตั้งค่าเป็น False เพราะไม่จำเป็นหากเลือกสั่งกลับบ้าน
        widget=forms.NumberInput(attrs={'min': 1, 'max': 20, 'class': INPUT_CLASSES, 'placeholder': 'จำนวนคน'}),
        label='จำนวนคน (ถ้าจองโต๊ะ)',
    )
    
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': INPUT_CLASSES}),
        label='คำขอพิเศษ',
    )
    
    # *** เพิ่มฟิลด์ is_takeaway (สั่งกลับบ้าน) ***
    is_takeaway = forms.BooleanField(
        required=False, 
        label='ต้องการสั่งกลับบ้าน',
        # กำหนด CSS สำหรับ Checkbox เพื่อให้ใช้ Tailwind
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-amber-600 border-gray-300 rounded'})
    )

    class Meta:
        model = Reservation
        # *** เพิ่ม is_takeaway ใน fields ***
        fields = ['name', 'phone', 'email', 'date', 'time', 'party_size', 'special_requests', 'is_takeaway']
        labels = {
            'name': 'ชื่อผู้จอง/ผู้สั่ง',
            'phone': 'เบอร์โทรศัพท์',
            'email': 'อีเมล (ไม่จำเป็น)',
        }