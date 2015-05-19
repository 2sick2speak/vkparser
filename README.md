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
- vkrequests - работа с API VK. Делится на 2 типа
-- генерация текста запроса
-- отправка самого запроса


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

*Инициализация объекта*

    from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DIRECTORY # импорт настроек

    vk_requests = VkRequests(TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES) # создание класса, который будет стучаться в АПИ

*Одиночный запрос*

Получение информации по отдельной группе (https://vk.com/dev/groups.getById)

    fields = "description,members_count" # дополнительные поля для запроса
	method_name = "groups.getById" # имя вызова API
	group_id = -145384 # id группы

    fix_params = "group_id={id}&fields={fields}".format(
			ids=group_id, fields=fields) # строка с дополнительным набором параметров

	request = vk_requests.single_request(method_name=method_name, fix_params=fix_params, token_flag=True) # формируем текст одиночного запроса 
	response = vk_requests.make_single_request(request) # посылаем одиночный запрос

*Избегаем банов*

Особенности работы API Вконтакте в том, что он банит большое количество подряд идущих однотипных запросов. Чтобы это избежать, раз в N запросов стоит слать запрос на случайный вызов API, определенный в RANDOM_METHOD_NAMES. Для этого есть 2 способа:

    req_url = vk_requests.random_request() # получаем url запроса на случайный метод api
    vk_requests.make_single_request(req_url) # посылаем одиночный запрос в АПИ

или
    
    vk_requests.make_single_request(fake=True) # просто указываем флаг, что надо послать одиночный фейковый запрос. Берет автоматически случайный урл из RANDOM_METHOD_NAMES и шлет запрос

Также контакт банит очень частую отправку запросов, поэтому во всех примерах добавлено time.sleep(time_in_sec) между запросами.
Эмпирически установлено, что значение между 0.33 - 0.5 вполне достаточно

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

Вызовы некоторых API позволяют получать информацию сразу по массиву id интересующих сущностей, например, получение информации о юзерах https://vk.com/dev/users.get. Но на стороне VK есть ограничение на максимальную длину запросов (примерно 2500 символов на начало 2015 года). Поэтому если нам надо получить информацию о 100к пользователей - мы не можем это сделать за один запрос.

Поэтому для работы с такой ситуацией есть метод, который генерит запросы в удобном формате
    
    mass_request(method_name, fix_params, ids, mass_field_name, token_flag=False, token_id=None)
    # method_name - имя метода из API
    # fix_params - набор фиксированных параметров
    # ids - список id сущностей
    # mass_field_name - поле, в которое записываются в запросе массив id (например, user_ids, group_ids и так далее)
    # token_flag  - прикреплять ли к запросу access_token
    # token_id - порядковый номер токена из массива токенов. Если не стоит - берется случайный

Пример работы для получения информации пользователей

    users_info = [] # список для ответов от апи
	METHOD_NAME = "users.get" # имя вызова АПИ
	FIX_PARAMS = 'fields=bdate,home_town,country,universities,last_seen,sex,'\
	'city,personal,interests,activities,occupation,relation,music,about,quotes,'\
	'domain,has_mobile,contacts,site,education,schools,relatives,connections,movies,tv,books' # набор дополнительных полей запроса
	MASS_FIELD_NAME = "user_ids" # поле, к которому будет прикрепляться массив id
	bulk_size = 250 # количество id в одном запросе 

	for i in range(0, len(users_ids)/bulk_size+1):

		time.sleep(0.33) # задержка для избежания банов
		ids_bulk = users_ids[bulk_size*i : bulk_size*(i+1)] # получаем кусок id пользователей
		req_url = vk_requests.mass_request(METHOD_NAME, FIX_PARAMS, ids_bulk, MASS_FIELD_NAME, True) # формируем текст запроса
		result = vk_requests.make_single_request(req_url) # посылаем запрос

		users_info.extend(result)		 # сохраняем результат
		if not i % 3:
			vk_requests.make_single_request(fake=True) # шлем случайные запросы, чтобы нас не забанили


*One-to-one запросы*

Ряд методов вконтакте позволяет получить информацию только по одной сущности. Для их массовой обработки можно генерировать запросы через VKScript, что позволяет отправлять до 25 запросов за раз (https://vk.com/dev/execute). Для этого в библиотечке есть метод, генерирующий простой VkScript код.

    script_request(method_name, change_var, values, fix_params=None)

    # method_name - имя метода из API
    # change_var - переменная, которая меняется в каждом запросе
    # values - список id сущностей
    # fix_params - набор фиксированных параметров. Пока не работает :)

Пример работы для получения последних 100 записей со стены юзеров

    BULK_SIZE = 25 # количество запросов в коде
	CODE_METHOD_NAME = "wall.get" # метод, для вызова из кода 
	CHANGE_VAR = "owner_id" # поле, которое меняется
	METHOD_NAME = "execute" # метод execute
	walls_info = []  # сохраняем результат

	for i in range(0, len(item_ids)/BULK_SIZE+1):

		time.sleep(0.33) # задержка для избежания банов

		ids_bulk = item_ids[i*BULK_SIZE:(i+1)*BULK_SIZE] # выбираем набор id
		vk_code =  vk_requests.script_request(CODE_METHOD_NAME, CHANGE_VAR, ids_bulk) # генерируем VkScript код
		fix_params = "code={code}&count=100".format(code=vk_code) # добавляем его в параметры обычного запроса
		request = vk_requests.single_request(method_name=METHOD_NAME, fix_params=fix_params, token_flag=True) # генерируем обычный запрос с VkScript

		response = vk_requests.make_single_request(request) # посылаем запрос

		j = 0
		failed = 0
		for item in response: обрабатываем ответы на запрос.
			if not isinstance(item, bool): # Если один из методов отработал с ошибкой - то в массиве ответов будет False
				item["user_id"] = ids_bulk[j]
				walls_info.append(item)
			else: 
				failed += 1
			j += 1  

		if not i % 3:
				vk_requests.make_single_request(fake=True) # шлем случайные запросы, чтобы нас не забанили





