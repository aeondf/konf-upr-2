# Граф зависимостей пакетов Ubuntu

Практическая работа №2 по дисциплине «Конфигурационное управление»,
вариант 27.

Программа строит граф зависимостей пакета Ubuntu (формат apt). Данные
берутся прямо из индекса репозитория, без apt и сторонних библиотек.

Сейчас сделан этап 1: параметры командной строки и их проверка.

## Параметры

```
./run.sh --package ИМЯ --repo URL_ИЛИ_ФАЙЛ [--test] [--version ВЕРСИЯ] [--output ФАЙЛ.png]
```

| Параметр | Что это | Проверка |
|---|---|---|
| `--package` | имя пакета | обязателен; строчные буквы, цифры, `+ - .` (в тестовом режиме — заглавные латинские буквы) |
| `--repo` | URL файла `Packages` репозитория или путь к тестовому репозиторию | обязателен; `http`/`https` адрес (в тестовом режиме — существующий файл) |
| `--test` | режим тестового репозитория | флаг |
| `--version` | версия пакета | необязателен; начинается с цифры, без пробелов |
| `--output` | файл с картинкой графа | по умолчанию `graph.png`; расширение `.png`, папка должна существовать |

Параметры проверяются библиотекой pydantic. При ошибке печатается
сообщение `error: ...` и программа завершается с кодом 1. Если не указан
обязательный параметр, ошибку выдаёт argparse (код 2).

## Как запустить

Нужен Python 3.12 и [uv](https://docs.astral.sh/uv/).

```sh
uv sync                      # поставить зависимости
./run.sh --help              # справка по параметрам
uv run pytest                # тесты
uv run ruff check src tests  # линтер
sh scripts/stage1.sh         # демонстрация этапа 1
```

## Пример работы

```
$ ./run.sh --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --version 8.5.0-2ubuntu10
package=curl
repo=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
test=False
version=8.5.0-2ubuntu10
output=graph.png

$ ./run.sh --package a --repo repos/simple.txt --test
error: package: 'a' must be capital Latin letters in test mode

$ ./run.sh --package curl --repo ftp://example.org/Packages
error: repo: 'ftp://example.org/Packages' is not an http(s) URL
```

## Структура

```
src/depgraph/
    main.py      запуск, чтение параметров
    config.py    проверка параметров (pydantic)
tests/           тесты
repos/           тестовые репозитории
scripts/         демонстрационные скрипты
run.sh           скрипт запуска
```
