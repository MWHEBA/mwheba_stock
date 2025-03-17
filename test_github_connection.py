"""
اختبار الاتصال بـ GitHub قبل محاولة الرفع.
قم بتشغيل هذا الملف للتحقق من إمكانية الوصول إلى GitHub.
"""

import subprocess
import sys
import os

def test_git_installation():
    """التحقق من تثبيت Git"""
    try:
        result = subprocess.run(['git', '--version'], 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               check=True)
        print(f"✅ Git مثبت: {result.stdout.strip()}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Git غير مثبت أو غير متاح في مسار النظام")
        return False

def test_github_connection():
    """اختبار الاتصال بـ GitHub"""
    try:
        result = subprocess.run(['ping', 'github.com', '-c', '4' if os.name != 'nt' else '-n', '4'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        if result.returncode == 0:
            print("✅ يمكن الوصول إلى GitHub")
            return True
        else:
            print("❌ لا يمكن الوصول إلى GitHub")
            print(result.stderr)
            return False
    except subprocess.SubprocessError:
        print("❌ فشل اختبار الاتصال")
        return False

def test_git_credentials():
    """التحقق من تكوين بيانات اعتماد Git"""
    try:
        name = subprocess.run(['git', 'config', 'user.name'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        email = subprocess.run(['git', 'config', 'user.email'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True)
        
        if name.returncode == 0 and name.stdout.strip():
            print(f"✅ اسم المستخدم في Git: {name.stdout.strip()}")
        else:
            print("❌ لم يتم تعيين اسم المستخدم في Git")
            print("   استخدم الأمر: git config --global user.name \"Your Name\"")
        
        if email.returncode == 0 and email.stdout.strip():
            print(f"✅ البريد الإلكتروني في Git: {email.stdout.strip()}")
        else:
            print("❌ لم يتم تعيين البريد الإلكتروني في Git")
            print("   استخدم الأمر: git config --global user.email \"your@email.com\"")
            
        return name.returncode == 0 and email.returncode == 0 and name.stdout.strip() and email.stdout.strip()
    except subprocess.SubprocessError:
        print("❌ فشل التحقق من بيانات الاعتماد")
        return False

def main():
    """تشغيل جميع الاختبارات"""
    print("🔍 اختبار إعدادات Git لمشروع MWHEBA_App...\n")
    
    git_installed = test_git_installation()
    github_accessible = test_github_connection()
    credentials_configured = test_git_credentials()
    
    print("\n📋 ملخص الاختبارات:")
    print(f"- تثبيت Git: {'✅' if git_installed else '❌'}")
    print(f"- الوصول إلى GitHub: {'✅' if github_accessible else '❌'}")
    print(f"- تكوين بيانات الاعتماد: {'✅' if credentials_configured else '❌'}")
    
    if git_installed and github_accessible and credentials_configured:
        print("\n✅ كل شيء جاهز للرفع إلى GitHub!")
    else:
        print("\n❌ هناك بعض المشكلات التي تحتاج إلى معالجتها قبل الرفع إلى GitHub.")

if __name__ == "__main__":
    main()
