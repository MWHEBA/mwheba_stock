/**
 * دوال مساعدة للتشخيص وإصلاح الأخطاء
 */

// دالة لعرض الـ URL النهائي للتشخيص
function logUrlInfo(urlName, actualUrl) {
    console.log(`URL Name: ${urlName}`);
    console.log(`Actual URL: ${actualUrl}`);
}

// دالة للتأكد من صحة URLs المستخدمة في الصفحة
function validatePageUrls() {
    // إذا كان هناك متغير عالمي للـ URLs، استخدمه للتشخيص
    if (typeof categoryCreateAjaxUrl !== 'undefined') {
        logUrlInfo('categoryCreateAjaxUrl', categoryCreateAjaxUrl);
    } else {
        console.warn('Variable categoryCreateAjaxUrl is not defined');
    }
    
    // التحقق من أي متغيرات URLs أخرى
}

// التشغيل التلقائي عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إضافة زر للتشخيص في وضع التطوير
    if (document.querySelector('meta[name="debug-mode"]')) {
        const debugButton = document.createElement('button');
        debugButton.textContent = 'تشخيص URLs';
        debugButton.className = 'btn btn-sm btn-warning position-fixed';
        debugButton.style.bottom = '20px';
        debugButton.style.right = '20px';
        debugButton.style.zIndex = '9999';
        debugButton.addEventListener('click', validatePageUrls);
        document.body.appendChild(debugButton);
    }
});
