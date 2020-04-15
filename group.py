
try:
	from general import *
except:
	raise ImportError("Unable to import necessary Modules, Please contact al202t@att.com")
# ----------------------------------------------------------------------------------------
def ipObjContainers(objgrps, col, dic={}, counter=0):
	"""creates dictionary for -->  col: object group details for IP Network objects
	"""
	found = False
	c = 0
	for grpName, grpValues in objgrps.items():
		if grpValues['object_type'] != 'network-object': continue
		checkins = ('host_candidate', 'prefix_candidate')
		for checkin in checkins:
			if grpValues.dic.get(checkin):
				if set(col) == grpValues.dic[checkin]:
					if not dic.get(tuple(col)):
						dic[tuple(col)] = []
					if isinstance(dic[tuple(col)], str): 
						continue
					if not {'ogname': grpName, 'isExact': True} in dic[tuple(col)]:
						dic[tuple(col)].append({'ogname': grpName, 'isExact': True})
					found = True
				else:
					colset = set(col)
					hostset = grpValues[checkin]
					if colset.issubset(hostset):
						if not dic.get(tuple(col)):
							dic[tuple(col)] = []
						if isinstance(dic[tuple(col)], str): 
							continue
						if not {'ogname': grpName, 'isExact': False} in dic[tuple(col)]:
							dic[tuple(col)].append({'ogname': grpName, 'isExact': False})
						found = True
	if not found:
		if not dic.get(tuple(col)):
			counter += 1
			dic[tuple(col)] = 'NEWGRP_'+str(counter)

	return dic, counter

# ----------------------------------------------------------------------------------------
def portObjContainers(objgrps, col, dic={}, counter=0, fc=None):
	"""creates dictionary for -->  col: object group details for Port objects
	"""
	# fc = col
	found = False
	for grpName, grpValues in objgrps.items():
		if grpValues['object_type'] != 'port-object': continue
		found = False
		if True: # condition to be add for mathing items/excluding items - tbd
			if col == grpValues.dic:
				if not dic.get(fc):
					dic[fc] = []
				if not {'ogname': grpName, 'isExact': True} == dic[fc]:
					dic[fc].append({'ogname': grpName, 'isExact': True})
				found = True
			else:
				try:
					colset = set(col)
					hostset = grpValues.dic
				except:
					continue
				# print(colset, hostset)
				if colset.issubset(hostset):
					if not dic.get(fc):
						dic[fc] = []
					if not {'ogname': grpName, 'isExact': False} in dic[fc]:
						dic[fc].append({'ogname': grpName, 'isExact': False})
					found = True
	if not found:
		if not dic.get(fc):
			counter += 1
			dic[fc] = 'NEWGRP_'+str(counter)

	return dic, counter


# ----------------------------------------------------------------------------------------
def disact_port(l):    # duplicate better func available **appp(row, port_line) to be edit later
	"""Post mortem on port number cell """
	ppp = []
	orgl = l
	l = l.strip().replace(",", " ").split()
	protocol = l[0]
	if protocol in ICMP: 
		protocol = 'icmp'
		l = "icmp "+orgl
		l = l.strip().replace(",", " ").split()
	for x in l[1:]:
		port = x
		port_type = 'eq_candidate'
		if not port == port.replace("-"," ") and port.find("echo") == -1:
			port = port.replace("-"," ")
			port_type = 'range_candidate'
		if port in WELL_KNOWN_PORTS: port = WELL_KNOWN_PORTS[port]
		ppp.append((protocol, port_type, port))
	return ppp

def createPortDic(ppp):
	"""Generate port dictionary for generation of port object container
	"""
	dic = {}
	for item in ppp:
		for tpl in item:
			if not dic.get(tpl[1]):
				dic[tpl[1]] = set()
			dic[tpl[1]].add(tpl[2])
			if not dic.get('type'):
				dic['object_type'] = 'port-object'
	return dic

# ----------------------------------------------------------------------------------------

def addaction(df):
	"""--> addaction for each rows """
	ipsdic, portsdic, counter = {}, {}, 0
	for x in range(len(df)):
		row = df.iloc[x]
		firewalls = (row.src_fw, row.dst_fw)
		for fw_name in firewalls:
			if not fw_name: continue
			if not "action" in df.columns:
				df["action"] = "permit"
				row = df.iloc[x]
			if row.action == "":
				df.at[x, 'action'] = 'permit'
	return df
# ----------------------------------------------------------------------------------------
