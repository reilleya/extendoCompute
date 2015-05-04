import sys, os, threading, time
from multiprocessing.connection import Listener

class connectionThread():
	def __init__(self, threadMan, ID, connection):
		self.threadMan = threadMan
		self.address = self.threadMan.listener.last_accepted
		self.threadID = ID
		self.programName = None
		self.state = "idle"
		self.conn = connection
		self.exiting = False
		self.thread = threading.Thread(target=self.handleClient, args=())
		self.thread.start()
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Thread started")
		
	def handleClient(self):
		while not self.exiting:
			try:
				d = self.conn.recv()
			except:
				if not self.exiting:
					self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Connection receive error!")
					self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Closing")
					self.exiting = True
					self.threadMan.deleteThread(self.threadID)
				break
			if d[0] == "close":
				self.exit()
			
		self.conn.close()
				
	def generateStatusString(self):
		ss = "#"+str(self.threadID)+": Addr="+self.address[0]+", Prog="+str(self.programName)+","
		if self.state == "idle":
			ss += " Idle"
		if self.state == "running":
			ss += "Running, iteration"
		if self.state == "done":
			ss += "Done"
		return ss
	
	def exit(self):
		self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Closing")
		self.exiting = True
		self.conn.send(["exit"])
		self.conn.close()
		self.threadMan.deleteThread(self.threadID)
		
	def newProgram(self, name, prog):
		self.programName = name
		self.conn.send(["program", name, prog])
		
	def run(self):
		if self.programName != None:
			self.conn.send(["run"])
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] Program started")
		else:
			self.threadMan.logEvent("[Connection"+str(self.threadID)+"] No program to start")
			
	def assignTasks(self, tasks):
		self.conn.send(["tasks", tasks, "r"])