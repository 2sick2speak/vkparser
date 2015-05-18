"""Class for different input data"""
import pymongo
import json

class DataReader:

	def __init__(self, name, db_source = False):
		"""Init inpur source according db_source flag"""

		if not db_source:
			self.filename = name
		else:
			self.connection = pymongo.MongoClient()
			try:
				self.db = self.connection[name]
			except pymongo.errors.ConnectionFailure:
				print "Connection error to {database}".format(database=name)

	def read_json(self):
		"""Read json source"""
		try:
			f = open(self.filename, "r")
		except Exception as e:
			print "Error while reading a file: {filename}. Clue: {msg}".format(
				filename=self.filename, msg = e)
			return []
		else:
			result = json.load(f)
			f.close()

			# return json
			return result

	def read_ids(self):
		"""Read ids source file"""

		try:
			f = open(self.filename, "r")
		except Exception as e:
			print "Error while reading a file: {filename}. Clue: {msg}".format(
				filename=self.filename, msg = e)
			return []
		else:
			ids = f.readlines()
			ids = [int(val) for val in ids]
			
			# return list of ids
			return ids

	def read_items_db(self, table_name, fields=[]):
		"""Read items from db"""

		table_db = self.db[table_name]

		fields_query = {"_id": 0}
		for field in fields:
			fields_query[field] = 1

		result = list(table_db.find({}, fields_query))

		return result





