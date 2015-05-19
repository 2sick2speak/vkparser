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

Подключение без MongoDB
--------
Достаточно забрать себе файлик vkparser/vkrequests.py, он не привязан к монге. 

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

Принцип работы схож в DataReader.
Пример использования

    dir_name = 'sample.txt' # имя файла
    db_name 'sample_db' # имя базы данных
    file_writer = DataWriter(dir_name) # создаем объект для чтения из файла
    db_writer = DataWriter(DB_NAME, True) # создаем объект для чтения из БД

    sample_ids = [11,12,13,14]
    sample_json = [{"field_1":11, "field2":12}, {"field1":13, "field2":14}]

    file_writer.write_ids(sample_ids) # пишем список id в файл
    file_writer.write_json(sample_json) # пишем json c данными в файл

    table_name = "sample_table" # имя коллекции в БД
    fields_name = ['field_1','field_2'] # список полей, по которым создавать индекс

    db_writer.write_items_db(table_name, sample_json) # записываем список dictionaries в базу. По дефолту индекс не создается
    
    db_writer.write_items_db(table_name, sample_json, create_index=True, index_fields=fields_name) # записываем данные и создаем составной индекс на поля fields_name
    
    db_writer.write_items_db(table_name, sample_ids, field_name='user_id') # записываем список айдишников в базу, конвертируя список из int в формат {"field_name": id}



VkRequests
--------

Запросы к API контакта делятся на 3 вида:

- one-to-many - запрос на получение списка сущностей, принадлежащих другой сущности. Такие запросы сопровождаются полями offset и count (хотя иногда можно запросить сразу все). Например - список постов конкретного пользователя (https://vk.com/dev/wall.get), список групп пользователя (https://vk.com/dev/groups.get)
- many-to-one - запрос на получение информации по списку сущностей. Такие запросы сопровождаюся полем, отвечающим за список сущностей - users_ids, items_ids и тд. Например - информация по профилям пользователей (https://vk.com/dev/users.get), информация по группам (https://vk.com/dev/groups.getById)
- one-to-one - запрос на получение информации по одной сущности. Самый быстрый способ работы с такими сущностями - через VkScript запросы. Например - список друзей (https://vk.com/dev/friends.get)

**N.B. Разделение условное и выведено эмпирически**

Примеры

    from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DIRECTORY # импорт настроек

    vk_requests = VkRequests(TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES) # создание класса, который будет стучаться в АПИ

Особенности работы API Вконтакте в том, что он банит большое количество подряд идущих однотипных запросов. Чтобы это избежать, раз в N запросов стоит слать запрос на случайный вызов API, определенный в RANDOM_METHOD_NAMES. Для этого есть 2 способа:

    req_url = vk_requests.random_request() # получаем url запроса на случайный метод api
    vk_requests.make_single_request(req_url) # посылаем одиночный запрос в АПИ

или
    
    vk_requests.make_single_request(fake=True) # просто указываем флаг, что надо послать одиночный фейковый запрос. Берет автоматически случайный урл из RANDOM_METHOD_NAMES и шлет запрос

*One-to-many запросы*

Когда возникают ситуации, что надо получить список айтемов для какой-то сущности (например, список постов со стены). Для этого есть метод 

    make_offset_request(method_name, fix_params, count, bulk_size,token_flag=False, req_freq=0.3, fake_freq=3)
    # method_name - имя метода из API
    # fix_params - набор фиксированных параметров
    # count - общее количество айтемов, которое требуется забрать
    # bulk_size - количество айтемов, которые надо забирать за один запрос
    # token_flag  - прикреплять ли к запросу access_token
    # req_freq - частота запросов в секунду, чтобы избежать бана 
    # fake_req - частота отправления фейковый запросов (по дефолту - каждый третий)

Пример использования для метода groups.getMembers (https://vk.com/dev/groups.getMembers)

    bulk_size = 1000 # получать будем 1000 пользователей за раз
	method_name = "groups.getMembers" # имя метода апи
	members_count = 5000 # общее количество юзеров в группе. Для получение этого значения можно вызвать метод https://vk.com/dev/groups.getById
	fix_params = "group_id={group_id}".format(group_id=-1) # id группы
	result = vk_requests.make_offset_request(method_name, fix_params, members_count, bulk_size, True) # делаем offset запрос на получение списка юзеров

*Many-to-one запросы*





