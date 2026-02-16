import streamlit as st
import json
import requests

# Настройка страницы
st.set_page_config(
    page_title="Цифровой супервизор продаж",
    page_icon="📊",
    layout="wide"
)

# API URL для нового роутера Hugging Face
API_URL = "https://router.huggingface.co"

# Токен встроен в headers
HF_TOKEN = "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"

# Headers с токеном
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# Экспертный промпт
EXPERT_PROMPT = """Ты — экспертный аналитик продаж и корпоративный психолог. Твоя задача: проанализировать входящий текст диалога между продавцом и клиентом и выдать структурированный JSON-ответ.
В анализе должно быть два блока:
HARD DATA (Факты): суть запроса, бюджет, дедлайны, конкретные обязательства.
SOFT SKILLS & PSYCHOLOGY (Эмоции и манипуляции): эмоциональный фон клиента, точки давления, скрытые сигналы (готов ли покупать), совет менеджеру.
Формат вывода: Строгий JSON без лишнего текста."""

# Функция для тестирования API
def test_api():
    """Тестирует подключение к HuggingFace API"""
    try:
        # Простой тестовый запрос с Llama-3
        # Для роутера используем формат: /chat/completions или /v1/chat/completions
        model = "meta-llama/Llama-3-8b-Instruct"
        
        # Пробуем разные форматы для роутера
        urls_to_try = [
            f"{API_URL}/v1/chat/completions",
            f"{API_URL}/chat/completions",
            f"{API_URL}/models/{model}"
        ]
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Привет"}
            ],
            "max_tokens": 10
        }
        
        response = None
        for url in urls_to_try:
            try:
                response = requests.post(url, headers=HEADERS, json=payload, timeout=15)
                if response.status_code != 404:
                    break
            except:
                continue
        
        if response is None:
            return False, "Не удалось подключиться к API"
        
        if response.status_code == 200:
            return True, None
        elif response.status_code == 401:
            return False, "Неверный API-ключ. Проверьте токен в коде."
        elif response.status_code == 403:
            return False, "Доступ запрещён. Проверьте права доступа к модели или примите лицензию Llama-3."
        elif response.status_code == 503:
            return False, "Модель загружается. Подождите несколько секунд и попробуйте снова."
        else:
            return False, f"Ошибка {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return False, "Таймаут запроса. Проверьте подключение к интернету."
    except Exception as e:
        return False, f"Ошибка: {str(e)[:200]}"

