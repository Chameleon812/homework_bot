class EasyException(Exception):
    """Не требует отправки в телеграм."""
    pass


class HardException(Exception):
    """Требует отправки в телеграм."""
    pass
