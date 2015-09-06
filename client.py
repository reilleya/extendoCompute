from multiprocessing.connection import Client
import threading, time, useful, os, sys
	
sys.stderr = open('clientErrors.txt','w')
	
def logEvent(event):
	global log
	log.append("["+time.strftime("%c")+"] "+str(event))
	
def statusThread():
	global state, ctask
	while running:
		conn.send(["state", state, ctask, len(tasks)])
		time.sleep(0.1)
		
def outputThread():
	while running:
		if connected:
			buff = ("="*46)+"extendoCompute->Client"+("="*46)+"\n"
			buff += ("="*114)+"\n"
			buff += "Recent Events:\n"
			for i in range(-1, -useful.clamp(16, 0, len(log))+1, -1):
				buff += "\t"+log[i]+"\n"
			for i in range(0, 16-len(log)):
				buff += "\t-"+"\n"
			buff += ("-"*114)+"\n"
			buff += "Connection Info:\n"
			if connected:
				buff += "\tConnected to "+str(ip)+"\n"
			else:
				buff += "\tConnection error!\n"
			buff += ("-"*114)+"\n"
			buff += "Progress:\n"
			if state == "running":
				buff += "\tRunning program: "+progname+"\n"
				buff += "\tTask:\n"
				buff += "\t\t"+useful.progressBar(ctask, ntasks, 90)+"\n\t\tTask: "+str(ctask)+"/"+str(ntasks)+"\n"
				#buff += "\t\tCurrent: "+str(tasks[ctask])+"\n"
			else:
				buff += "Idle"+"\n"
			buff += ("="*114)+"\n"
			buff += ("="*114)+"\n"
			os.system("cls")
			print buff
			time.sleep(0.1)
	
def runProg():
	global state, ctask, results, log
	while running:
		if state == "running":
			for task in tasks: #will this be OK if more tasks are added mid-loop?
				#print "Running task "+str(ctask+1)+"/"+str(ntasks)
				#print "\t Task inputs: "+str(task)
				exec prog
				results.append([task, result])
				ctask+=1
				if len(results)%100 == 0: #make this configurable?
					logEvent("Sending a batch of 100 results")
					conn.send(["results", results[-100:]])
					logEvent("Sent!")
					
			state = "idle"
			ctask = 0
			if len(tasks)%100!=0:
				logEvent("All tasks complete, sending final results...")
				conn.send(["results", results[-(len(results)%100):]])
				logEvent("Sent a batch of "+str(len(results[-(len(results)%100):]))+" results")
				results = []
			
			#print "Results: "+str(results)
			
log = []
			
ip = raw_input("IP>")
if ip=="":
	ip = "192.168.1.148"
		
running = True
conn = Client((ip,2424), authkey="password")
conn.send(-1)
handshake = conn.recv()

threadID = handshake["threadID"]
state = "idle"

progname = ""
prog = ""

ntasks = 0
ctask = 1
tasks = []
cres = None
results = []
connected = True
paused = False

threading.Thread(target = runProg).start()
threading.Thread(target = statusThread).start()
threading.Thread(target = outputThread).start()

while running:
	try:
		d = conn.recv()

	except:
		if running:
			logEvent("Connection error! Retrying...") 
			conn = Client((ip,2424), authkey="password")
			conn.send(threadID)
			handshake = conn.recv()
			logEvent("Connection regained!")
			continue
		
	if d[0] == "exit":
		logEvent("Exiting, because "+d[1])
		running = False
		
	if d[0] == "program":
		logEvent("Received a new program ("+d[1]+")")
		progname = d[1]
		prog = d[2]
		
	if d[0] == "tasks":
		logEvent("Received "+str(len(d[1]))+" new tasks, "+("appending to list of tasks"*(d[2]=="a"))+("replacing current list of tasks"*(d[2]=="r")))
		if d[2] == "a":
			tasks+=d[1]
		if d[2] == "r":
			tasks=d[1] #Probably need to alert the other thread about this somehow
		ntasks = len(tasks)
		
	if d[0] == "run":
		logEvent("Setting state to run")
		state = "running"
		
	if d[0] == "pause":
		state = "paused"
		
	if d[0] == "resume":
		if state == "paused":
			state = "running"
			
	if d[0] == "cancel":
		if state == "running":
			state = "idle"
			ntasks = 0
			ctask = 1
			tasks = []
			cres = None
			results = []
			