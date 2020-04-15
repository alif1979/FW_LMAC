

from general import *
from common import InitGroups, DictMethods, network_type, port_type
from addressing import addressing
from acg import Obj
# ----------------------------------------------------------------------------------------
class AclDict(InitGroups, DictMethods):
	"""Dictionary of ACLs"""
	def __str__(self):
		return f"[O]: Access-List-Dictionary for Device: " + super().__str__()

	def get_groups(self, acl_list, object_group_dict):
		"""set ACL"""
		acl, aclName = {}, []
		for line in acl_list:
			if blank_line(line): continue
			if hostname_line(line, self.hostname): continue
			spl = line.split()
			if line.lstrip() != line: continue		##obj-group expanded lines
			if find_any(line, ('END', 'elements','cached')): continue #counter, exception lines
			try:
				if spl[0] == 'access-list' and spl[1] not in aclName:
					aclName.append(spl[1])
					self[spl[1]] = Acl(self.hostname, acl_list, spl[1], line, object_group_dict)
					continue
			except:
				lgmain.save(f"!!!Error Parsing Line {spl}, skipping!!!", ERR)			
		return None

# ----------------------------------------------------------------------------------------
class Acl(DictMethods):
	"""ACL Detail"""
	def __str__(self):
		return f"[O]: Access-List: " + super().__str__()

	def __init__(self, hostname, acl_list, aclName, beingline=None, object_group_dict=None):
		self.acl_name = aclName
		self.name = aclName
		self.acg = object_group_dict
		self.dic = parse_acldic(hostname, acl_list, aclName, beingline, object_group_dict)

	def matching_remark_numbers(self, remark):
		"""set of line numbers for matching remark in ACL"""
		return {acl_number 
			for acl_number, line_attr in self 
			if line_attr['remark']==remark and line_attr["action"] != "None"}

	def remark_line_number(self, remark):
		"""Line number of the remark line"""
		return min({int(acl_number) for acl_number, line_attr in self if line_attr['remark']==remark})

	def find_description(self, frStr, toStr):
		"""-->Find Description and get last line number for that matching description section"""
		frStr = frStr.lower()
		toStr = toStr.lower()
		for i in range(3):
			for k, v in self:
				found = False
				f = "from " + frStr in v["remark"].lower()
				t = "to " + toStr in v["remark"].lower()
				onlyf = f and "to " not in v["remark"].lower()
				onlyt = t and "from " not in v["remark"].lower()
				if ((i==0 and f and t) or 
					(i==1 and onlyf) or
					(i==2 and onlyt)): 
					found = True
					rem = v["remark"]
					break
			if found: break
		if found:
			return max([k for k, v in self if v['remark']==rem])
		else:
			exc = False 
			if toStr in ALIAS_DICT:
				toStr =  ALIAS_DICT[toStr]
				exc = True
			if frStr in ALIAS_DICT:
				frStr =  ALIAS_DICT[frStr]
				exc = True
			if exc: return self.find_description(frStr, toStr)
		return None

	def find_desc_via_ip(self, srcip, dstip):
		pass


	def search_rule(self, **kwargs):
		"""--> Line number, for matching rule; None else """
		all_matches = {}
		for line, rule in self:
			if kwargs.get('remark') and rule['remark'] != kwargs['remark']: continue
			for key, matches in self._set(line, **kwargs):
				if not all_matches.get(key):
					all_matches[key] = []
				all_matches[key].append(matches)
		return all_matches

	def _set(self, line, **kwargs):
		"""-->mathing rule parameters"""
		for k, v in kwargs.items():			
			if k == 'remark': continue
			if isinstance(self[line][k], Obj):
				selflinek = set(self.acg.group_members(self[line][k].name))
			elif isinstance(self[line][k], str):
				selflinek = set({self[line][k]})
			else:
				selflinek = self[line][k]

			if not isinstance(v, set): v = set({v})

			yp = {}
			if v == selflinek:
				yp['acl_line_number'] = line
				yp["exist"] = True
				yp["exact"] = True
				yield (k, yp)
				continue
			if v.issubset(selflinek):
				yp['acl_line_number'] = line
				yp["exist"] = True
				yp[f"supersetgroup_{k}"] = self[line][k]
				yield (k, yp)
				continue
			if v.issuperset(selflinek):
				yp['acl_line_number'] = line
				yp["exist"] = True
				yp[f"subsetgroup_{k}"] = self[line][k]
				yield (k, yp)
				continue
			elif isinstance(self[line][k], Obj):
				yp['acl_line_number'] = line
				yp["exist"] = True
				yp[f"subsetgroup_{k}"] = self[line][k]
				yield (k, yp)
				continue
			else:
				continue

