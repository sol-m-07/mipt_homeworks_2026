from app.config import AppConfig, load_config
from app.display import (
    clear_screen,
    print_assistant,
    print_error,
    print_system,
    prompt_line,
)
from app.files import (
    ChunkOptions,
    expand_file_references,
    parse_file_chunk_args,
    read_text_file,
    split_into_chunks,
)
from app.history import HistoryManager
from app.llm_client import LLMClient

EXIT_COMMAND = r'\q'
RESET_COMMAND = '/reset'
FILE_CHUNK_PREFIXES = ('/file_chunk', '/filechunk')
WELCOME_MESSAGE = r'Чат с ИИ-ассистентом. Команды: /reset, /file_chunk, \q — выход.'
FILE_READ_ERRORS = (FileNotFoundError, ValueError, OSError)


def _report_file_error(error: Exception) -> None:
    print_error(str(error))


def _read_file_safe(path: str) -> str | None:
    try:
        return read_text_file(path)
    except FILE_READ_ERRORS as error:
        _report_file_error(error)
        return None


def _expand_refs_safe(text: str) -> str | None:
    try:
        return expand_file_references(text)
    except FILE_READ_ERRORS as error:
        _report_file_error(error)
        return None


def _read_file_chunk_inputs() -> tuple[str, str] | None:
    path_input = prompt_line('Введите путь до файла')
    if path_input == EXIT_COMMAND:
        return None

    user_prompt = prompt_line('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
    if user_prompt == EXIT_COMMAND:
        return None

    return path_input, user_prompt


def _process_single_chunk(app: 'ChatApp', user_prompt: str, chunk: str) -> bool:
    try:
        response = app._client.send_chunk(user_prompt, chunk)
    except KeyboardInterrupt:
        print_system('Обработка прервана.')
        return False
    except Exception as error:
        print_error(f'Ошибка при обращении к LLM: {error}')
        return False

    print_assistant(response)
    return True


def _advance_file_chunk(index: int, total: int, options: ChunkOptions) -> bool:
    if options.auto_advance or index == total - 1:
        return True

    while True:
        step = prompt_line()
        if step == EXIT_COMMAND:
            return False
        if step == '':
            return True


def _process_file_chunks(
    app: 'ChatApp',
    user_prompt: str,
    chunks: list[str],
    options: ChunkOptions,
) -> None:
    print_system('Принято. Начинаю обработку:')
    for index, chunk in enumerate(chunks):
        if not _process_single_chunk(app, user_prompt, chunk):
            return
        if not _advance_file_chunk(index, len(chunks), options):
            return

    print_system('Обработка файла завершена.')


def run_file_chunk(app: 'ChatApp', options: ChunkOptions) -> None:
    inputs = _read_file_chunk_inputs()
    if inputs is None:
        return

    path_input, user_prompt = inputs
    file_text = _read_file_safe(path_input)
    if file_text is None:
        return

    chunks = split_into_chunks(file_text, options)
    if not chunks:
        print_error('Файл пуст или не удалось разбить на фрагменты.')
        return

    _process_file_chunks(app, user_prompt, chunks, options)


class ChatApp:
    def __init__(
        self,
        config: AppConfig | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self._config = config or load_config()
        self._history = HistoryManager(
            limit_message=self._config.limit_message,
            limit_chars=self._config.limit_chars,
        )
        self._client = client or LLMClient(self._config)

    def run(self) -> None:
        print_system(WELCOME_MESSAGE)
        while True:
            user_input = prompt_line()
            if self._handle_input(user_input):
                break

    def _handle_input(self, user_input: str) -> bool:
        if not user_input:
            return False
        if user_input == EXIT_COMMAND:
            return True
        if self._handle_command(user_input):
            return False
        self._process_chat_message(user_input)
        return False

    def _handle_command(self, text: str) -> bool:
        if text == RESET_COMMAND:
            self._history.clear()
            clear_screen()
            print_system('История очищена.')
            return True

        for prefix in FILE_CHUNK_PREFIXES:
            if text.startswith(prefix):
                args = text[len(prefix) :].strip()
                run_file_chunk(self, parse_file_chunk_args(args))
                return True

        return False

    def _process_chat_message(self, user_input: str) -> None:
        message_text = _expand_refs_safe(user_input)
        if message_text is None:
            return

        self._history.add('user', message_text)
        response = self._fetch_chat_response()
        if response is None:
            return

        self._history.add('assistant', response)

    def _fetch_chat_response(self) -> str | None:
        api_messages = self._history.to_api_format(self._config.system_prompt)
        try:
            response = self._client.send(api_messages)
        except KeyboardInterrupt:
            self._history.remove_last()
            print_system('Запрос прерван. Введите новое сообщение.')
            return None
        except Exception as error:
            self._history.remove_last()
            print_error(f'Ошибка при обращении к LLM: {error}')
            return None

        print_assistant(response)
        return response
