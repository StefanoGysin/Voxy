"""
Helper utilities para logging padronizado com Loguru.
Acelera migração com templates copiar/colar.

Migração Loguru - Sprint 1: Infraestrutura Base
"""

from loguru import logger


def create_component_logger(component_name: str):
    """
    Factory para criar logger especializado por componente.

    Uso:
        class TranslatorAgent:
            def __init__(self):
                self.logger = create_component_logger("TRANSLATOR_AGENT")
                self.logger.info("Agent initialized")

    Args:
        component_name: Nome do componente (UPPERCASE recomendado)

    Returns:
        Logger bound com component name no contexto extra
    """
    return logger.bind(component=component_name)


class LoggedComponent:
    """
    Base class para componentes com logging integrado.

    Automaticamente cria self.logger bound com component_name.

    Uso:
        class TranslatorAgent(LoggedComponent):
            component_name = "TRANSLATOR_AGENT"

            async def translate(self, text: str):
                self.logger.info("Translating...")
                # logger já está disponível com component bound

    Attributes:
        component_name: Nome do componente (deve ser sobrescrito pela subclasse)
        logger: Logger instance bound com component_name
    """

    component_name: str = "UNKNOWN"

    def __init__(self):
        self.logger = logger.bind(component=self.component_name)
