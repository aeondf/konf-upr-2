# Граф зависимостей пакетов Ubuntu

Практическая работа №2 по дисциплине «Конфигурационное управление»,
вариант 27.

Программа строит граф зависимостей пакета Ubuntu (формат apt). Данные
берутся прямо из индекса репозитория, без apt и сторонних библиотек.

Сделаны этапы 1–2: параметры командной строки и их проверка, получение
прямых зависимостей пакета из репозитория Ubuntu.

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

## Откуда берутся зависимости

Репозиторий Ubuntu хранит индекс пакетов — файл `Packages` (обычно
сжатый, `Packages.gz`). Например, для Ubuntu 24.04, раздел `main`:

```
http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
```

Внутри — описания пакетов, разделённые пустой строкой:

```
Package: curl
Version: 8.5.0-2ubuntu10
Depends: libc6 (>= 2.34), libcurl4t64 (= 8.5.0-2ubuntu10), zlib1g (>= 1:1.1.4)
```

Программа скачивает индекс стандартным `urllib`, распаковывает (`.gz`
или `.xz`) и разбирает сама. Прямые зависимости — это пакеты из полей
`Pre-Depends` и `Depends`. Ограничения версий `(>= 2.34)` и архитектуры
`:any` отбрасываются. Если указано несколько вариантов через `|`,
берётся первый — его apt и ставит по умолчанию.

**Версия.** В одном индексе может быть несколько версий пакета (например,
в репозитории Docker их десятки). С `--version` берётся указанная,
без него — последняя в индексе. Если такой версии нет, программа
покажет, какие есть.

**Ошибки:** адрес недоступен или файл не найден (404), архив повреждён,
в файле нет пакетов, нет такого пакета, нет такой версии.

## Как запустить

Нужен Python 3.12 и [uv](https://docs.astral.sh/uv/).

```sh
uv sync                      # поставить зависимости
./run.sh --help              # справка по параметрам
uv run pytest                # тесты
uv run ruff check src tests  # линтер
sh scripts/stage1.sh         # демонстрация этапа 1
sh scripts/stage2.sh         # демонстрация этапа 2 (нужен интернет)
```

## Пример работы

```
$ ./run.sh --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
Package: curl 8.5.0-2ubuntu10
Direct dependencies (3):
  libc6
  libcurl4t64
  zlib1g

$ ./run.sh --package docker-ce --repo https://download.docker.com/linux/ubuntu/dists/noble/stable/binary-amd64/Packages --version "5:26.0.0-1~ubuntu.24.04~noble"
Package: docker-ce 5:26.0.0-1~ubuntu.24.04~noble
Direct dependencies (6):
  containerd.io
  docker-ce-cli
  iptables
  libseccomp2
  libc6
  libsystemd0

$ ./run.sh --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --version 1.0
error: version '1.0' of 'curl' not found; available (1): 8.5.0-2ubuntu10

$ ./run.sh --package a --repo repos/simple.txt --test
error: package: 'a' must be capital Latin letters in test mode

$ ./run.sh --package curl --repo ftp://example.org/Packages
error: repo: 'ftp://example.org/Packages' is not an http(s) URL
```

## Структура

```
src/depgraph/
    main.py        запуск, чтение параметров
    config.py      проверка параметров (pydantic)
    repository.py  общий интерфейс репозитория
    apt.py         чтение индекса пакетов Ubuntu
tests/           тесты
repos/           тестовые репозитории
scripts/         демонстрационные скрипты
run.sh           скрипт запуска
```
