import sys, os, threading, time, connectionThread
from multiprocessing.connection import Listener, Client
import random

bindIP = "192.168.3.162"

class threadManager():
	def __init__(self):
		self.activeThreads = {}
		self.nextConnID = 0
		
		self.exiting = False
		
		self.log = []
		
		self.iterations = 0
		self.results = []
		
		self.listener = Listener((bindIP, 2424), authkey="password")
		self.listenThread = threading.Thread(target=self.listen, args=())
		self.listenThread.start()
	
	def update(self):
		pass
		
	def listen(self):
		while not self.exiting: 
			self.logEvent("[Listener] Waiting")
			conn = self.listener.accept()
			if not self.exiting:
				self.logEvent("[Listener] Receiving connection from "+self.listener.last_accepted[0])
				self.activeThreads[self.nextConnID]=connectionThread.connectionThread(self, self.nextConnID, conn)
				self.nextConnID+=1
			
	def endThread(self, threadID):
		self.logEvent(" Ending thread #"+str(threadID))
		self.activeThreads[threadID].exit()
		self.deleteThread(threadID)
	
	def deleteThread(self, threadID):
		if threadID in self.activeThreads:
			del self.activeThreads[threadID]
		else:
			print "Attempted to delete non-existent thread"
				
	def logEvent(self, event):
		self.log.append("["+time.strftime("%c")+"]"+str(event))
	
	def run(self):
		self.logEvent(" Instructing all clients to run assigned program")
		for k,thd in self.activeThreads.items():
			tempTasks = []
			for i in range(0, self.iterations):
				tempTasks.append([random.randint(1,50)])
			thd.assignTasks(tempTasks)
			thd.run()
	
	def exit(self):
		self.exiting = True
		print "\tClosing all client threads..."
		for k,thd in self.activeThreads.items():
			thd.exit()
		print "\tDone."
		print "\tClosing listener..."
		conn = Client((bindIP,2424), authkey="password") #This allows 'accept' to happen and the listen thread to be done
		print "\tDone."
		
	def distribNewProgram(self, name, prog):
		self.logEvent(" Setting all clients to program "+name+ " of length " + str(len(prog)))
		for k,thd in self.activeThreads.items():
			thd.newProgram(name, prog)
			
	def reportResults(self, results):
		self.results += results
		
	def setIterations(self, iters):#make a general function for this sort of thing!
		self.iterations = iters