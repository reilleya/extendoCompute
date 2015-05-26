from multiprocessing.connection import Client
import threading, time
	
def statusThread():
	global state, ctask
	while running:
		conn.send(["state", state, ctask, len(tasks)])
		time.sleep(0.1)
	
def runProg():
	global state, ctask, results
	while running:
		if state == "running":
			for task in tasks: #will this be OK if more tasks are added mid-loop?
				print "Running task "+str(ctask+1)+"/"+str(ntasks)
				print "\t Task inputs: "+str(task)
				exec prog
				results.append([task, result])
				ctask+=1
		
			state = "idle"
			print "All done with tasks"
			ctask = 0
			#print "Results: "+str(results)
			conn.send(["results", results])
			results = []
			
ip = raw_input("IP>")
if ip=="":
	ip = "192.168.3.162"
		
running = True
conn = Client((ip,2424), authkey="password")
conn.send(-1)
handshake = conn.recv()

threadID = handshake[]
state = "idle"

progname = ""
prog = ""

ntasks = 0
ctask = 1
tasks = []
cres = None
results = []

threading.Thread(target = runProg).start()
threading.Thread(target = statusThread).start()

while running:
	try:
		d = conn.recv()

	except:
		if running:
			print "Connection error! Retrying..." 
			conn = Client((ip,2424), authkey="password")
			conn.send(threadID)
			handshake = conn.recv()

			print "Connection regained!"
			continue
		
	if d[0] == "exit":
		print "Exiting, because "+d[1]
		running = False
		
	if d[0] == "program":
		print "Received a new program ("+d[1]+")"
		progname = d[1]
		prog = d[2]
		
	if d[0] == "tasks":
		print "Received "+str(len(d[1]))+" new tasks, "+("appending to list of tasks"*(d[2]=="a"))+("replacing current list of tasks"*(d[2]=="r"))
		if d[2] == "a":
			tasks+=d[1]
		if d[2] == "r":
			tasks=d[1] #Probably need to alert the other thread about this somehow
		ntasks = len(tasks)
		
	if d[0] == "run":
		print "Setting state to run"
		state = "running"