/**
 * هذا الملف يساعد في تتبع معالجات الأحداث المضافة للعناصر
 * لمنع إضافة نفس معالج الحدث أكثر من مرة
 */

// وظيفة للتحقق مما إذا كان قد تم إضافة حدث بالفعل
function isEventHandlerAttached(element, eventName, handlerKey) {
    if (!element) return false;
    
    // استخدام سمة مخصصة لتتبع الأحداث المضافة
    const trackerAttr = `data-event-${eventName}-${handlerKey}`;
    return element.hasAttribute(trackerAttr);
}

// وظيفة لإضافة حدث مع الحماية من التكرار
function addEventOnce(element, eventName, handlerKey, handler) {
    if (!element) return;
    
    const trackerAttr = `data-event-${eventName}-${handlerKey}`;
    
    // التحقق مما إذا كان الحدث مضافًا بالفعل
    if (!element.hasAttribute(trackerAttr)) {
        // إضافة الحدث
        element.addEventListener(eventName, handler);
        
        // وضع علامة على العنصر
        element.setAttribute(trackerAttr, 'true');
        
        return true; // تم إضافة الحدث بنجاح
    }
    
    return false; // تم تخطي إضافة الحدث لأنه مضاف بالفعل
}

// وظيفة لإزالة جميع العلامات من العنصر
function resetEventTracking(element) {
    if (!element) return;
    
    // إزالة جميع سمات تتبع الأحداث
    const attributes = [...element.attributes];
    attributes.forEach(attr => {
        if (attr.name.startsWith('data-event-')) {
            element.removeAttribute(attr.name);
        }
    });
}
