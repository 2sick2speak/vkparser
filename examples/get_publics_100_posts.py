import re
import os
import time
import pymongo

from vkparser.vkrequests import VkRequests
from vkparser.datareader import DataReader
from vkparser.datawriter import DataWriter
from multiprocessing import Process, cpu_count
from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DB_NAME, DIRECTORY

def get_walls(token, item_ids):

	print "Start "  + str(os.getppid()) + " " + str(os.getpid())

	# create instance of vkrequest
	vk_requests = VkRequests(token, API_VERSION, RANDOM_METHOD_NAMES)

	print "Total walls to get: {amount}".format(amount=len(item_ids))

	i = 0

	# create instance to write to DB
	datawriter = DataWriter(DB_NAME, True)
	# constants
	BULK_SIZE = 25 # amount of requests in vksctipt
	CODE_METHOD_NAME = "wall.get" # request name
	CHANGE_VAR = "owner_id" 
	METHOD_NAME = "execute"

	for i in range(0, len(item_ids)/BULK_SIZE+1):

		# add time lag to avoid bans
		time.sleep(0.33)
		walls_info = []

		# get ids portion
		ids_bulk = item_ids[i*BULK_SIZE:(i+1)*BULK_SIZE]
		# create vkscript request
		vk_code =  vk_requests.script_request(CODE_METHOD_NAME, CHANGE_VAR, ids_bulk)
		# add params to request
		fix_params = "code={code}&count=100".format(code=vk_code)
		# send request wtih vkscript to vk 
		request = vk_requests.single_request(method_name=METHOD_NAME, fix_params=fix_params, token_flag=True)
		response = vk_requests.make_single_request(request)

		print "Process: {proc} Getting publics walls:  ({size}/{total})".format(
			proc=str(os.getpid()), size=i*BULK_SIZE, total=len(item_ids))

		
		# add public_id field to response and count failed items
		j = 0
		failed = 0
		for item in response:
			if not isinstance(item, bool):
				item["public_id"] = ids_bulk[j]
				walls_info.append(item)
			else: 
				failed += 1
			j += 1

		# save to db
		datawriter.write_items_db("publics_walls", walls_info, create_index=True, index_fields=["public_id"])

		# send random request every 3rd request to avoid bans
		if not i % 3:
				vk_requests.make_single_request(fake=True)

	print "End " + " " + str(os.getppid()) + " " + str(os.getpid())

if __name__ == "__main__":

	start = time.time()

	# get public ids
	data_reader = DataReader("./data/" + DIRECTORY + "/public_ids.csv")
	publics_ids = data_reader.read_ids()

	# create single process for each token 
	num_processes = len(TOKEN_LIST) 
	bulk = len(publics_ids)/num_processes + 1
	process=[]

	for i in range(0, num_processes):
			print i

			# parallel process ids
			p = Process(target=get_walls, args=([TOKEN_LIST[i]],publics_ids[i*bulk:(i+1)*bulk],))
			p.start()
			process.append(p)

	for p in process:
			p.join()

	print time.time()-start



	
	