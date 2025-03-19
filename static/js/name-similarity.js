/**
 * وظائف للتحقق من تشابه النصوص وأسماء العملاء
 */

/**
 * دالة لحساب مسافة Levenshtein بين نصين
 * تقيس عدد العمليات المطلوبة لتحويل نص إلى آخر
 */
function levenshteinDistance(str1, str2) {
    const track = Array(str2.length + 1).fill(null).map(() => 
        Array(str1.length + 1).fill(null));
    
    for (let i = 0; i <= str1.length; i += 1) {
        track[0][i] = i;
    }
    
    for (let j = 0; j <= str2.length; j += 1) {
        track[j][0] = j;
    }
    
    for (let j = 1; j <= str2.length; j += 1) {
        for (let i = 1; i <= str1.length; i += 1) {
            const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
            track[j][i] = Math.min(
                track[j][i - 1] + 1, // حذف
                track[j - 1][i] + 1, // إضافة
                track[j - 1][i - 1] + indicator // استبدال
            );
        }
    }
    
    return track[str2.length][str1.length];
}

/**
 * حساب نسبة التشابه بين نصين
 * النتيجة من 0 (لا تشابه) إلى 1 (تطابق تام)
 */
function calculateSimilarity(str1, str2) {
    if (!str1 || !str2) return 0;
    if (str1 === str2) return 1;
    
    // تنظيف النصوص وتحويلها إلى أحرف صغيرة
    const s1 = str1.toLowerCase().trim();
    const s2 = str2.toLowerCase().trim();
    
    // احسب مسافة Levenshtein
    const distance = levenshteinDistance(s1, s2);
    
    // احسب نسبة التشابه (1 ناقص نسبة المسافة إلى الطول الأقصى)
    const similarity = 1 - (distance / Math.max(s1.length, s2.length));
    
    return similarity;
}

/**
 * فحص اسم العميل للبحث عن تشابه مع العملاء الموجودين
 */
async function checkNameSimilarity(customerName, threshold = 0.8) {
    try {
        // طباعة تشخيصية
        console.log('Checking similarity for:', customerName);
        
        // صياغة عنوان URL مع بارامترات البحث
        const searchParams = new URLSearchParams({
            name: customerName,
            threshold: threshold
        });
        
        const url = `/customers/check-similarity/?${searchParams.toString()}`;
        console.log('Request URL:', url);
        
        // استدعاء نقطة النهاية API من الخادم
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Similarity check result:', data);
        return data;
    } catch (error) {
        console.error('Error checking name similarity:', error);
        // في حالة الخطأ، نسمح بإضافة العميل دون تحقق
        return { similar_customers: [] };
    }
}
