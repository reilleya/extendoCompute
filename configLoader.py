class cfgLoader(object):
	def __init__(self, filename="config.cfg"):
		self.filename = filename
		self.settings = {}
		#self.loadSettings()
		
	def loadSettings(self):
		f = open(self.filename, "r")
		contents = f.read()
		f.close()
		lines = contents.split("\n")
		for line in lines:
			parts = line.split(" ")
			name = parts[0]
	
	def __getattribute__(self, key):
		if key == "settings":
			return object.__getattribute__(self, key)
		else:
			if key in self.settings:
				return self.settings[key]
			else:
				raise Exception("Tried to access "+key+", a setting that does not exist!")