#!/bin/bash

# التأكد من تواجدك في الدليل الصحيح
cd c:\Users\UTD\MWHEBA_App

# حذف أي مجلدات .git قديمة (احتياطية في حالة وجود مشاكل)
# rm -rf .git

# تهيئة مستودع git جديد
git init

# إضافة الملفات الأساسية فقط في البداية (تجنب إضافة الكل دفعة واحدة)
git add .gitignore
git add README.md
git add requirements.txt

# عمل commit أولي
git commit -m "Initial commit with basic files"

# إضافة ملفات التطبيق الرئيسية
git add mwheba_stock/core/
git commit -m "Add core application files"

# إضافة ملفات التطبيق inventory بشكل تدريجي
git add mwheba_stock/inventory/models.py
git commit -m "Add inventory models"

git add mwheba_stock/inventory/views.py
git commit -m "Add inventory views"

git add mwheba_stock/inventory/urls.py
git commit -m "Add inventory URLs"

git add mwheba_stock/inventory/admin.py
git commit -m "Add inventory admin configurations"

# إضافة ملفات الـ static بشكل تدريجي
git add mwheba_stock/static/js/accounts_receivable.js
git commit -m "Add accounts receivable JS module"

# إضافة ملفات القوالب بشكل تدريجي
git add mwheba_stock/inventory/templates/inventory/accounts_receivable_test.html
git commit -m "Add accounts receivable test template"

# بقية ملفات static
git add mwheba_stock/static/js/
git commit -m "Add remaining JS files"

git add mwheba_stock/static/css/
git commit -m "Add CSS files"

git add mwheba_stock/static/images/
git commit -m "Add image files"

# بقية التطبيقات والملفات
git add mwheba_stock/
git commit -m "Add remaining application files"

# إضافة remote لـ GitHub repository (استبدل الـ URL بـ URL المستودع الخاص بك)
git remote add origin https://github.com/yourusername/mwheba_stock.git

# رفع الكود (قد تحتاج لتسجيل الدخول)
git push -u origin master
