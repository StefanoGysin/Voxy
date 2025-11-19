"""
Vision Agent Intelligent Caching System

Implementa cache multi-nível para otimizar performance do Vision Agent:
- Cache L1: Memória local (análises idênticas)
- Cache L2: Redis (análises similares com hash semântico)
- Cache L3: Análises por tipo/complexidade

Baseado na análise de performance que identificou 40s de overhead.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from io import BytesIO
from typing import Any, Optional

import redis
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class AnalysisComplexity(Enum):
    """Níveis de complexidade de análise."""

    MINIMAL = "minimal"  # Emojis, ícones simples
    LOW = "low"  # Objetos básicos, texto claro
    MEDIUM = "medium"  # Cenas complexas, múltiplos objetos
    HIGH = "high"  # Documentos técnicos, diagramas


@dataclass
class CacheEntry:
    """Entrada do cache com metadata."""

    result: str
    timestamp: datetime
    complexity: AnalysisComplexity
    processing_time: float
    model_used: str
    image_hash: str
    analysis_type: str
    cost: float
    hit_count: int = 0


class VisionCache:
    """
    Sistema de cache inteligente para Vision Agent.

    Features:
    - Cache semântico baseado em hash de imagem
    - TTL adaptativo baseado na complexidade
    - Análise de similaridade de imagens
    - Métricas de performance
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache: dict[str, CacheEntry] = {}

        # Configurações de TTL por complexidade (em segundos)
        self.ttl_config = {
            AnalysisComplexity.MINIMAL: 1800,  # 30 minutos - análises simples mudam pouco
            AnalysisComplexity.LOW: 900,  # 15 minutos - análises básicas
            AnalysisComplexity.MEDIUM: 600,  # 10 minutos - análises padrão
            AnalysisComplexity.HIGH: 300,  # 5 minutos - análises complexas podem ter nuances
        }

        # Métricas
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_time_saved = 0.0

    async def get_cached_analysis(
        self,
        image_url: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]] = None,
    ) -> Optional[tuple[str, dict[str, Any]]]:
        """
        Busca análise no cache multi-nível.

        Returns:
            Tuple de (resultado, metadata) se encontrado, None caso contrário
        """
        try:
            # Gerar chaves de cache
            exact_key = self._generate_exact_cache_key(
                image_url, analysis_type, detail_level, specific_questions
            )
            semantic_key = await self._generate_semantic_cache_key(
                image_url, analysis_type
            )

            # L1: Cache local exato
            if exact_key in self.local_cache:
                entry = self.local_cache[exact_key]
                if self._is_cache_valid(entry):
                    entry.hit_count += 1
                    self.cache_hits += 1
                    self.total_time_saved += entry.processing_time
                    logger.info(
                        f"🎯 L1 Cache HIT: {exact_key[:20]}... (saved {entry.processing_time:.2f}s)"
                    )

                    return entry.result, {
                        "cached": True,
                        "cache_level": "L1_local",
                        "cache_age": (datetime.now() - entry.timestamp).total_seconds(),
                        "original_processing_time": entry.processing_time,
                        "model_used": entry.model_used,
                        "hit_count": entry.hit_count,
                    }
                else:
                    del self.local_cache[exact_key]

            # L2: Redis cache semântico
            if self.redis_client:
                redis_result = await self._get_from_redis(semantic_key)
                if redis_result:
                    self.cache_hits += 1
                    logger.info(f"🎯 L2 Cache HIT: {semantic_key[:20]}...")

                    # Promover para L1
                    entry = CacheEntry(
                        result=redis_result["result"],
                        timestamp=datetime.fromisoformat(redis_result["timestamp"]),
                        complexity=AnalysisComplexity(redis_result["complexity"]),
                        processing_time=redis_result["processing_time"],
                        model_used=redis_result["model_used"],
                        image_hash=redis_result["image_hash"],
                        analysis_type=analysis_type,
                        cost=redis_result.get("cost", 0.0),
                        hit_count=redis_result.get("hit_count", 0) + 1,
                    )
                    self.local_cache[exact_key] = entry

                    return entry.result, {
                        "cached": True,
                        "cache_level": "L2_redis",
                        "cache_age": (datetime.now() - entry.timestamp).total_seconds(),
                        "original_processing_time": entry.processing_time,
                        "model_used": entry.model_used,
                        "hit_count": entry.hit_count,
                    }

            # Cache miss
            self.cache_misses += 1
            logger.info(f"❌ Cache MISS: {exact_key[:20]}...")
            return None

        except Exception as e:
            logger.error(f"Error accessing cache: {e}")
            return None

    async def store_analysis(
        self,
        image_url: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]],
        result: str,
        processing_time: float,
        model_used: str,
        cost: float,
    ) -> None:
        """Armazena análise no cache multi-nível."""
        try:
            # Determinar complexidade baseada nos parâmetros
            complexity = self._determine_complexity(
                analysis_type, detail_level, specific_questions, result
            )

            # Gerar hash da imagem para detecção de duplicatas
            image_hash = await self._generate_image_hash(image_url)

            # Criar entrada do cache
            entry = CacheEntry(
                result=result,
                timestamp=datetime.now(),
                complexity=complexity,
                processing_time=processing_time,
                model_used=model_used,
                image_hash=image_hash,
                analysis_type=analysis_type,
                cost=cost,
            )

            # Armazenar em L1 (local)
            exact_key = self._generate_exact_cache_key(
                image_url, analysis_type, detail_level, specific_questions
            )
            self.local_cache[exact_key] = entry

            # Armazenar em L2 (Redis) se disponível
            if self.redis_client:
                semantic_key = await self._generate_semantic_cache_key(
                    image_url, analysis_type
                )
                await self._store_in_redis(semantic_key, entry)

            # Limpar cache antigo
            await self._cleanup_expired_entries()

            logger.info(
                f"💾 Cached analysis: {exact_key[:20]}... (complexity: {complexity.value})"
            )

        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    def _generate_exact_cache_key(
        self,
        image_url: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]] = None,
    ) -> str:
        """Gera chave exata para cache L1."""
        cache_data = f"{image_url}|{analysis_type}|{detail_level}|{str(specific_questions or [])}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    async def _generate_semantic_cache_key(
        self, image_url: str, analysis_type: str
    ) -> str:
        """Gera chave semântica baseada no hash da imagem para cache L2."""
        try:
            image_hash = await self._generate_image_hash(image_url)
            return f"vision_cache:{analysis_type}:{image_hash}"
        except Exception:
            # Fallback para URL hash se não conseguir processar a imagem
            return f"vision_cache:{analysis_type}:{hashlib.md5(image_url.encode()).hexdigest()}"

    async def _generate_image_hash(self, image_url: str) -> str:
        """Gera hash perceptual da imagem para detectar similaridade."""
        try:
            # Para URLs, baixar e processar imagem
            if image_url.startswith(("http://", "https://")):
                response = requests.get(image_url, timeout=10)
                image = Image.open(BytesIO(response.content))
            else:
                # Para base64 ou dados locais
                if "base64," in image_url:
                    import base64

                    image_data = base64.b64decode(image_url.split("base64,")[1])
                    image = Image.open(BytesIO(image_data))
                else:
                    return hashlib.md5(image_url.encode()).hexdigest()

            # Redimensionar para comparação consistente
            image = image.resize((32, 32), Image.Resampling.LANCZOS)

            # Converter para escala de cinza para hash perceptual simples
            if image.mode != "L":
                image = image.convert("L")

            # Gerar hash baseado nos pixels
            pixels = list(image.getdata())
            pixel_str = "".join(str(p) for p in pixels)
            return hashlib.sha256(pixel_str.encode()).hexdigest()[
                :16
            ]  # 16 chars suficiente

        except Exception as e:
            logger.warning(f"Failed to generate image hash: {e}")
            # Fallback para hash da URL
            return hashlib.md5(image_url.encode()).hexdigest()

    def _determine_complexity(
        self,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]],
        result: str,
    ) -> AnalysisComplexity:
        """Determina complexidade da análise para TTL adaptativo."""
        # Análises básicas/gerais são simples
        if analysis_type == "general" and detail_level == "basic":
            return AnalysisComplexity.MINIMAL

        # Análises com questões específicas são mais complexas
        if specific_questions and len(specific_questions) > 3:
            return AnalysisComplexity.HIGH

        # Análises detalhadas/comprehensivas são complexas
        if detail_level in ["detailed", "comprehensive"]:
            return (
                AnalysisComplexity.MEDIUM
                if detail_level == "detailed"
                else AnalysisComplexity.HIGH
            )

        # Análises OCR/técnicas são complexas
        if analysis_type in ["ocr", "technical", "document"]:
            return AnalysisComplexity.MEDIUM

        # Baseado no tamanho da resposta
        if len(result) > 1000:
            return AnalysisComplexity.MEDIUM
        elif len(result) > 500:
            return AnalysisComplexity.LOW
        else:
            return AnalysisComplexity.MINIMAL

    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Verifica se entrada do cache ainda é válida."""
        age = (datetime.now() - entry.timestamp).total_seconds()
        ttl = self.ttl_config[entry.complexity]
        return age < ttl

    async def _get_from_redis(self, key: str) -> Optional[dict[str, Any]]:
        """Busca entrada no Redis."""
        try:
            if not self.redis_client:
                return None

            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def _store_in_redis(self, key: str, entry: CacheEntry) -> None:
        """Armazena entrada no Redis."""
        try:
            if not self.redis_client:
                return

            data = {
                "result": entry.result,
                "timestamp": entry.timestamp.isoformat(),
                "complexity": entry.complexity.value,
                "processing_time": entry.processing_time,
                "model_used": entry.model_used,
                "image_hash": entry.image_hash,
                "analysis_type": entry.analysis_type,
                "cost": entry.cost,
                "hit_count": entry.hit_count,
            }

            ttl = self.ttl_config[entry.complexity]
            self.redis_client.setex(key, ttl, json.dumps(data))

        except Exception as e:
            logger.error(f"Redis store error: {e}")

    async def _cleanup_expired_entries(self) -> None:
        """Remove entradas expiradas do cache local."""
        try:
            expired_keys = []
            for key, entry in self.local_cache.items():
                if not self._is_cache_valid(entry):
                    expired_keys.append(key)

            for key in expired_keys:
                del self.local_cache[key]

            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) * 100 if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_time_saved": f"{self.total_time_saved:.2f}s",
            "local_cache_size": len(self.local_cache),
            "avg_time_saved_per_hit": self.total_time_saved / max(1, self.cache_hits),
        }

    async def preload_common_analyses(self) -> None:
        """Precarrega análises comuns para otimizar cold starts."""
        # TODO: Implementar preloading baseado em padrões de uso
        pass
