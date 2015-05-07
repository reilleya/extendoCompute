import os, sys, pickle
from multiprocessing.connection import Client

ip = raw_input("IP>")
if ip=="":
	ip = "192.168.3.162"

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
		conn.send(["results"])
		if i[4] == "s":
			if i[6] == "l":
				res = conn.recv()
				f = open(i[8:], "w")
				pickle.dump(res, f)
				f.close()
				print "Wrote results to "+i[8:]
			if i[6] == "r":
				conn.send(["saveresults", i[8:]])
				print "Saving results to "+ i[8:]+" on the server"
		if i[4] == "d":
			res = conn.recv()
			print res
		
	if i[0:5] == "iters":
		conn.send(["iterations", int(i.split(" ")[1])])
		print "Set iteration count to "+i.split(" ")[1]
	
	i = raw_input(">")
	
conn.send(["close"])