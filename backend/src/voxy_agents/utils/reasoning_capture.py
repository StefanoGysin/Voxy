"""
Reasoning Capture Utility

Captura reasoning_content de logs do OpenAI Agents SDK via Loguru custom sink.

O OpenAI Agents SDK loga reasoning_content mas não o expõe em RunResult.raw_responses.
Esta utilidade intercepta esses logs e extrai o reasoning automaticamente.
"""

import re
import json
from typing import Dict, Optional, List
from threading import Lock
from loguru import logger


class ReasoningCapture:
    """
    Captura reasoning_content de logs do OpenAI Agents SDK.

    Usage:
        capture = ReasoningCapture()
        capture.enable()  # Adiciona custom sink ao Loguru

        # Depois de Runner.run():
        reasoning_list = capture.get_captured_reasoning()
        capture.clear()  # Limpa buffer
    """

    def __init__(self):
        self._buffer: List[Dict[str, str]] = []
        self._lock = Lock()
        self._sink_id: Optional[int] = None
        self._enabled = False

        # Regex para extrair reasoning_content do log
        # Procura por: "reasoning_content": "texto aqui..."
        self._reasoning_pattern = re.compile(
            r'"reasoning_content":\s*"((?:[^"\\]|\\.)*)"',
            re.MULTILINE
        )

    def _sink_handler(self, message) -> None:
        """Custom sink que processa logs e extrai reasoning_content.

        Args:
            message: Loguru Message object contendo o log formatado
        """
        # Extrai texto da mensagem formatada
        log_text = str(message)

        # Só processa logs contendo 'LLM resp' (vindo de openai.agents via InterceptHandler)
        # InterceptHandler muda o event para GENERAL, então não podemos filtrar por 'openai.agents'
        if 'LLM resp' not in log_text:
            return

        # Busca reasoning_content no log
        match = self._reasoning_pattern.search(log_text)
        if match:
            reasoning_text = match.group(1)
            # Decodifica escape sequences (\n, etc)
            try:
                reasoning_text = reasoning_text.encode().decode('unicode_escape')
            except Exception as e:
                # Ignora erro de decodificação silenciosamente
                pass

            with self._lock:
                self._buffer.append({
                    'reasoning': reasoning_text,
                    'source': 'openai_agents_log',
                    'timestamp': log_text.split('|')[0].strip() if '|' in log_text else 'unknown'
                })
                logger.bind(event="REASONING_CAPTURE|CAPTURED").info(
                    f"✅ Reasoning captured",
                    length=len(reasoning_text),
                    preview=reasoning_text[:100]
                )

    def enable(self) -> None:
        """Habilita captura de reasoning via Loguru sink."""
        if self._enabled:
            return

        # Adiciona custom sink que processa mensagens formatadas
        # Não usa filtro - deixa o handler decidir o que processar
        self._sink_id = logger.add(
            self._sink_handler,
            format="{message}",  # Processa mensagem completa
            level="DEBUG",
        )
        self._enabled = True
        logger.bind(event="REASONING_CAPTURE|ENABLED").debug(
            "Reasoning capture sink enabled",
            sink_id=self._sink_id
        )

    def disable(self) -> None:
        """Desabilita captura de reasoning."""
        if not self._enabled or self._sink_id is None:
            return

        logger.remove(self._sink_id)
        self._sink_id = None
        self._enabled = False
        logger.bind(event="REASONING_CAPTURE|DISABLED").debug("Reasoning capture sink disabled")

    def get_captured_reasoning(self) -> List[Dict[str, str]]:
        """Retorna lista de reasoning capturados."""
        with self._lock:
            return self._buffer.copy()

    def clear(self) -> None:
        """Limpa buffer de reasoning capturados."""
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            if count > 0:
                logger.bind(event="REASONING_CAPTURE|CLEARED").debug(
                    f"Cleared {count} captured reasoning blocks"
                )

    def get_last_reasoning(self) -> Optional[str]:
        """Retorna último reasoning capturado, ou None."""
        with self._lock:
            if self._buffer:
                return self._buffer[-1]['reasoning']
            return None

    def __enter__(self):
        """Context manager: habilita ao entrar."""
        self.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: desabilita ao sair."""
        self.disable()
        return False


# Instância global para uso conveniente
_global_capture = ReasoningCapture()


def enable_reasoning_capture() -> None:
    """Habilita captura global de reasoning."""
    _global_capture.enable()


def disable_reasoning_capture() -> None:
    """Desabilita captura global de reasoning."""
    _global_capture.disable()


def get_captured_reasoning() -> List[Dict[str, str]]:
    """Retorna reasoning capturados globalmente."""
    return _global_capture.get_captured_reasoning()


def get_last_reasoning() -> Optional[str]:
    """Retorna último reasoning capturado globalmente."""
    return _global_capture.get_last_reasoning()


def clear_reasoning() -> None:
    """Limpa buffer global de reasoning."""
    _global_capture.clear()
