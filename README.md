VkParser
==============
Простая библиотечка для работы с API VK

Сторонние зависимости
    pymongo
    requests

для установки зависимостей надо выполнить команду
    python setup.py install

Для запуска примеров требуется внести свои данные в файл настроек examples/setup.py
    TOKEN_LIST - список токенов для доступа к API
    RANDOM_METHOD_NAMES - список методов, на которые надо слать случайные запросы
    API_VERSION - версия VK API 
    DB_NAME - имя базы, куда читать/писать данные
    DIRECTORY - имя директории, куда сохранять дампы данных (если это требуется)

Запуск примеров
    python -m examples.example_name

Описание библиотеки vkparser
==============

- datareader - обработка входных данных (БД или файлы)
- datawriter - сохранение выходных данных (БД или файлы)
- vkrequests - работа с API VK


DataReader
--------
Пример использования
    dir_name = 'sample.txt' # имя файла
    db_name 'sample_db' # имя базы данных
    file_reader = DataReader(dir_name) # создаем объект для чтения из файла
    db_reader = DataReader(DB_NAME, True) # создаем объект для чтения из БД

    ids = file_reader.read_ids() # читаем список id из файла. Файл должен состоять из одной колонки без заголовков
    items = file_reader.read_json() # читаем json c данными из файла

    table_name = "sample_table" # имя коллекции в БД
    fields_name = ['field_1','field_2'] # список возвращаемых полей. По дефолту возвращаются все поля, кроме служебного _id
    items = db_reader.read_items_db(table_name, fields_name) # читаем из базы данные


DataWriter
--------

VkRequests
--------


