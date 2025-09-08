from app.ai_agent.interaction import MarketingAIBot
from app.config.database.db_config import init_db

# Инициализация БД
init_db()

# Создаем экземпляр ИИ агента
bot = MarketingAIBot()
