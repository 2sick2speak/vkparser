 # -*- coding: utf-8 -*-
import re
import time

from vkparser.vkrequests import VkRequests
from vkparser.datareader import DataReader
from vkparser.datawriter import DataWriter
from settings import TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES, DIRECTORY

if __name__ == "__main__":

	# read json with public names
	data_reader = DataReader("./data/"+ DIRECTORY +"/publics.json")
	publics = data_reader.read_json()

	# create parser for single request
	vk_requests = VkRequests(TOKEN_LIST, API_VERSION, RANDOM_METHOD_NAMES)

	# static fields for request
	fields = "description,members_count"
	method_name = "groups.getById"

	# save additional info about publics
	publics_info = []

	# get additional info about publics
	for public in publics:

		# make list of public names and add to request params
		public["names"] = map(lambda x: str(x).encode('ascii','ignore'), public["names"])
		ids = re.sub("[\[|\]|\s|\'']", "", str(public["names"]))
		fix_params = "group_ids={ids}&fields={fields}".format(
			ids=ids, fields=fields)

		print "Getting publics info: {names}".format(names = ids)

		request = vk_requests.single_request(method_name=method_name, fix_params=fix_params, token_flag=True)
		response = vk_requests.make_single_request(request)

		if response:
			publics_info.extend(response)


	print len(publics_info)

	# constants for requests

	bulk_size = 1000
	method_name = "groups.getMembers"
	publics_users = []
	users_ids = []

	for public in publics_info:

		# add time lag to avoid bans
		time.sleep(0.5)

		offset = 0
		if 'members_count' in public:
			members_count = public["members_count"]
		else:
			print "Public problems: {id}".format(id=str(public))
			print public.keys()
			continue
		print public

		fix_params = "group_id={group_id}".format(group_id=public["id"])

		# make offset request to get all users

		result = vk_requests.make_offset_request(method_name, fix_params, members_count, bulk_size, True)
		print "Getting users ids: {count}/{from_req}".format(
			count=members_count, from_req=len(result["items"]))

		print len(result["items"])	
		publics_users.append({"public_id":public["id"], "items": result["items"]})
		users_ids.extend(result["items"])

	print len(publics_users)

	# dump data with users list
	data_writer = DataWriter("./data/"+ DIRECTORY +"/public_users_list.json")
	data_writer.write_json(publics_users)


	print len(users_ids)

	# dump data with all users
	data_writer = DataWriter("./data/"+ DIRECTORY +"/users_ids.txt")
	data_writer.write_ids(list(set(users_ids)))
