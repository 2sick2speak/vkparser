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
	BULK_SIZE = 100 # amount of posts per request
	METHOD_NAME = "wall.get"

	for item in item_ids:
		
		offset = 0

		# fix params to request
		fix_params = "owner_id={id}".format(id=item)

		# get walls counter
		req_url = vk_requests.single_request(METHOD_NAME, fix_params, True)
		response = vk_requests.make_single_request(req_url)
		result = []

		# if posts counter > 0 
		if response and "count" in response:
			if response["count"]:
				count = response["count"]

				# make offset request to vk to get all posts
				result = vk_requests.make_offset_request(METHOD_NAME, fix_params, count, BULK_SIZE, True)
				result["public_id"] = item

				print "Getting publics walls:  ({size}/{total}) Posts (total/api): {count}/{result}".format(
					size=i, total=len(item_ids), count=response["count"], result=len(result["items"]))

		# send random request every 3rd request to avoid bans
		if not i % 3:
				vk_requests.make_single_request(fake=True)

		if len(result) > 0:

			# save to db
			datawriter.write_items_db("public_walls_flat", result["items"],
			 create_index=True, index_fields=["owner_id", "id"])
		
		i += 1



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


	
	