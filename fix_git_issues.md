# حل مشاكل Git الشائعة

## عندما يتعلق Git أثناء الرفع

### 1. مشكلة الملفات الكبيرة
```bash
# تعديل حد حجم الملفات
git config http.postBuffer 524288000

# لتخطي ملفات كبيرة يمكنك استخدام git-lfs
# تثبيت git-lfs
git lfs install

# تحديد أنواع الملفات الكبيرة
git lfs track "*.psd" "*.pdf" "*.zip"
```

### 2. مشكلة اتصال الشبكة
```bash
# زيادة وقت الانتظار
git config http.lowSpeedLimit 1000
git config http.lowSpeedTime 300

# استخدام بروتوكول SSH بدلاً من HTTPS
git remote set-url origin git@github.com:yourusername/mwheba_stock.git
```

### 3. مشكلة تعارض الملفات
```bash
# لمعرفة الملفات المتعارضة
git status

# حل التعارضات
git add <file_path>
git commit -m "Resolve conflicts"
```

### 4. استخدام Git بشكل تدريجي لملفات كثيرة
```bash
# تقسيم الرفع إلى مجموعات
git add folder1/
git commit -m "Add folder1"

git add folder2/
git commit -m "Add folder2"
```

### 5. تنظيف الريبو إذا كان هناك مشاكل كبيرة
```bash
# حفظ التغييرات المحلية
git stash

# إعادة ضبط الفرع
git reset --hard origin/master

# استعادة التغييرات المحلية
git stash pop
```

### 6. إذا كان هناك خطأ في حالة استمرار التعليق
```bash
# قم بإلغاء العملية الحالية
Ctrl+C 

# وقم بتقسيم المهمة إلى أجزاء أصغر
```

### 7. التأكد من تحديث Git
```bash
# تحقق من إصدار Git
git --version

# قم بتحديثه إذا كان قديمًا
```
