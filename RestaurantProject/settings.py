"""
Django settings for RestaurantProject project.
"""
import os
import sys
from pathlib import Path
from decouple import config # ⭐️ นำเข้า python-decouple
import dj_database_url      # ⭐️ นำเข้า dj-database-url สำหรับ PostgreSQL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production

# 1. SECURITY WARNING: ดึงค่าความลับจาก Environment Variables (ปลอดภัย)
# ค่านี้จะถูกตั้งค่าใน Render Environment Variables
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-for-local-use-only')

# 2. SECURITY WARNING: ดึงค่า DEBUG จาก Environment Variables
# ตั้งค่าเป็น False บน Render
DEBUG = config('DEBUG', default=False, cast=bool)

# 3. ตั้งค่า Host สำหรับ Production
ALLOWED_HOSTS = ['*']
# หากต้องการความปลอดภัย ให้ใช้: ALLOWED_HOSTS = [config('RENDER_EXTERNAL_HOSTNAME')]


# Application definition

INSTALLED_APPS = [
    # 'jazzmin', # ❌ ลบ jazzmin ออกจาก INSTALLED_APPS เพื่อแก้ปัญหา Build
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'menu',
]

# 4. ⭐️ เพิ่ม Whitenoise Middleware สำหรับ Static Files ⭐️
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ⭐️ เพิ่ม Whitenoise ที่นี่
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'RestaurantProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'RestaurantProject.wsgi.application'


# 5. ⭐️ ตั้งค่า Database สำหรับ PostgreSQL บน Render ⭐️
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'), # ดึงค่าจาก Render
        conn_max_age=600 # เพื่อความเสถียร
    )
}
# ⬇️ เงื่อนไขสำหรับ Build Time (เช่น collectstatic) เพื่อใช้ SQLite ชั่วคราว
if 'collectstatic' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# Password validation (คงเดิม)
# ...

# Internationalization (คงเดิม)
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True


# 6. ⭐️ ตั้งค่า Static Files สำหรับ Whitenoise ⭐️
STATIC_URL = 'static/'
# ⭐️ STATIC_ROOT: โฟลเดอร์ที่ Whitenoise ใช้
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 


# การตั้งค่าสำหรับ Media Files (รูปภาพที่ผู้ใช้อัปโหลด)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_uploads')


# Default primary key field type (คงเดิม)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 7. ❌ ลบ JAZZMIN SETTINGS ออกทั้งหมด ❌
# เนื่องจากได้ลบ 'jazzmin' ออกจาก INSTALLED_APPS แล้ว ควรลบ JAZZMIN_SETTINGS และ JAZZMIN_UI_TWEAKS ออกทั้งหมด


# 8. ❌ ลบ LINE MESSAGING API SETTINGS ออกทั้งหมด ❌
# ⚠️ สำคัญมาก! ห้ามเก็บ Token และ Secret ในโค้ด
LINE_CHANNEL_ACCESS_TOKEN = config('LINE_CHANNEL_ACCESS_TOKEN', default='')
LINE_CHANNEL_SECRET = config('LINE_CHANNEL_SECRET', default='')
LINE_NOTIFICATION_TARGET_ID = config('LINE_NOTIFICATION_TARGET_ID', default='')
