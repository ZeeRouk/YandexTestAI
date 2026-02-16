"""
Простой скрипт для тестирования Groq API
Использование: python test_groq_api.py
"""
from groq import Groq
import sys

def test_groq_api(api_key):
    """Тестирует Groq API с разными моделями"""
    print(f"🔍 Тестирую API-ключ: {api_key[:10]}...")
    print("-" * 60)
    
    api_key = api_key.strip()
    
    if not api_key.startswith("gsk_"):
        print("❌ Ошибка: API-ключ должен начинаться с 'gsk_'")
        return False
    
    try:
        client = Groq(api_key=api_key)
        
        # Список моделей для тестирования
        # Начинаем с самой стабильной модели без требований к подтверждению телефона
        models = [
            "llama3-8b-8192",  # Основная стабильная модель
            "llama-3-70b-8192",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768"
        ]
        
        for model in models:
            try:
                print(f"\n📡 Тестирую модель: {model}...")
                response = client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": "Скажи 'Привет' одним словом"}
                    ],
                    model=model,
                    max_tokens=10
                )
                
                result = response.choices[0].message.content
                print(f"✅ Успешно! Ответ: {result}")
                print(f"✅ Модель {model} работает!")
                return True
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка с моделью {model}: {error_msg}")
                
                if "403" in error_msg:
                    print("\n🔍 Детали ошибки 403:")
                    print("   - Проверьте, что API-ключ действителен")
                    print("   - Возможно, превышен лимит запросов")
                    print("   - Попробуйте создать новый ключ на https://console.groq.com/")
                    return False
                elif "401" in error_msg:
                    print("\n🔍 Детали ошибки 401:")
                    print("   - API-ключ неверный")
                    return False
                continue
        
        print("\n❌ Все модели вернули ошибку")
        return False
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        print("Введите API-ключ Groq:")
        api_key = input().strip()
    
    if not api_key:
        print("❌ API-ключ не введен")
        sys.exit(1)
    
    success = test_groq_api(api_key)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ API-ключ работает! Можно использовать в приложении.")
    else:
        print("\n" + "=" * 60)
        print("❌ API-ключ не работает. Проверьте ключ на https://console.groq.com/")
        sys.exit(1)