def parse_acldic(hostname, acl_list, aclName, beingline, object_group_dict):
	'''read thru full access-list and return it in dict format
	acl_list = show access-list output list
	aclName = specific ACL to filter
	--> dict with all acl para
	'''
	acl, remark = OrderedDict(), ''
	for line in acl_list:
		if blank_line(line): continue
		if line.startswith(hostname) and start: break
		if hostname_line(line, hostname): continue
		try:
			spl = line.split()
			if spl[1] != aclName: 
				start = True
				continue
			if line.lstrip() != line: continue		                  # obj-group expanded lines
			if find_any(line, ('END', 'elements','cached')): continue # counter, exception lines
			if spl[1] != aclName: start = False
			if line == beingline:
				start = True
			if not start: continue
			if start and spl[1] != aclName: break

			# initial blank set
			(line_no, action, protocol, source_type, source_candidate,
			destination_type, destination_candidate, destination_port_type, 
			destination_port) = ('', '', '','', '', '', '', '', '')

			# ADD REMARK AND ACL NAME
			line_no = spl[3]
			if found(line, 'remark '):
				rspl = line.split('remark ')
				# acl_name = rspl[0].split()[1]
				remark = rspl[-1].strip()#.strip().replace("*",'').strip()
				acl[line_no] = make_dict("None", "None", "None", "None",
				"None", "None", "None", "None", remark, "None")
				continue

			### ADD REST (action, protocol,...)
			action = spl[5]
			protocol = spl[6]
			log_warning = found(line, "log warnings")
			# source
			source_type, source_candidate = network_type(spl, 7)
			if spl[9] in ('eq', ): pass           # Source Port - unimplemented
			# destination
			dest_cand_distance = 1 if spl[7] in ('any', 'any4') else 2
			destination_type, destination_candidate = network_type(spl, 7+dest_cand_distance)
			if protocol == "ip":
				destination_port_type, destination_port = "", ""
			else:
				destination_port_type, destination_port = port_type(spl, 11)

			if source_type == 'object-group_candidate': 
				source_candidate = object_group_dict[source_candidate]
				source_candidate.permitted_on.add(line_no)
			if destination_type == 'object-group_candidate': 
				destination_candidate = object_group_dict[destination_candidate]
				destination_candidate.permitted_on.add(line_no)
			if port_type == 'object-group_candidate': 
				destination_port = object_group_dict[destination_port]
				destination_port.permitted_on.add(line_no)

			# make dict
			acl[line_no] = make_dict(source_type, source_candidate, 
				destination_type, destination_candidate,
				action, protocol, destination_port_type, destination_port, 
				remark, log_warning)
		except:
			lgmain.save(f"!!!Error Parsing Line '{line}'!!!", ERR)
		
	return acl

def make_dict(src_t, src, dst_t, dst, act, prot, pt_t, pt, rem, log):
	""" Make dictionary """
	return {
			'source_candidate_type': src_t, 
			'source_candidate': src,
			'destination_candidate_type': dst_t, 
			'destination_candidate': dst,
			'action': act, 
			'protocol': prot,
			'port_type': pt_t, 
			'port': pt,
			'remark': rem,
			'log_warning': log,
		}


# ----------------------------------------------------------------------------------------
