
from general import *
from addressing import addressing
# ----------------------------------------------------------------------------------------
rct_candids = ('source_candidate_type', 'destination_candidate_type', 'port_type')
obj_candids = ('source_candidate', 'destination_candidate', 'port')
# ----------------------------------------------------------------------------------------
class Firewall(object):
	"""Firewall object """

	def __init__(self, fw, load, row):
		""" set initial parameters """
		self.fw = fw
		self.RT = load[fw]['RT']
		self.intvsAcl = load[fw]['intvsAcl']
		self.acldict = load[fw]['acldict']
		self.objgrps = load[fw]['objgrps']
		s, d = fw + "src_ip_grps", fw + "dst_ip_grps"
		self.row = row

	@property
	def ports(self):
		for port_line in self.row.dst_port.split("\n"):
			for protocol, attrib in self.action_port_protocol(port_line).items():
				yield protocol, attrib

	def action_port_protocol(self, port_line):
		"""Generate and yield -> ports attributes 'APPP' (a row from Excel column)"""
		return appp(self.row, port_line)

	def get_acl(self, src, base="SOURCE"):
		"""--> Find acl Name based on source(default) ip
		[Looks in routing table and inverse lookup to intvsACL to get ACL]
		"""
		self.acl = None
		if isinstance(src, dict):
			lgmain.save("UNIMPLEMENTED.. TBD - firewall[91]", WARN)
		elif isinstance(src, (set, str)):
			ip = src
		if base == "SOURCE":
			self.s_prefix_desc = self.RT.get_prefix_desc(ip)
			acl = self.intvsAcl[self.s_prefix_desc]
		elif base == "DESTINATION":
			self.d_prefix_desc = self.RT.get_prefix_desc(ip)
			acl = self.intvsAcl[self.d_prefix_desc]
		self.acl = acl
		return self.acl

	def objgrp(self, grpObj, newmembers, sr):
		"""ADD/REMOVE OBJECT Group content."""
		group_type = grpObj["group_type"]
		group_name = grpObj.name
		if group_type in ("network",):
			object_type = "network-object"
			candidate_type = "host"
		elif group_type == "service":
			object_type = "port-object"
			candidate_type = "eq"   # modify later for different
		l = ""
		if isinstance(newmembers, (tuple, list, set)):
			l += f"object-group {group_type} {group_name}\n"
			if sr == "del":
				for candidate in newmembers:
					l += self.objgrpadd(object_type, candidate_type, candidate)
			elif sr == "add":
				for candidate in newmembers:
					l += self.objgrprem(object_type, candidate_type, candidate)
		elif isinstance(newmembers, str):
			if sr == "del":
				l += self.objgrpadd(object_type, candidate_type, candidate)
			elif sr == "add":
				l += self.objgrprem(object_type, candidate_type, candidate)
		l += "!"
		return l

	def objgrpadd(self, object_type, candidate_type, candidate):
		return f" {object_type} {candidate_type} {candidate}\n"
	def objgrprem(self, object_type, candidate_type, candidate):
		return " no" + self.objgrpadd(object_type, candidate_type, candidate)



