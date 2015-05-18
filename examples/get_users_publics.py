import re
import os
import time

from vkparser.vkrequests import VkRequests
from vkparser.datareader import DataReader
from vkparser.datawriter import DataWriter
from multiprocessing import Process, cpu_count
from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DB_NAME, DIRECTORY


def get_publics(token, users_ids):

	print "Start "  + str(os.getppid()) + " " + str(os.getpid())

	# create parser for single request
	vk_requests = VkRequests(token, API_VERSION, RANDOM_METHOD_NAMES)

	# constants
	BULK_SIZE = 25
	CODE_METHOD_NAME = "groups.get"
	CHANGE_VAR = "user_id"
	METHOD_NAME = "execute"

	print "Total users: {amount}".format(amount=len(users_ids))

	publics_info = []
	publics_ids = set()
	failed = 0

	print "Process: " + str(os.getpid()) + " len users_ids: " + str(len(users_ids))

	for i in range(0, len(users_ids)/BULK_SIZE+1):

		# add time lag to avoid bans
		time.sleep(0.33)

		ids_bulk = users_ids[i*BULK_SIZE:(i+1)*BULK_SIZE]

		# create request on VkScript language
		vk_code =  vk_requests.script_request(CODE_METHOD_NAME, CHANGE_VAR, ids_bulk)
		fix_params = "code={code}".format(code=vk_code)
		request = vk_requests.single_request(method_name=METHOD_NAME, fix_params=fix_params, token_flag=True)
		response = vk_requests.make_single_request(request)

		print "Process: {proc} Getting users publics:  ({size}/{total})".format(
			proc=str(os.getpid()), size=i*BULK_SIZE, total=len(users_ids))

		# add user_id field to response and count failed items
		j = 0
		for item in response:
			if not isinstance(item, bool):
				item["user_id"] = ids_bulk[j]
				publics_info.append(item)
				publics_ids |= set(item["items"])
			else: 
				failed += 1
			j += 1

		# sent random request every 3rd request to avoid bans
		if not i % 3:
				vk_requests.make_single_request(fake=True)

	print "Total publics: " + str(len(publics_ids))

	print "Process: {proc} Publics: {publics} Users: {users} Failed: {failed}".format(
		proc=str(os.getpid()), publics=str(len(publics_info)),
		users=len(users_ids), failed=failed)

	# save data to DB
	datawriter = DataWriter(DB_NAME, True)
	datawriter.write_items_db("users_publics", publics_info, create_index=True, index_fields=["user_id"])
	datawriter.write_items_db("publics_total", publics_ids, 
		create_index=True, index_fields=["public_id"], field_name="public_id")

	print "End " + " " + str(os.getppid()) + " " + str(os.getpid())

if __name__ == "__main__":

	# read all users ids from file
	data_reader = DataReader("./data/" + DIRECTORY + "/users_ids.txt")
	total_ids = data_reader.read_ids()

	# read ready user ids from database
	db_reader = DataReader(DB_NAME, True)
	ready_users = db_reader.read_items_db("users_publics")
	ready_ids = [item["user_id"] for item in ready_users]
	users_ids = list(set(total_ids)-set(ready_ids))

	# create single process for each token 

	num_processes = len(TOKEN_LIST) 
	bulk = len(users_ids)/num_processes + 1
	process=[]

	for i in range(0, num_processes):
			print i
			p = Process(target=get_publics, args=([TOKEN_LIST[i]],users_ids[i*bulk:(i+1)*bulk],))
			p.start()
			process.append(p)

	for p in process:
			p.join()


	# dump data into text file

	publics_reader = DataReader(DB_NAME, True)
	publics_info = publics_reader.read_items_db("users_publics")
	print len(publics_info)
	data_writer = DataWriter("./data/" + DIRECTORY + "/users_publics.json")
	data_writer.write_json(publics_info)