import re
import time
import os

from vkparser.vkrequests import VkRequests
from multiprocessing import Process
from vkparser.datareader import DataReader
from vkparser.datawriter import DataWriter
from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DB_NAME,DIRECTORY

def get_friends(token, users_ids):

	print "Start "  + str(os.getppid()) + " " + str(os.getpid())
	
	# create parser for single request
	vk_requests = VkRequests(token, API_VERSION, RANDOM_METHOD_NAMES)

	# constants
	BULK_SIZE = 25 # amount of ids in one code request
	CODE_METHOD_NAME = "friends.get" # method for request in code
	CHANGE_VAR = "user_id" # variable that should differ every request
	METHOD_NAME = "execute"

	print "Total users: {amount}".format(amount=len(users_ids))

	friends_info = []
	failed = 0

	print "Process: " + str(os.getpid()) + " len users_ids: " + str(len(users_ids))

	for i in range(0, len(users_ids)/BULK_SIZE+1):

		# add time lag to avoid bans
		time.sleep(0.33)

		# create request on VkScript language
		ids_bulk = users_ids[i*BULK_SIZE:(i+1)*BULK_SIZE]
		vk_code =  vk_requests.script_request(CODE_METHOD_NAME, CHANGE_VAR, ids_bulk)
		fix_params = "code={code}".format(code=vk_code)

		# send request with vkscript code
		request = vk_requests.single_request(method_name=METHOD_NAME, fix_params=fix_params, token_flag=True)
		response = vk_requests.make_single_request(request)

		print "Process: {proc} Getting users friends:  ({size}/{total})".format(
			proc=str(os.getpid()), size=i*BULK_SIZE, total=len(users_ids))

		# add user_id field to response and count failed items
		j = 0
		for item in response:
			if not isinstance(item, bool):
				item["user_id"] = ids_bulk[j]
				friends_info.append(item)
			else: 
				failed += 1
			j += 1


		# send random request every 3rd request to avoid bans
		if not i % 3:
				vk_requests.make_single_request(fake=True)

	print "Process: {proc} Friends: {friends} Users: {users} Failed: {failed}".format(
		proc=str(os.getpid()), friends=str(len(friends_info)),
		users=len(users_ids), failed=failed)

	# save data to DB
	datawriter = DataWriter(DB_NAME, True)
	datawriter.write_items_db("friends_info", friends_info, create_index=True, index_fields=["user_id"])

	print "End " + " " + str(os.getppid()) + " " + str(os.getpid())

if __name__ == "__main__":

	start = time.time()

	# read all users ids from file
	data_reader = DataReader("./data/"+DIRECTORY+"/users_ids.txt")
	users_ids = data_reader.read_ids()

	# create single process for each token 
	num_processes = len(TOKEN_LIST) 
	bulk = len(users_ids)/num_processes + 1
	process=[]

	for i in range(0, num_processes):
			print i
			p = Process(target=get_friends, args=([TOKEN_LIST[i]],users_ids[i*bulk:(i+1)*bulk],))
			p.start()
			process.append(p)

	for p in process:
			p.join()


	# read ready info from DB
	db_reader = DataReader(DB_NAME, True) 
	friends_info = db_reader.read_items_db("friends_info")


	print "Friends_info: " + str(len(friends_info))

	print "End of program: " + str(time.time()-start)
	print "Length: " + str(len(users_ids))

	# dump data into text file
	data_writer = DataWriter("./data/"+DIRECTORY+"/users_friends_trolo.json")
	data_writer.write_json(friends_info)
