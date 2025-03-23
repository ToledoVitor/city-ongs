import time
from functools import wraps
from typing import Callable

from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse


class PerformanceMetrics:
    """
    Classe para coletar e armazenar métricas de performance.
    """

    def __init__(self):
        self.metrics: dict[str, list[float]] = {
            "response_times": [],
            "db_query_counts": [],
            "db_query_times": [],
            "cache_hits": [],
            "cache_misses": [],
        }

    def add_metric(self, category: str, value: float) -> None:
        """Adiciona uma métrica à categoria especificada."""
        if category in self.metrics:
            self.metrics[category].append(value)

    def get_average(self, category: str) -> float:
        """Calcula a média de uma categoria de métricas."""
        values = self.metrics.get(category, [])
        return sum(values) / len(values) if values else 0.0

    def get_summary(self) -> dict[str, float]:
        """Retorna um resumo com médias de todas as métricas."""
        return {category: self.get_average(category) for category in self.metrics}


class PerformanceMonitor:
    """
    Monitor de performance para views Django.
    """

    def __init__(self):
        self.metrics = PerformanceMetrics()

    def monitor_view(self, view_func: Callable) -> Callable:
        """
        Decorator para monitorar performance de views.
        """

        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            start_time = time.time()
            initial_queries = len(connection.queries)

            # Monitora cache hits/misses
            initial_hits = cache.get("cache_hits", 0)
            initial_misses = cache.get("cache_misses", 0)

            try:
                response = view_func(request, *args, **kwargs)

                # Coleta métricas
                end_time = time.time()
                final_queries = len(connection.queries)

                self.metrics.add_metric("response_times", end_time - start_time)
                self.metrics.add_metric(
                    "db_query_counts", final_queries - initial_queries
                )

                # Calcula tempo total de queries
                query_time = sum(
                    float(q.get("time", 0))
                    for q in connection.queries[initial_queries:final_queries]
                )
                self.metrics.add_metric("db_query_times", query_time)

                # Atualiza métricas de cache
                final_hits = cache.get("cache_hits", 0)
                final_misses = cache.get("cache_misses", 0)
                self.metrics.add_metric("cache_hits", final_hits - initial_hits)
                self.metrics.add_metric("cache_misses", final_misses - initial_misses)

                return response

            except Exception:
                # Em caso de erro, ainda registra as métricas coletadas
                end_time = time.time()
                self.metrics.add_metric("response_times", end_time - start_time)
                raise

        return wrapper

    def get_metrics_summary(self) -> dict[str, float]:
        """Retorna um resumo das métricas coletadas."""
        return self.metrics.get_summary()


# Instância global do monitor
performance_monitor = PerformanceMonitor()


def monitor_performance(view_func: Callable) -> Callable:
    """
    Decorator para facilitar o uso do monitor de performance.

    Uso:
        @monitor_performance
        def my_view(request):
            ...
    """
    return performance_monitor.monitor_view(view_func)
