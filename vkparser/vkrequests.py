"""Class for different requests to VK API"""
import re
import requests
import json
import time
from random import randint

class VkRequests:

	def __init__(self, tokens, api_v, random_requests_list):
		"""Save tokens"""

		self.tokens = tokens
		self.api_v = api_v
		self.random_requests_list = random_requests_list

	def get_token(self, token_id = None):
		"""Choose token by id or get random"""

		if token_id:
			token = self.tokens[token_id]
		else:
			token = self.tokens[randint(0, len(self.tokens)-1)]
		return token


	def script_request(self, method_name, change_var, values, count=None, fix_params= {}):
		"""Return dumb request in VKScript format.
		IMPORTANT: Current VK api (5.28) allows max 25 api requests per script, 
		so, length of values should be less than 25.
		For more information visit http://vk.com/dev/execute

		fix_params = dict of fix params. Ex.:  {"fields":["groups", ""]}. Works only with flat dictionaries
		values = list of tuples [(id1, offset1),(id2,offset2)]

		"""

		if isinstance(values[0],int):
			# convert list of int to list of tuples
			values = [(value,0) for value in values]

		i = 0
		final_req = ''
		variables = []

		if count != None:
			fix_params["count"] = count
			

		for value in values:
			variables.append("a" + str(i))

			# add count to fix_params

			# convert dict to str and erase {} 					
			fix_params = re.sub("[\{|\}]","", str(fix_params))
			fix_params = re.sub("[\'|\']",'\"', fix_params)

			# create base query
			query_code = '"{change_var}": {ids_bulk}, "offset": {offset}'.format(
					ids_bulk= value[0], change_var=change_var, offset=value[1])

			# add fix params if present
			if len(fix_params):
				query_code = query_code + "," + fix_params


			part_req = 'var {variable} = API.{method_name}({{{query_code}}});'.format(
				method_name=method_name, variable=variables[i], query_code=query_code)

			final_req+= part_req
			i += 1

		final_req += "return [" + ', '.join(str(p) for p in variables) + "];"

		return final_req

	def mass_request(self, method_name, fix_params, ids, mass_field_name, token_flag=False, token_id=None):
		"""Return request with a lot of ids"""

		req_url = 'https://api.vk.com/method/{method_name}?{parameters}&{mass_field}={ids}&v={api_v}'.format(
			method_name=method_name, api_v=self.api_v, 
			mass_field=mass_field_name, ids=ids, 
			parameters=fix_params)

		req_url	= re.sub('[\[|\]|\s]','', req_url)

		# add token if required 
		if token_flag:
			req_url = '{req}&access_token={access_token}'.format(
				req=req_url, access_token = self.get_token(token_id))

		return req_url


	def single_request(self, method_name, fix_params, token_flag=False, token_id=None):
		"""Return single request"""

		req_url = 'https://api.vk.com/method/{method_name}?{parameters}&v={api_v}'.format(
			method_name=method_name, api_v=self.api_v, 
			parameters=fix_params)

		# add token if required 
		if token_flag:
			req_url = '{req}&access_token={access_token}'.format(
				req=req_url, access_token = self.get_token(token_id))

		return req_url


	def random_request(self):
		"""Return random request from list to avoid bans due series of similar requests"""

		req_url = 'https://api.vk.com/method/{method_name}?{parameters}&v={api_v}'.format(
			method_name=self.random_requests_list[randint(0, len(self.random_requests_list)-1)],
			api_v=self.api_v , parameters='id=1')

		return req_url


	def make_single_request(self, request=None, fake=False):
		"""Make request and process response from VK"""

		# don't parse response for fake requests
		if fake:
			request = self.random_request()
			r = requests.get(request)
			print "Fake request: {req}".format(req=request)
			return 0

		json_result = {}

		try:
			r = requests.get(request)

		except requests.exceptions.RequestException as e:
			print "Error during sending request: {error}".format(error=e)
			print "Response will be empty"
			json_result["response"] = []

		else:
			json_result = json.loads(r.text)
			if "response" not in json_result:
				
				print 'Error during processing response from VK. Error code: {error_code} , '\
				      'error message: {error_msg}'.format(
				      	error_code = json_result["error"]["error_code"],
				      	error_msg =  json_result["error"]["error_msg"])

				print "Response will be empty"
				json_result["response"] = []

		finally:
			if "response" not in json_result:
				print "No response in result: {req} {res}".format(
					req=request, res=json_result)
				return []
			else:
				return json_result["response"]

	def make_offset_request(self,method_name, 
		fix_params, count, bulk_size, 
		token_flag=False, req_freq=0.3, fake_freq=3):
		"""Make request with offset and count"""

		offset = 0
		i = 0
		result = {}

		while (offset < count):

			# add pause not to be banned due to frequency of requests
			time.sleep(req_freq)

			# add precision

			if offset + bulk_size > count:
				bulk_size_local = count - offset
			else:
				bulk_size_local = bulk_size

			var_params = "count={count}&offset={offset}&{fix_params}".format(
				count=bulk_size_local, offset=offset, fix_params=fix_params)

			request = self.single_request(
				method_name=method_name, fix_params=var_params,
				token_flag=token_flag)

			response = self.make_single_request(request)

			if response:
				if not result:
					# initialize result with first response object
					result = response
				else:
					# merge list fields with each other 
					# TODO check for correctness for different API calls, can merge non unique items
					# for fix it ex.: list(set(l1) | set(l2))
					for key in response.keys():
						if isinstance(response[key], list):
							result[key].extend(response[key])

			offset += bulk_size_local
			i += 1

			# make fake requests not to be banned due series of similar requests
			if not i % fake_freq:
				self.make_single_request(fake=True)

		return result

	def make_multioffset_code_request(self, method_name, change_var, values, count, 
    	token, code_bulk=25, fix_params={}):
	    """Make offset requests for big items with VkScript.
	    Input:
	       method_name - invoked method name
	       change_var - name of variable corresponded to ids in values
	       values - list of tuples [(item_id, items_count)]
	       count - max items per request
	       code_bulk - max requests in code
	       fix_params - dictionary with additional params for requests. 
	    """

	    if isinstance(values[0],int):
			# convert list of int to list of tuples
			values = [(value,0) for value in values]

	    # expand list to offsets parts
	    expanded_list = []
	    for item in values:
	    	for i in range(0,item[1]/count+1):

	    		# (id,offset) list
	    		expanded_list.append((item[0], count*i))

	    # empty dictionary for accumulating result
	    result = {}
	    for item in values:
	    	result[item[0]] = []

	    for i in range(0, len(expanded_list)/code_bulk+1):

	    	time.sleep(0.33)

	    	requests_bulk = expanded_list[code_bulk*i:code_bulk*(i+1)]
	    	
	    	# if len(list) mod code_bulk == 0 -> return
	    	if len(requests_bulk)==0:
	    		continue
	    	
	    	j = 0

	    	#create vkscript code
	    	final_req = self.script_request(method_name, change_var, requests_bulk, count, fix_params)

	    	# make code request
	    	fix_params_code = "code={code}".format(code=final_req)
	    	request = self.single_request(method_name="execute", fix_params=fix_params_code, token_flag=True)
	    	response = self.make_single_request(request)

	    	# aggregate in dictionary
	    	for j in range(0,len(response)):
	    		if not isinstance(response[j], bool):
	    			result[requests_bulk[j][0]].extend(response[j]["items"])

	    	if not i % 3:
	    		self.make_single_request(fake=True)

	    # return dictionary {id:[items]}
	    return result
