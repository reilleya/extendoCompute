import sys, os, threading, time, connectionThread, pickle
from multiprocessing.connection import Listener, Client
import random

class threadManager():
	def __init__(self, config):
		self.config = config
	
		self.activeThreads = {}
		self.nextConnID = 0
		
		self.exiting = False
		self.running = False
		
		self.log = []
		
		self.logEvent(" Thread Manager starting")
		
		self.prog = ""
		self.progName = ""
		
		self.iterations = 1
		self.inputs = {}
		self.tasks = []
		
		self.batchSize = 1
		self.batches = []
		self.batchStates = []
		
		self.startTime = 0
		self.results = []
		
		self.listener = Listener((self.config.bindIP, self.config.listenPort), authkey="password")
		self.listenThread = threading.Thread(target=self.listen, args=())
		self.listenThread.start()
		
		self.updateThread = threading.Thread(target=self.update)
		self.updateThread.start()
		self.logEvent(" Thread Manager started")
	
	def update(self):
		while not self.exiting:
			if self.running:
				for ctn in range(0, len(self.activeThreads)): #self.activeThreads is a dict... not a list. Why not loop over the keys?
					if self.activeThreads[ctn].state == "idle":
						#self.logEvent(" "+str(ctn)+" is idle!")
						for bsn in range(0, len(self.batchStates)):
							if self.batchStates[bsn][0] == "waiting":
								self.batchStates[bsn] = ["calc", ctn]
								self.activeThreads[ctn].assignTasks(bsn, self.batches[bsn])
								self.activeThreads[ctn].run()
								break
					
					if self.activeThreads[ctn].state == "connerror":
						self.logEvent(" Thread "+str(ctn)+" is reporting connection problems, reallocating tasks")
						for bsn in range(0, len(self.batchStates)):
							if self.batchStates[bsn][0] == "calc" and self.batchStates[bsn][1] == ctn:
								self.logEvent(" Reallocating batch "+str(bsn))
								self.batchStates[bsn] = ["waiting"]
				
				if len(self.results) == len(self.tasks):
					self.logEvent(" All results received, done running after "+str(time.time()-self.startTime)+" seconds")
					self.calcShareStats()
					self.running = False
	
	def calcShareStats(self):
		workDone = {}
		tasksDone = 0
		for bsn in range(0, len(self.batchStates)):
			if self.batchStates[bsn][0] == "complete":
				if self.batchStates[bsn][1] not in workDone:
					workDone[self.batchStates[bsn][1]] = 0
				workDone[self.batchStates[bsn][1]]+=len(self.batches[bsn])
				tasksDone += len(self.batches[bsn])
		outputMess = "Workshares: "
		for threadID in workDone:
			outputMess += "#"+str(threadID)+": "+str(workDone[threadID])+"/"+str(tasksDone)+"("+str(100*float(workDone[threadID])/tasksDone)[:5]+"%), "
		self.logEvent(outputMess[:-2])
	
	def listen(self):
		while not self.exiting: 
			self.logEvent("[Listener] Waiting")
			conn = self.listener.accept()
			if not self.exiting:
				self.logEvent("[Listener] Receiving connection from "+self.listener.last_accepted[0])
				threadID = conn.recv()
				if threadID == -1:
					self.activeThreads[self.nextConnID]=connectionThread.connectionThread(self, self.nextConnID, conn)
					self.nextConnID+=1
				else:
					if threadID in self.activeThreads:
						self.activeThreads[threadID].reconnect(conn)
					else:
						conn.send(["exit", "client failed to reconnect in time"]) #BAD WORKAROUND
			
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
		if not self.running:
			self.logEvent(" Instructing all clients to run assigned program")
			self.batchStates = []
			for b in self.batches:
				self.batchStates.append(["waiting"])
			self.running = True
			self.startTime = time.time()
		else:
			self.logEvent(" Already running")
			#for k,thd in self.activeThreads.items():
			#	tempTasks = []
			#	for i in range(0, self.iterations):
			#		tempTasks.append({"in":random.randint(1,50)})
			#	thd.assignTasks(tempTasks)
			#	thd.run()
	
	def exit(self):
		self.exiting = True
		print "\tClosing all client threads..."
		for k,thd in self.activeThreads.items():
			thd.exit()
		print "\tDone."
		print "\tClosing listener..."
		conn = Client((self.config.bindIP,self.config.listenPort), authkey="password") #This allows 'accept' to happen and the listen thread to be done
		print "\tDone."
		
	def distribNewProgram(self, name, prog):
		self.prog = prog
		self.progName = name
		self.logEvent(" Setting all clients to program "+name+ " of length " + str(len(prog)))
		for k,thd in self.activeThreads.items():
			thd.newProgram(name, prog)
			
	def reportResults(self, results, threadID):
		#testmess = str(len(self.results))+"->"
		self.results += results
		#testmess += str(len(self.results))
		#self.logEvent(testmess)
		for bsn in range(0, len(self.batches)):
			if self.batchStates[bsn][0] == "calc" and self.batchStates[bsn][1] == threadID:
				self.batchStates[bsn][0] = "complete"
		
	def setIterations(self, iters):#make a general function for this sort of thing!
		self.iterations = iters
		
	def saveResults(self, location):
		f = open(location, "w")
		pickle.dump(self.results, f)
		f.close()
		
	def setBatchSize(self, batchsize):
		self.batchSize = batchsize
		
	def addInput(self, name, values):
		self.logEvent(" Added or changed input '"+name+"' to have "+str(len(values))+" different value(s)")
		self.inputs[name] = values
		
	def deleteInput(self, name):
		if name in self.inputs:
			self.logEvent(" Deleting input '"+name+"'")
			del self.inputs[name]
		else:
			self.logEvent(" No input called "+name)
			
	def generateTasks(self):
		self.tasks=[]
		if len(self.inputs) == 1: #We can skip all of the messiness that lies ahead if we only have one input
			for v in self.inputs[self.inputs.keys()[0]]:
				self.tasks.append({self.inputs.keys()[0]:v})
			
		else:
			counts = {}
			order = []
			for i in self.inputs:
				counts[i] = 0
				order.append(i)
			ntasks = 1
			for name,values in self.inputs.items():
				ntasks *= len(values)
			for it in range(0, ntasks):
				self.tasks.append({})
				for name,values in self.inputs.items():
					self.tasks[-1][name] = self.inputs[name][counts[name]]
				counts[order[0]]+=1
				for i in range(0, len(self.inputs)):
					for n,c in counts.items():
						if c == len(self.inputs[n]):
							if order.index(n)+1 != len(order):
								counts[order[order.index(n)+1]]+=1
							counts[n] = 0
			iterTasks = []
			for t in self.tasks:
				for i in range(0, self.iterations):
					iterTasks.append(t)
			self.tasks = iterTasks
		self.logEvent(" Generated "+str(len(self.tasks))+" tasks")
		
	def generateBatches(self):
		self.batches = []
		
		if len(self.tasks) < self.batchSize*len(self.activeThreads):
			self.logEvent(" Batch size too large for all connections to get a task")
			self.batchSize = int(len(self.tasks)/len(self.activeThreads))
			if self.batchSize == 0:
				self.batchSize = 1
				self.logEvent(" More connections than tasks, setting batch size to 1")
			else:
				self.logEvent(" Automatically setting batch size to "+str(self.batchSize)+" to balance load")

		nbatches = int(len(self.tasks)/float(self.batchSize))
		self.logEvent(" Dividing up "+str(nbatches+(nbatches*self.batchSize<len(self.tasks)))+" batches for calculation")
		for b in range(0, nbatches):
			self.batches.append(self.tasks[b*self.batchSize:(b+1)*self.batchSize])
		if nbatches*self.batchSize<len(self.tasks):
			self.batches.append(self.tasks[nbatches*self.batchSize:])
			
	#def reportDisconnect(self):
	#	
			
	def reset(self, components):
		self.logEvent(" Resetting "+str(components)[1:-1].replace("'", ""))
		if "all" in components:
			self.prog = ""
			self.progName = ""
			self.iterations = 1
			self.inputs = {}
			self.tasks = []
			self.batchSize = 1
			self.batches = []
			self.batchStates = []
			self.startTime = 0
			self.results = []
			
		if "results" in components:
			self.results = []
			
		if "program" in components:
			self.prog = ""
			self.progName = ""
		
		if "tasks" in components:
			self.tasks = []
		
		if "inputs" in components:
			self.inputs = {}
		
		if "batches" in components:
			self.batches = []
			self.batchStates = []
			
	def pause(self):
		self.running = False
		for key in self.activeThreads:
			self.activeThreads[key].pause()
		
	def resume(self):
		self.running = True
		for key in self.activeThreads:
			self.activeThreads[key].resume()
			
	def cancel(self):
		self.running = False
		for key in self.activeThreads:
			self.activeThreads[key].cancel()