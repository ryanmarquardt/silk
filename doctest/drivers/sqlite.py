
from runsuite import *

class DriverTestSqlite(DriverTestBase):
	def test_invalid_path(self):
		with self.assertRaises(IOError):
			self.connect(path = 'path/to/false/database.sqlite')

if __name__=='__main__':
	main('sqlite')
