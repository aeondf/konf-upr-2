"""Общий интерфейс репозиториев пакетов."""


class RepositoryError(Exception):
    """Ошибка получения данных из репозитория."""


class Repository:
    """Источник сведений о пакетах и их зависимостях."""

    def load(self) -> None:
        """Читает данные репозитория."""
        raise NotImplementedError

    def select(self, name: str, version: str | None) -> str:
        """Проверяет, что пакет есть, и возвращает выбранную версию."""
        raise NotImplementedError

    def dependencies(self, name: str) -> list[str]:
        """Возвращает прямые зависимости пакета."""
        raise NotImplementedError

    def names(self) -> list[str]:
        """Возвращает имена всех пакетов репозитория."""
        raise NotImplementedError
