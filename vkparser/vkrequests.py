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


	def script_request(self, method_name, change_var, values, fix_params=None):
		"""Return dumb request in VKScript format.
		IMPORTANT: Current VK api (5.28) allows max 25 api requests per script, 
		so, length of values should be less than 25.
		For more information visit http://vk.com/dev/execute"""

		i = 0
		final_req = ''
		variables = []

		for value in values:
			variables.append("a" + str(i))
			part_req = 'var {variable} = API.{method_name}({{{change_var}: {ids_bulk}}});'.format(
				method_name=method_name, variable = variables[i],
				ids_bulk= value, change_var=change_var)
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
