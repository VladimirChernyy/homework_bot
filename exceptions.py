class HTTPError(Exception):
    def __init__(self, request):
        message = (
            f'Эндпоинт {request.url} недоступен. '
            f'Код ответа API: {request.status_code}'
        )
        super().__init__(message)

