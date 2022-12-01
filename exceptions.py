class EasyException(Exception):
    """Не требует отправки в телеграм."""


class HardException(Exception):
    """Требует отправки в телеграм."""
