
from runsuite import *

class DriverTestMysql(DriverTestBase):
	def test_invalid_db(self):
		with self.assertRaises((AuthenticationError, IOError)):
			self.connect(database = self.options['_database'])

	def test_invalid_user(self):
		with self.assertRaises(AuthenticationError):
			self.connect(user = self.options['_user'])

	def test_invalid_password(self):
		with self.assertRaises(AuthenticationError):
			self.connect(password = self.options['password'] + ' ')

if __name__=='__main__':
	main('mysql')
