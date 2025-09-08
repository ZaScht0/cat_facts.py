from typing import List, Dict

import httpx

from app.config.core.global_var import OLLAMA_API_URL
from app.util.reader import read_prompt


class MarketingAIBot:
    """Класс для взаимодействия с ИИ агентом для маркетинга через Ollama"""

    async def get_response(self, message: str, history: List[Dict[str, str]], chat_type: str) -> str:
        """
        Получает ответ от локальной модели с учетом типа чата

        Args:
            message: Сообщение пользователя
            history: История диалialogа
            chat_type: Тип чата (анализ, стратегия, контент, реклама и т.д.)

        Returns:
            Ответ от модели
        """
        # Формируем контекст диалога
        messages = []

        # Добавляем системное сообщение в зависимости от типа чата
        system_prompts = {
            "analysis": read_prompt("analysis"),
            "strategy": read_prompt("strategy"),
            "content": read_prompt("content"),
            "ads": read_prompt("ads"),
            "seo": read_prompt("seo"),
            "social": read_prompt("social")
        }

        system_message = system_prompts.get(chat_type, read_prompt("default"))

        messages.append({
            "role": "system",
            "content": system_message
        })

        # Добавляем историю диалога
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Добавляем новое сообщение пользователя
        messages.append({
            "role": "user",
            "content": message
        })

        # Параметры запроса к Ollama
        payload = {
            "model": "llama2",  # Вы можете изменить на другую модель
            "messages": messages,
            "stream": False
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OLLAMA_API_URL,
                    json=payload,
                    timeout=60.0  # Увеличенный таймаут для локальных моделей
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["message"]["content"]
                else:
                    return f"Ошибка локальной модели: {response.status_code} - {response.text}"

        except httpx.ConnectError:
            return "Ошибка: Не удалось подключиться к локальной модели. Убедитесь, что Ollama запущен."
        except Exception as e:
            return f"Ошибка при обращении к локальной модели: {str(e)}"
