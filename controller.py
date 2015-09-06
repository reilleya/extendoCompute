import os, sys, pickle
from multiprocessing.connection import Client

ip = raw_input("IP>")
if ip=="":
	ip = "192.168.1.148"

conn = Client((ip,7777), authkey="password")

i = raw_input(">")

while i!="exit":
	if i=="stop":
		conn.send(["stop"])
		print "Shutting extendoCompute down"
		sys.exit()
		
	if i=="info":
		conn.send(["info"])
		d = conn.recv()
		print "Recent Events:"
		events = d[1][-10:]
		events.reverse()
		while len(events)<10:
			events.append("-")
		for event in events:
			print "\t"+event
		print ("-"*94)
		print str(len(d[0]))+" active connection"+("s"*(len(d[0])!=1))+(":"*(len(d[0])!=0))
		for ct in d[0]:
			print "\t"+ct
			
	if i[0:4] == "prog":
		loc = i.split(" ")[1]
		n = loc.split("/")[-1]
		f = open(loc, "r")
		c = f.read()
		conn.send(["program", n,c])
		
	if i[0:3] == "run":
		conn.send(["run"])
		
	if i[0:4] == "disc":
		conn.send(["disc", int(i.split(" ")[1])])
		res = conn.recv()
		if res == -1:
			print "Attempted to close a non-existent connection"
		else:
			print "Closed connection #"+str(res)
	
	if i[0:3] == "res":
		if i[4] == "s":
			if i[6] == "l":
				conn.send(["results"])
				res = conn.recv()
				f = open(i[8:], "w")
				pickle.dump(res, f)
				f.close()
				print "Wrote results to "+i[8:]
			if i[6] == "r":
				conn.send(["saveresults", i[8:]])
				print "Saving results to "+ i[8:]+" on the server"
		if i[4] == "d":
			conn.send(["results"])
			res = conn.recv()
			print res
		
	if i[0:5] == "iters":
		conn.send(["iterations", int(i.split(" ")[1])])
		print "Set iteration count to "+i.split(" ")[1]
	
	if i[0:9] == "batchSize":
		conn.send(["batchsize", int(i.split(" ")[1])])
		print "Set batch size to "+i.split(" ")[1]
		
	if i[0:8] == "newInput":
		args = i[9:]
		name = args[:args.index(" ")]
		rawvalues = args[args.index(" ")+1:]
		values = []
		if rawvalues[0] == "[":
			vals = rawvalues[1:-1].split(",")
			for val in vals:
				try:
					values.append([float(val)])
				except:
					if "-" in val:
						parts = val.split("-")
						try:
							start = int(parts[0])
							end = int(parts[1])
							values += range(start, end+1)
						except:
							values.append([val])
					else:
						values.append([val])
		elif rawvalues[0] == '"' or rawvalues[0] == "'":
			exec "values = "+rawvalues[1:-1]
		else:
			try:
				values = [float(rawvalues)]
			except:
				values = [rawvalues]
		conn.send(["newInput", name, values])
		
	if i[0:8] == "delInput":
		name = i[9:]
		conn.send(["delInput", name])
		
	if i[0:6] == "inputs":
		conn.send(["inputs"])
		res = conn.recv()
		print "Active inputs:"
		for name,values in res.items():
			print "\t"+name+": "+str(values)
			
	if i[0:8] == "genTasks":
		conn.send(["genTasks"])
		ntasks = conn.recv()
		print "Generated "+str(ntasks)+" tasks."
		
	if i[0:10] == "genBatches":
		conn.send(["genBatches"])
		nbatches = conn.recv()
		print "Generated "+str(nbatches)+" batches."
	
	if i[0:7] == "batches":
		conn.send(["batches"])
		batches = conn.recv()
		print len(batches)
		for bnum in range(0,len(batches)):
			print "Batch #"+str(bnum+1)+":"
			while len(batches[bnum])>0:
				for t in batches[bnum]:
					print "\t"+str(t)+"x"+str(batches[bnum].count(t))
					while t in batches[bnum]:
						batches[bnum].remove(t)
	
	if i[0:3] == "log":
		conn.send(["info"])
		d = conn.recv()
		events = d[1][-(int(i[4:])):]
		events.reverse()
		for event in events:
			print event
	
	if i[0:11] == "batchStatus":
		conn.send(["batchStatus"])
		b = conn.recv()
		print b
		
	if i[0:5] == "reset":
		toreset = i.split(" ")[1:]
		conn.send(["reset"]+toreset)
	
	if i[0:5] == "pause":
		conn.send(["pause"])
	
	if i[0:6] == "resume":
		conn.send(["resume"])
	
	if i[0:6] == "cancel":
		conn.send(["cancel"])
	
	#TODO: Tasks command			

	i = raw_input(">")
	
conn.send(["close"])