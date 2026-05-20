from app.config import AppConfig, load_config
from app.display import (
    clear_screen,
    print_assistant,
    print_assistant_stream,
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

EXIT_COMMAND = '\\q'
RESET_COMMAND = '/reset'
STREAM_COMMAND = '/stream'
FILE_CHUNK_PREFIXES = ('/file_chunk', '/filechunk')


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
        self._use_stream = False

    def run(self) -> None:
        print_system(
            'Чат с ИИ-ассистентом. Команды: /reset, /file_chunk, /stream, \\q — выход.'
        )
        while True:
            user_input = prompt_line()
            if not user_input:
                continue
            if user_input == EXIT_COMMAND:
                break
            if self._handle_command(user_input):
                continue
            self._process_chat_message(user_input)

    def _handle_command(self, text: str) -> bool:
        if text == RESET_COMMAND:
            self._history.clear()
            clear_screen()
            print_system('История очищена.')
            return True

        if text == STREAM_COMMAND:
            self._use_stream = not self._use_stream
            mode = 'включён' if self._use_stream else 'выключен'
            print_system(f'Потоковый вывод {mode}.')
            return True

        for prefix in FILE_CHUNK_PREFIXES:
            if text.startswith(prefix):
                args = text[len(prefix) :].strip()
                self._run_file_chunk(parse_file_chunk_args(args))
                return True

        return False

    def _process_chat_message(self, user_input: str) -> None:
        try:
            message_text = expand_file_references(user_input)
        except (FileNotFoundError, ValueError, OSError) as error:
            print_error(str(error))
            return

        self._history.add('user', message_text)
        api_messages = self._history.to_api_format(self._config.system_prompt)

        try:
            if self._use_stream:
                response = print_assistant_stream(
                    self._client.send_stream(api_messages)
                )
            else:
                response = self._client.send(api_messages)
                print_assistant(response)
        except KeyboardInterrupt:
            self._history.remove_last()
            print_system('Запрос прерван. Введите новое сообщение.')
            return
        except Exception as error:
            self._history.remove_last()
            print_error(f'Ошибка при обращении к LLM: {error}')
            return

        self._history.add('assistant', response)

    def _run_file_chunk(self, options: ChunkOptions) -> None:
        path_input = prompt_line('Введите путь до файла')
        if path_input == EXIT_COMMAND:
            return

        user_prompt = prompt_line(
            'Принято. Что нужно сделать для каждого фрагмента (User Prompt)?'
        )
        if user_prompt == EXIT_COMMAND:
            return

        try:
            file_text = read_text_file(path_input)
        except (FileNotFoundError, ValueError, OSError) as error:
            print_error(str(error))
            return

        chunks = split_into_chunks(file_text, options)
        if not chunks:
            print_error('Файл пуст или не удалось разбить на фрагменты.')
            return

        print_system('Принято. Начинаю обработку:')
        for index, chunk in enumerate(chunks):
            try:
                if self._use_stream:
                    print_assistant_stream(
                        self._client.send_stream_chunk(user_prompt, chunk)
                    )
                else:
                    response = self._client.send_chunk(user_prompt, chunk)
                    print_assistant(response)
            except KeyboardInterrupt:
                print_system('Обработка прервана.')
                return
            except Exception as error:
                print_error(f'Ошибка при обращении к LLM: {error}')
                return

            if options.auto_advance or index == len(chunks) - 1:
                continue

            while True:
                step = prompt_line()
                if step == EXIT_COMMAND:
                    return
                if step == '':
                    break

        print_system('Обработка файла завершена.')
