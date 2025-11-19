"""
Adaptive Reasoning Effort System

Sistema inteligente para determinar o nível de reasoning_effort baseado em:
- Complexidade da imagem (análise de conteúdo)
- Tipo de análise solicitada
- Histórico de performance
- Context clues na query

Objetivo: Reduzir latência de 48s para 5-15s em análises simples.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ReasoningLevel(Enum):
    """Níveis de reasoning effort."""

    MINIMAL = "minimal"  # ~3-8s - Para emojis, ícones simples
    LOW = "low"  # ~8-15s - Para objetos básicos, texto claro
    MEDIUM = "medium"  # ~15-30s - Para cenas complexas, múltiplos objetos
    HIGH = "high"  # ~30-60s - Para análises científicas, técnicas


@dataclass
class AnalysisContext:
    """Contexto da análise para determinar complexity."""

    query_text: str
    analysis_type: str
    detail_level: str
    specific_questions: Optional[list[str]]
    image_url: str
    user_history: Optional[dict] = None


class AdaptiveReasoningSystem:
    """
    Sistema adaptativo para determinar reasoning effort ótimo.

    Usa machine learning simples e heurísticas para otimizar performance.
    """

    def __init__(self):
        # Histórico de performance por nível
        self.performance_history = {
            ReasoningLevel.MINIMAL: {"avg_time": 5.0, "success_rate": 0.95},
            ReasoningLevel.LOW: {"avg_time": 12.0, "success_rate": 0.98},
            ReasoningLevel.MEDIUM: {"avg_time": 22.0, "success_rate": 0.99},
            ReasoningLevel.HIGH: {"avg_time": 45.0, "success_rate": 0.999},
        }

        # Palavras-chave para detecção rápida
        self.simple_keywords = {
            "emoji",
            "emoticon",
            "icon",
            "símbolo",
            "logo",
            "que",
            "qual",
            "este",
            "esta",
            "identifique",
            "reconheça",
            "mostre",
            "vejo",
            "simples",
            "básico",
        }

        self.complex_keywords = {
            "analise",
            "explique",
            "detalhe",
            "técnico",
            "científico",
            "médico",
            "jurídico",
            "diagnóstico",
            "compare",
            "contraste",
            "avalie",
            "interprete",
            "comprehensive",
            "detalhado",
            "profundo",
            "completo",
            "minucioso",
        }

        self.medium_keywords = {
            "descreva",
            "conte",
            "explique",
            "como",
            "porque",
            "onde",
            "quando",
            "contexto",
            "cenário",
            "situação",
            "pessoas",
            "objetos",
            "ambiente",
        }

    def determine_reasoning_effort(
        self, context: AnalysisContext
    ) -> tuple[ReasoningLevel, dict]:
        """
        Determina o nível de reasoning effort ótimo baseado no contexto.

        Returns:
            Tuple de (ReasoningLevel, metadata_dict)
        """
        try:
            # Analisar query text
            query_score = self._analyze_query_complexity(context.query_text)

            # Analisar tipo de análise
            type_score = self._analyze_analysis_type(context.analysis_type)

            # Analisar nível de detalhe
            detail_score = self._analyze_detail_level(context.detail_level)

            # Analisar questões específicas
            questions_score = self._analyze_specific_questions(
                context.specific_questions
            )

            # Score total (0-100)
            total_score = (
                query_score * 0.4
                + type_score * 0.3
                + detail_score * 0.2
                + questions_score * 0.1
            )

            # Determinar nível baseado no score
            if total_score <= 25:
                level = ReasoningLevel.MINIMAL
                reason = "Simple identification task"
            elif total_score <= 50:
                level = ReasoningLevel.LOW
                reason = "Basic analysis task"
            elif total_score <= 75:
                level = ReasoningLevel.MEDIUM
                reason = "Moderate complexity analysis"
            else:
                level = ReasoningLevel.HIGH
                reason = "Complex/technical analysis"

            # Ajustes baseados em context clues específicos
            level, reason = self._apply_context_adjustments(context, level, reason)

            metadata = {
                "reasoning_level": level.value,
                "total_score": total_score,
                "query_score": query_score,
                "type_score": type_score,
                "detail_score": detail_score,
                "questions_score": questions_score,
                "reason": reason,
                "estimated_time": self.performance_history[level]["avg_time"],
                "expected_success_rate": self.performance_history[level][
                    "success_rate"
                ],
            }

            logger.info(
                f"🧠 Adaptive Reasoning: {level.value} "
                f"(score: {total_score:.1f}, est. time: {metadata['estimated_time']:.1f}s)"
            )

            return level, metadata

        except Exception as e:
            logger.error(f"Error determining reasoning effort: {e}")
            # Fallback seguro
            return ReasoningLevel.LOW, {"reason": "fallback_due_to_error"}

    def _analyze_query_complexity(self, query: str) -> float:
        """Analisa complexidade da query (0-100)."""
        if not query:
            return 50

        query_lower = query.lower()
        words = set(query_lower.split())

        # Detectar indicadores simples
        simple_matches = len(words.intersection(self.simple_keywords))
        if simple_matches >= 2:
            return 10  # Muito simples
        elif simple_matches >= 1:
            return 25  # Simples

        # Detectar indicadores complexos
        complex_matches = len(words.intersection(self.complex_keywords))
        if complex_matches >= 2:
            return 90  # Muito complexo
        elif complex_matches >= 1:
            return 75  # Complexo

        # Detectar indicadores médios
        medium_matches = len(words.intersection(self.medium_keywords))
        if medium_matches >= 1:
            return 50  # Médio

        # Análise baseada em tamanho e estrutura
        word_count = len(words)
        if word_count <= 3:
            return 20  # Queries curtas geralmente são simples
        elif word_count <= 10:
            return 40
        else:
            return 60  # Queries longas podem ser mais complexas

    def _analyze_analysis_type(self, analysis_type: str) -> float:
        """Analisa complexidade do tipo de análise (0-100)."""
        complexity_map = {
            "general": 20,
            "basic": 15,
            "identification": 25,
            "ocr": 60,
            "technical": 80,
            "scientific": 90,
            "medical": 85,
            "artistic": 70,
            "document": 75,
            "comprehensive": 95,
        }

        return complexity_map.get(analysis_type.lower(), 50)

    def _analyze_detail_level(self, detail_level: str) -> float:
        """Analisa complexidade do nível de detalhe (0-100)."""
        level_map = {
            "basic": 20,
            "simple": 15,
            "standard": 40,
            "detailed": 70,
            "comprehensive": 90,
            "in-depth": 85,
        }

        return level_map.get(detail_level.lower(), 50)

    def _analyze_specific_questions(self, questions: Optional[list[str]]) -> float:
        """Analisa complexidade das questões específicas (0-100)."""
        if not questions:
            return 30  # Sem questões específicas = mais simples

        if len(questions) == 1:
            return 40
        elif len(questions) <= 3:
            return 60
        else:
            return 80  # Muitas questões = análise complexa

    def _apply_context_adjustments(
        self, context: AnalysisContext, level: ReasoningLevel, reason: str
    ) -> tuple[ReasoningLevel, str]:
        """Aplica ajustes baseados em contexto específico."""
        query_lower = context.query_text.lower()

        # Forçar MINIMAL para casos muito óbvios
        ultra_simple_patterns = [
            r"\b(que|qual)\s+(emoji|emoticon|ícone)\b",
            r"\b(este|esta|isso)\s+é\s+(que|qual|um|uma)\b",
            r"\b(identifi|reconhec|mostr)\w*\s+(o|a|este|esta)\b",
            r"\b(simples|rápid|básic)\w*\s+(análise|pergunta)\b",
        ]

        for pattern in ultra_simple_patterns:
            if re.search(pattern, query_lower):
                return (
                    ReasoningLevel.MINIMAL,
                    f"Ultra-simple pattern detected: {pattern}",
                )

        # Detectar análise rápida explícita
        if "[análise rápida]" in query_lower:
            if level != ReasoningLevel.MINIMAL:
                return ReasoningLevel.MINIMAL, "Explicit fast analysis requested"

        # Forçar HIGH para casos técnicos
        technical_patterns = [
            r"\b(diagnóstic|médic|científic|técnic)\w*\b",
            r"\b(analise|avalie|interprete)\s+(técnic|científic|médic)\w*\b",
            r"\b(comparação|contraste)\s+(detalhad|profund)\w*\b",
        ]

        for pattern in technical_patterns:
            if re.search(pattern, query_lower):
                if level.value in ["minimal", "low"]:
                    return (
                        ReasoningLevel.MEDIUM,
                        f"Technical pattern requires higher reasoning: {pattern}",
                    )

        # Ajuste baseado no tamanho da imagem (se for muito simples, força minimal)
        if "base64" in context.image_url and len(context.image_url) < 1000:
            # Imagem muito pequena provavelmente é simples
            if level != ReasoningLevel.MINIMAL:
                return (
                    ReasoningLevel.MINIMAL,
                    "Very small image suggests simple content",
                )

        return level, reason

    def update_performance_stats(
        self, level: ReasoningLevel, actual_time: float, success: bool
    ) -> None:
        """Atualiza estatísticas de performance para learning."""
        try:
            stats = self.performance_history[level]

            # Moving average para tempo
            alpha = 0.1  # Learning rate
            stats["avg_time"] = (1 - alpha) * stats["avg_time"] + alpha * actual_time

            # Moving average para success rate
            current_success_rate = 1.0 if success else 0.0
            stats["success_rate"] = (1 - alpha) * stats[
                "success_rate"
            ] + alpha * current_success_rate

            logger.debug(
                f"📊 Updated stats for {level.value}: "
                f"avg_time={stats['avg_time']:.1f}s, success_rate={stats['success_rate']:.3f}"
            )

        except Exception as e:
            logger.error(f"Error updating performance stats: {e}")

    def get_optimization_recommendations(self) -> dict:
        """Retorna recomendações de otimização baseadas no histórico."""
        recommendations = []

        for level, stats in self.performance_history.items():
            if stats["avg_time"] > self._get_target_time(level):
                recommendations.append(
                    {
                        "level": level.value,
                        "issue": "average_time_too_high",
                        "current": stats["avg_time"],
                        "target": self._get_target_time(level),
                        "suggestion": "Consider using lower reasoning effort for similar tasks",
                    }
                )

            if stats["success_rate"] < 0.95:
                recommendations.append(
                    {
                        "level": level.value,
                        "issue": "success_rate_too_low",
                        "current": stats["success_rate"],
                        "target": 0.95,
                        "suggestion": "Consider using higher reasoning effort for better accuracy",
                    }
                )

        return {
            "recommendations": recommendations,
            "performance_history": self.performance_history,
            "optimization_status": "optimal" if not recommendations else "needs_tuning",
        }

    def _get_target_time(self, level: ReasoningLevel) -> float:
        """Retorna tempo alvo para cada nível."""
        targets = {
            ReasoningLevel.MINIMAL: 8.0,
            ReasoningLevel.LOW: 15.0,
            ReasoningLevel.MEDIUM: 30.0,
            ReasoningLevel.HIGH: 60.0,
        }
        return targets[level]


# Global instance
adaptive_reasoning = AdaptiveReasoningSystem()
