import re
import time

from vkparser.vkrequests import VkRequests
from vkparser.datareader import DataReader
from vkparser.datawriter import DataWriter
from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DIRECTORY

if __name__ == "__main__":

	# read users ids
	data_reader = DataReader("./data/" + DIRECTORY + "/users_ids.txt")
	users_ids = data_reader.read_ids()

	# create parser for single request
	vk_requests = VkRequests(TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES)


	# save info about users
	users_info = []
	METHOD_NAME = "users.get"
	FIX_PARAMS = 'fields=bdate,home_town,country,universities,last_seen,sex,'\
	'city,personal,interests,activities,occupation,relation,music,about,quotes,'\
	'domain,has_mobile,contacts,site,education,schools,relatives,connections,movies,tv,books'
	MASS_FIELD_NAME = "user_ids"

	# amount of user ids in one request
	bulk_size = 250

	for i in range(0, len(users_ids)/bulk_size+1):

		# add time lag to avoid bans
		time.sleep(0.33)

		# get bulk of user ids
		ids_bulk = users_ids[bulk_size*i : bulk_size*(i+1)]

		# create mass request for a lot of ids
		req_url = vk_requests.mass_request(METHOD_NAME, FIX_PARAMS, ids_bulk, MASS_FIELD_NAME, True)
		result = vk_requests.make_single_request(req_url)

		users_info.extend(result)

		print "Getting users info. Ready: ({ready}/{total})".format(ready=len(users_info), total=len(users_ids))
		
		# send random request every 3rd request to avoid bans
		if not i % 3:
			vk_requests.make_single_request(fake=True)

	print len(users_info), len(users_ids)

	# dump data into text file
	data_writer = DataWriter("./data/" + DIRECTORY + "/users_info.txt")
	data_writer.write_json(users_info)