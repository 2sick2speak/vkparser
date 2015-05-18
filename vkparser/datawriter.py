"""Class for different ways of data output"""
import pymongo 
import json

class DataWriter:

	def __init__(self, name, db_source = False):
		"""Init output file according db_source flag"""

		if not db_source:
			self.filename = name
		else:
			self.connection = pymongo.MongoClient()
			try:
				self.db = self.connection[name]
			except pymongo.errors.ConnectionFailure:
				print "Connection error to {database}".format(database=name)

	def write_json(self, data):
		"""Write json dump to file"""

		try:
			f = open(self.filename, "w")
		except Exception as e:
			print "Error while opening a file: {filename}. Clue: {msg}".format(
				filename=self.filename, msg = e)

		else:
			json.dump(data, f)
			f.close()

	def write_ids(self, ids):
		"""Write ids into file"""

		try:
			f = open(self.filename, "w")
		except Exception as e:
			print "Error while opening a file: {filename}. Clue: {msg}".format(
				filename=self.filename, msg = e)

		else:
			for item in ids:
				f.write("%s\n" % item)
			f.close()

	def write_items_db(self, table_name, items, create_index=False, index_fields=None, field_name='user_id'):
		"""Write items into db"""

		table_db = self.db[table_name]

		# create index
		if create_index:
			index = []
			for field in index_fields:
				tuple_field = (field, pymongo.ASCENDING)
				index.append(tuple_field)

			table_db.ensure_index(index, unique = True)

		error_counter = 0

		for item in items:

			# convert item to dictionary if it's not. Set it's key name as field_name
			if not isinstance(item, dict):
				dict_item = {}
				dict_item[field_name] = item
				item = dict_item

			try:
				table_db.insert(item, manipulate=False, continue_on_error=True)
			except pymongo.errors.OperationFailure as e:
				error_counter += 1
				#print "Insert error to db: {err}".format(err=e)

		if error_counter:
			print "Insert errors: {count}".format(count=error_counter)





