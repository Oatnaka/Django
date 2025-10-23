# =========================================================================
# menu/forms.py (FINAL CODE WITH VALIDATION)
# =========================================================================
from django import forms
from django.core.exceptions import ValidationError # ไม่ได้ใช้ ValidationError โดยตรง แต่ดีที่มี
from .models import Reservation

# กำหนด CSS class หลักสำหรับทุกฟิลด์ในฟอร์ม
INPUT_CLASSES = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-amber-500 focus:border-amber-500'

class ReservationForm(forms.ModelForm):
    # กำหนดจำนวนสูงสุดที่อนุญาตให้นั่งต่อ 1 โต๊ะ
    MAX_GUESTS_PER_TABLE = 4 
    
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
        fields = ['name', 'phone', 'email', 'date', 'time', 'party_size', 'special_requests', 'is_takeaway']
        labels = {
            'name': 'ชื่อผู้จอง/ผู้สั่ง',
            'phone': 'เบอร์โทรศัพท์',
            'email': 'อีเมล (ไม่จำเป็น)',
        }
        
    # =====================================================================
    # ⭐️ FUNCTION VALIDATION: บังคับใช้กฎ 4 คนต่อโต๊ะ ⭐️
    # =====================================================================
    def clean_party_size(self):
        """
        ตรวจสอบ: 
        1. ถ้าเป็นการจองโต๊ะ (is_takeaway=False) ต้องใส่ party_size
        2. จำนวนคนต้องไม่เกิน MAX_GUESTS_PER_TABLE
        """
        party_size = self.cleaned_data.get('party_size')
        is_takeaway = self.cleaned_data.get('is_takeaway')

        # 1. ถ้าเป็นการจองโต๊ะ (ไม่สั่งกลับบ้าน) ต้องระบุจำนวนคน
        if not is_takeaway and (party_size is None or party_size == 0):
             raise forms.ValidationError(
                "กรุณาระบุจำนวนคนสำหรับการจองโต๊ะ หรือเลือก 'ต้องการสั่งกลับบ้าน' "
            )

        # 2. ถ้าเป็นการจองโต๊ะ และจำนวนคนเกินขีดจำกัด
        if party_size and not is_takeaway:
            if party_size > self.MAX_GUESTS_PER_TABLE:
                raise forms.ValidationError(
                    f"จำนวนสูงสุดที่อนุญาตต่อ 1 โต๊ะคือ {self.MAX_GUESTS_PER_TABLE} ท่าน หากเกินกว่านี้กรุณาติดต่อร้านโดยตรง หรือจองหลายโต๊ะ"
                )
                
        # 3. ถ้าเป็นสั่งกลับบ้าน party_size สามารถเป็น None/0 ได้
        return party_size