# Функция для анализа диалога
def analyze_dialog(dialog_text):
    """Анализирует диалог с помощью HuggingFace API"""
    try:
        full_prompt = f"""{EXPERT_PROMPT}

Диалог для анализа:
{dialog_text}

Выдай только JSON без дополнительных комментариев."""
        
        # Формируем системный промпт и пользовательский запрос
        system_prompt = "Ты — экспертный аналитик продаж. Всегда отвечай только валидным JSON без дополнительного текста."
        
        # Формат промпта для Llama-3
        formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{full_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        # Используем модели Llama-3 (стабильные для работы с текстом)
        # Используем только проверенные названия моделей
        models_to_try = [
            "meta-llama/Llama-3-8b-Instruct",  # Основная модель - стабильная для текста
            "meta-llama/Llama-3-70b-Instruct",  # Резервная модель (более мощная)
            "meta-llama/Llama-3.1-8B-Instruct"  # Альтернативная версия (с большой B)
        ]
        
        last_error = None
        for model in models_to_try:
            try:
                # Пробуем разные форматы для роутера
                urls_to_try = [
                    f"{API_URL}/v1/chat/completions",
                    f"{API_URL}/chat/completions",
                    f"{API_URL}/models/{model}"
                ]
                
                # Формат для chat completions (OpenAI-совместимый)
                chat_payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
                
                # Формат для старого API
                old_payload = {
                    "inputs": formatted_prompt,
                    "parameters": {
                        "max_new_tokens": 2000,
                        "temperature": 0.3,
                        "return_full_text": False
                    }
                }
                
                response = None
                for url in urls_to_try:
                    try:
                        # Пробуем chat completions формат
                        if "/chat/completions" in url or "/v1/chat/completions" in url:
                            payload = chat_payload
                        else:
                            payload = old_payload
                            
                        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
                        
                        if response.status_code == 200:
                            break
                        elif response.status_code != 404:
                            # Если не 404, значит endpoint существует, но ошибка другая
                            break
                    except:
                        continue
                
                if response is None:
                    last_error = "Не удалось подключиться к API"
                    continue
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Обработка ответа в формате chat completions
                    if isinstance(result, dict) and "choices" in result:
                        response_text = result["choices"][0]["message"]["content"]
                    # Обработка старого формата
                    elif isinstance(result, list) and len(result) > 0:
                        response_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        response_text = result.get("generated_text", str(result))
                    else:
                        response_text = str(result)
                    
                    response_text = response_text.strip()
                    
                    # Попытка извлечь JSON из ответа
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    # Ищем JSON в ответе
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                    
                    return response_text, None
                    
                elif response.status_code == 503:
                    # Модель загружается, пробуем следующую
                    last_error = f"Модель {model} загружается. Пробую следующую..."
                    continue
                elif response.status_code == 400:
                    # Модель не найдена, пробуем следующую
                    error_data = response.json() if response.text else {}
                    if "model_not_found" in str(error_data) or "does not exist" in response.text:
                        last_error = f"Модель {model} не найдена. Пробую следующую..."
                        continue
                    else:
                        last_error = f"Ошибка 400: {response.text[:200]}"
                        continue
                else:
                    last_error = f"Ошибка {response.status_code}: {response.text[:200]}"
                    if response.status_code in [401, 403]:
                        break
                    continue
                    
            except requests.exceptions.Timeout:
                last_error = "Таймаут запроса. Пробую следующую модель..."
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        # Если все модели не сработали, возвращаем последнюю ошибку
        raise Exception(last_error or "Не удалось выполнить запрос")
    
    except Exception as e:
        error_msg = str(e)
        
        # Детальная обработка различных типов ошибок
        if "403" in error_msg or "Forbidden" in error_msg:
            detailed_msg = (
                "❌ Ошибка доступа (403 Forbidden):\n\n"
                "**Детали ошибки:**\n"
                f"{error_msg}\n\n"
                "**Возможные причины:**\n"
                "1. Неправильный или недействительный API-ключ\n"
                "2. API-ключ истёк или был отозван\n"
                "3. Нет доступа к модели\n"
                "4. Превышен лимит запросов\n\n"
                "**Решение:**\n"
                "• Проверьте токен в коде (переменная HF_TOKEN)\n"
                "• Убедитесь, что токен активен на https://huggingface.co/settings/tokens\n"
                "• Проверьте лимиты использования\n"
                "• Подождите несколько минут, если превысили лимит"
            )
            return None, detailed_msg
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return None, (
                "❌ Ошибка авторизации (401 Unauthorized):\n\n"
                "**Возможные причины:**\n"
                "1. API-ключ неверный или отсутствует\n"
                "2. Модель Llama-3 требует принятия лицензии на HuggingFace\n"
                "3. Ключ не имеет прав доступа к модели\n\n"
                "**Решение:**\n"
                "• Проверьте токен в коде (переменная HF_TOKEN)\n"
                "• **ВАЖНО**: Примите лицензию Llama-3 на https://huggingface.co/meta-llama/Llama-3-8b-Instruct\n"
                "  (нажмите кнопку 'Agree and access repository')\n"
                "• Проверьте токен на https://huggingface.co/settings/tokens"
            )
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            return None, (
                "❌ Превышен лимит запросов (429):\n\n"
                "Слишком много запросов к API.\n"
                "Подождите несколько минут и попробуйте снова.\n"
                "HuggingFace имеет ограничения на количество запросов."
            )
        elif "503" in error_msg or "loading" in error_msg.lower():
            return None, (
                "⏳ Модель загружается (503):\n\n"
                "Модель ещё не готова к использованию.\n"
                "Подождите 10-30 секунд и попробуйте снова."
            )
        else:
            return None, f"❌ Ошибка при обращении к API:\n\n{error_msg}\n\nПроверьте подключение к интернету и правильность токена."

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")
    
    st.info("🔑 API-ключ встроен в код")
    
    # Кнопка для тестирования API
    if st.button("🔍 Тестировать подключение", use_container_width=True):
        with st.spinner("Проверяю подключение к API..."):
            is_valid, error = test_api()
            if is_valid:
                st.success("✅ Подключение работает!")
            else:
                st.error(f"❌ Ошибка подключения:\n\n{error}")
    
    st.markdown("---")
    st.markdown("### 📖 О приложении")
    st.markdown("""
    **Цифровой супервизор продаж** — это AI-ассистент для анализа 
    диалогов между продавцом и клиентом.
    
    Приложение анализирует:
    - **HARD DATA**: факты, бюджет, дедлайны
    - **SOFT SKILLS**: эмоции, психология, советы
    
    **Используемые модели:** Llama-3 (стабильные для работы с текстом)
    
    **API:** Новый роутер Hugging Face
    """)

# Главный заголовок
st.title("📊 Цифровой супервизор продаж")
st.markdown("---")

# Основной интерфейс
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Введите диалог для анализа")
    dialog_input = st.text_area(
        "Диалог между продавцом и клиентом",
        height=300,
        placeholder="Пример:\nКлиент: Здравствуйте, мне нужен ваш продукт, но бюджет ограничен...\nПродавец: Понимаю, давайте обсудим варианты...",
        help="Вставьте текст диалога между продавцом и клиентом"
    )

with col2:
    st.subheader("📋 Инструкция")
    st.markdown("""
    1. Введите диалог в поле слева
    2. Нажмите кнопку "Запустить анализ"
    3. Получите структурированный анализ
    """)

# Кнопка анализа
st.markdown("---")
analyze_button = st.button(
    "🚀 Запустить анализ",
    type="primary",
    use_container_width=True
)

# Обработка анализа
if analyze_button:
    if not dialog_input.strip():
        st.error("❌ Пожалуйста, введите диалог для анализа")
    else:
        with st.spinner("🔄 Анализирую диалог... Это может занять несколько секунд"):
            result, error = analyze_dialog(dialog_input)
        
        if error:
            st.error(error)
            st.info("💡 **Совет**: Если проблема сохраняется, проверьте:\n- Токен в коде (переменная HF_TOKEN)\n- Принята ли лицензия Llama-3 на HuggingFace\n- Подключение к интернету")
        else:
            st.success("✅ Анализ завершен!")
            st.markdown("---")
            
            # Попытка распарсить JSON
            try:
                analysis_data = json.loads(result)
                
                # Вывод результатов в карточках
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 HARD DATA (Факты)")
                    st.markdown("---")
                    if "HARD DATA" in analysis_data or "hard_data" in analysis_data:
                        hard_data = analysis_data.get("HARD DATA") or analysis_data.get("hard_data") or analysis_data
                        st.json(hard_data)
                    else:
                        st.json(analysis_data)
                
                with col2:
                    st.subheader("🧠 SOFT SKILLS & PSYCHOLOGY")
                    st.markdown("---")
                    if "SOFT SKILLS" in analysis_data or "soft_skills" in analysis_data:
                        soft_skills = analysis_data.get("SOFT SKILLS & PSYCHOLOGY") or analysis_data.get("soft_skills") or analysis_data
                        st.json(soft_skills)
                    else:
                        st.json(analysis_data)
                
                # Полный JSON в раскрывающемся блоке
                with st.expander("📄 Полный JSON-ответ"):
                    st.json(analysis_data)
                    
            except json.JSONDecodeError:
                st.warning("⚠️ Ответ не является валидным JSON. Показываю сырой ответ:")
                st.code(result, language="json")
                
                # Попытка показать в виде текста
                st.markdown("### 📊 Результат анализа:")
                st.text(result)

# Футер
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Цифровой супервизор продаж | Powered by HuggingFace Router & Streamlit"
    "</div>",
    unsafe_allow_html=True
)