# ----------------------------------------------------------------------------------------
class Add(Firewall):
	"""class defining add request methods, Inherits Firewall class"""

	def newdesc(self, aclname, line_no, rule_desc):
		l = f"access-list {aclname} line {int(line_no)+1} remark {FORTEEN_STARS} {rule_desc} {FORTEEN_STARS}"
		return l

	def rollback_newdesc(self, aclname, line_no, rule_desc):
		line_no = f"line {int(line_no)+1} " if LINENO_ON_DEL else ""
		return f"no access-list {aclname} {line_no}remark {FORTEEN_STARS} {rule_desc} {FORTEEN_STARS}"

	def rule_common(self, rule_type, aclname, line_no, **attr):
		"""--> String representation of Delete request rule config"""
		log_warning = " log warnings" if LOG_WARNING else ""
		for x in rct_candids:
			attr[x] = remve_candidate_trailer(attr[x])
		for x in obj_candids:
			if str(attr[x]).startswith("[O]: Object-Group:"):
				attr[x] = attr[x].name
		sptype, spfx = prefix_str(attr['source_candidate_type'], attr['source_candidate'])
		dptype, dpfx = prefix_str(attr['destination_candidate_type'], attr['destination_candidate'])
		port = port_alias(attr['port'])
		line_number = f'line {int(line_no)+1} ' if rule_type == 'CHG' or LINENO_ON_DEL else ''		
		l = f"access-list {aclname} {line_number}extended {attr['action']}\
 {attr['protocol']} {sptype}{spfx} {dptype}{dpfx} {attr['port_type']} {port}{log_warning}"
		return l

	def rule(self, aclname, line_no, **attr):
		"""--> String representation of Delete request rule config"""
		return self.rule_common('CHG', aclname, line_no, **attr)

	def rollback_rule(self, aclname, line_no, **attr):
		"""--> String representation of Delete request rule config"""
		return "no " + self.rule_common('RBK', aclname, line_no, **attr)

# ----------------------------------------------------------------------------------------
class Del(Firewall):
	"""class defining delete request methods, Inherits Firewall class"""

	def rule_common(self, rule_type, aclname, line_no, org_logwarn, **attr):
		"""--> String representation of Common DEL request rule config"""
		line_no = f"line {line_no} " if rule_type == "RBK" or LINENO_ON_DEL else ""
		log_warning = " log warnings" if LOG_WARNING and org_logwarn else ""
		for x in rct_candids:
			attr[x] = remve_candidate_trailer(attr[x])
		for x in obj_candids:
			if str(attr[x]).startswith("[O]: Object-Group:"):
				attr[x] = attr[x].name
		sptype, spfx = prefix_str(attr['source_candidate_type'], attr['source_candidate'])
		dptype, dpfx = prefix_str(attr['destination_candidate_type'], attr['destination_candidate'])
		l = f"access-list {aclname} {line_no}extended {attr['action']}\
 {attr['protocol']} {sptype}{spfx} {dptype}{dpfx} {attr['port_type']} {attr['port']}{log_warning}"
		return l

	def rule(self, aclname, line_no, org_logwarn, **attr):
		"""--> String representation of Delete request rule config"""
		return "no " + self.rule_common('CHG', aclname, line_no, org_logwarn, **attr)

	def rollback_rule(self, aclname, line_no, org_logwarn, **attr):
		"""--> String representation of Delete request rule config"""
		return self.rule_common('RBK', aclname, line_no, org_logwarn, **attr)

	def rem_rule_common(self, rule_type, aclname, line_no, rem):
		line_no = f"line {line_no} " if rule_type == "RBK" or LINENO_ON_DEL else ""
		l = f"access-list {aclname} {line_no}remark {rem}"
		return l

	def rem_rule(self, aclname, line_no, rem):
		return "no " + self.rem_rule_common('CHG', aclname, line_no, rem)

	def rem_rollback_rule(self, aclname, line_no, rem):
		return self.rem_rule_common('RBK', aclname, line_no, rem)

# ----------------------------------------------------------------------------------------
def request_type_object(fw, load, row):
	"""Create Firewall Object based on request"""
	f = None
	req_type = get_request(row)
	if req_type == 'del':
		f = Del(fw, load, row)
	elif req_type == 'add':
		f = Add(fw, load, row)
	return f

def remve_candidate_trailer(s):
	"""Trunk candidate trailer"""
	return s[:-10] if s[-10::] == "_candidate" else s

def prefix_str(ptype, pfx):
	"""Prefix String"""
	if ptype == "prefix":
		ptype = ""
		pfx = addressing(pfx).ipbinmask()
		return (ptype, pfx)
	else:
		return (ptype + " ", pfx)

# ----------------------------------------------------------------------------------------
