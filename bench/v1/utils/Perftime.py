import time
from functools import wraps


def perf_time(func):
    """Décorateur pour mesurer le temps d'exécution d'une fonction."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        description = kwargs.get("description")
        if description is None and len(args) > 2:
            description = args[2]
        label = (
            description.strip()
            if isinstance(description, str) and description.strip()
            else func.__name__
        )
        print(f"[PERF] {label}: {duration:.3f}s")
        return result

    return wrapper


class PerfTimer:
    """Context manager pour mesurer le temps d'exécution d'un bloc de code.

    Usage:
        with PerfTimer("Traitement des données"):
            # code à mesurer
            process_data()

        # Avec récupération du temps
        with PerfTimer("Import CSV") as timer:
            import_csv()
        print(f"Temps total: {timer.duration:.3f}s")
    """

    def __init__(self, label="Bloc de code", silent=False):
        """
        Args:
            label: Description du bloc de code à mesurer
            silent: Si True, n'affiche pas le temps automatiquement
        """
        self.label = label
        self.silent = silent
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        """Démarre le chronomètre."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Arrête le chronomètre et affiche le temps."""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time

        if not self.silent:
            print(f"[PERF] {self.duration:.3f}s --> {self.label}")

        # Retourne False pour propager les exceptions
        return False

    def elapsed(self):
        """Retourne le temps écoulé depuis le début (sans arrêter le timer)."""
        if self.start_time is None:
            return 0
        return time.perf_counter() - self.start_time
