
from general import *
from rulebook import rulebook_sequence
from acg import Obj
# ----------------------------------------------------------------------------------------
#  DEL REQUEST
# ----------------------------------------------------------------------------------------
def process_del_request(req_type, fwop, acl, aclname, f, 
	src_candid, dst_candid, port, protocol, row, rw, lg):
	"""DELETE REQUEST PROCESSING"""
	if req_type != 'del': return None
	srObj = rulebook_sequence(req_type, row.customer)
	rule = {
		'source_candidate': src_candid,
		'destination_candidate': dst_candid, 
		'port': port ,
		'protocol': protocol,
	}
	# Group check
	matchedlines = acl.search_rule(**rule)
	srObj.merge(matchedlines)

	# Individual check
	for items_to_check in combinations(row.src_ip, row.dst_ip, port, {protocol,}):
		rule = {
			'source_candidate': items_to_check[0],
			'destination_candidate': items_to_check[1], 
			'port': items_to_check[2],
			'protocol': items_to_check[3],
		}
		matchedlines = acl.search_rule(**rule)
		srObj.merge(matchedlines)

	# Sequencing both, and add to output
	srObj.sequence
	#------------------------------------------------------------------
	if srObj.exact_matched_acl_lines:
		lg.save(f'One to One Matched ACL Lines: {srObj.exact_matched_acl_lines}', DEBUG)
	if srObj.super_matched_acl_lines:
		lg.save(f'Lines present with sparse match', DEBUG)
	#------------------------------------------------------------------
	#1. Remove 1 to 1 exactly matched rule. <ip/group to ip/group>
	if srObj.exact_matched_acl_lines:
		for line_no in srObj.exact_matched_acl_lines:
			fwop.add_del_req_op(acl, aclname, line_no, srObj, f, rw)

	#2.1  Remove group full if group is applied only at one place. or removing all lines.
	#     TBD- on row 65 in section 2.2

	#2.2  Remove members from object group if group is applied multiple places instead of 
	#     removing rule from step 2.
	if srObj.super_matched_acl_lines:
		for k, v in  srObj.super_matched_acl_lines.items():
			if k == "destination_candidate": 
				newmembers = row.dst_ip
			elif k == "source_candidate": 
				newmembers = row.src_ip
			elif k == "port": 
				newmembers = v
			for i in v:
				for key, value in i.items():
					if isinstance(value, Obj):
						if value.permitted_on.issubset(srObj.exact_matched_acl_lines):
							print("WARNG Full obje grop remove TBD, ........")
					if value == "exact": continue
					fwop.add_object_group(value, newmembers, srObj, f, rw)
	return srObj.exact_matched_acl_lines

def desc_remove_per_row(prev_emls, acl, aclname, fwop, row, f, rw):
	"""DESCRIPTION REMOVAL - ROW BASES 
	Split rules not eligible to remove description."""
	rule_desc = None
	if prev_emls:
		for line_no in prev_emls:
			if not rule_desc: rule_desc = acl[line_no]['remark']
		mrn = acl.matching_remark_numbers(rule_desc)
		if mrn.issubset(prev_emls):
			rem_linenum = str(acl.remark_line_number(rule_desc))
			fwop.rem_on_del_req_op(aclname, rem_linenum, row.customer, f, rw, rule_desc)

# ----------------------------------------------------------------------------------------
#                ADD REQUEST
# ----------------------------------------------------------------------------------------
def process_add_request(req_type, fwop, acl, aclname, acg, f, 
	src_candid, dst_candid, port_type, port, protocol, row, rw, lg, prlastline):
	"""ADD REQUEST PROCESSING"""
	if req_type != 'add': return None
	srObj = rulebook_sequence(req_type, row.customer)

	## 1. find requestor description and last line from acl
	lastline = acl.find_description(row.src_name, row.dst_name)
	if not prlastline and lastline:
		rule_desc = acl[lastline]['remark']
		newdesc = False
	else:
		newdesc = True
		rule_desc = "From " + row.src_name + " inTo " + row.dst_name
		lastline = max([int(x) for x in acl.dic.keys()]) if not prlastline else prlastline
		rule_desc_to_add = True if not prlastline else False

	## 2. check for existing object group if any.
	rule = {
		'remark': rule_desc,
		'source_candidate': src_candid,
		'destination_candidate': dst_candid, 
		'port': port,
		'protocol': protocol,
		}

	# Group check
	exact_candid_group_names = acg.search_group(**rule)
	matchedlines = acl.search_rule(**rule)
	srObj.merge(matchedlines)

	# Individual check
	for items_to_check in combinations(row.src_ip, row.dst_ip, port, {protocol,}):
		rule = {
			'remark': rule_desc,
			'source_candidate': items_to_check[0],
			'destination_candidate': items_to_check[1], 
			'port': items_to_check[2],
			'protocol': items_to_check[3],
		}
		matchedlines = acl.search_rule(**rule)
		srObj.merge(matchedlines)
	srObj.sequence

	# Check duplication
	if srObj.exact_matched_acl_lines:
		for line_no in srObj.exact_matched_acl_lines:
			fwop.append(EXC, (f'Rule Already Exist on Row {srObj.exact_matched_acl_lines},\
 for Excel request row {rw}', row.customer, int(rw)))

	# get Groups
	# commonmatchedlines = get_common_linenumbers(srObj.merged_sub_matched_lines)
	# mml = maxmatchingline(srObj.merged_sub_matched_lines, commonmatchedlines)
	# select Group 		--> temporary removed to be check again.
	# if row.customer_prefix.upper() != 'CP' and mml:
	# 	grpcandidlist = {
	# 		'source_candidate': src_candid,
	# 		'destination_candidate': dst_candid, 
	# 		'port': port,
	# 		}
	# 	for grpdics in mml:
	# 		# print(grpdics)
	# 		for who, grp in grpdics.items():
	# 			fwop.add_object_group(grp, grpcandidlist[who], srObj, f, rw)

	# Individual ACL RULE
	if not True: pass
	else:
		if not newdesc:
			lastline = add_individual_rule(acl, aclname, lastline, row, port_type, port, protocol, fwop, srObj, f, rw, exact_candid_group_names)
		else:
			lastline = add_new_individual_rule(acl, aclname, lastline, row, port_type, port, protocol, fwop, srObj, f, rw, rule_desc, rule_desc_to_add, exact_candid_group_names)

	return lastline

# ----------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------------------------

def get_common_linenumbers(matchedlines):
	"""-->set of common linenumber for matched lines"""
	linesets = {"source_candidate":set(), "destination_candidate":set(), "port":set(), "protocol":set()}
	for key, valuelist in matchedlines.items():
		for adic in valuelist:
			linesets[key].add(adic['acl_line_number'])
	u = set()
	for ls in linesets.values():
		if not u: u = ls
		u.intersection_update(ls)
	return u

def maxmatchingline(matchedlines, commonmatchedlines):
	"""-->maximum exact value matching line object group lists"""
	d = {'count': 0, 'groupnames':[]}
	linesets = {}
	for linenumber in commonmatchedlines:
		linesets[linenumber] = d.copy()
		for key, valuelist in matchedlines.items():
			for adic in valuelist:
				if adic["acl_line_number"] != linenumber: continue
				if adic.get("subsetgroup_"+key) and isinstance(adic.get("subsetgroup_"+key), Obj):
					linesets[linenumber]["groupnames"].append({key: adic.get("subsetgroup_"+key)})
				if adic.get("exact"):
					linesets[linenumber]["count"] += 1
	c = 0
	mml = None
	for k, v in linesets.items():
		if v["count"] > c and v["groupnames"]:
			c = v["count"]			
			mml = v["groupnames"]
	if mml: return mml

# ----------------------------------------------------------------------------------------
def add_individual_rule(acl, aclname, lastline, row, port_type, port, protocol, fwop, 
	srObj, f, rw, exact_candid_group_names):
	""" Individual Rule with ips """
	lastlineattr = acl[lastline]
	lastline = int(lastline)
	sdp_attr_sets = get_set_names(row, port, exact_candid_group_names)
	sd_cand_types = candid_type_set(exact_candid_group_names)

	for items_to_check in combinations(*sdp_attr_sets, {protocol,}):
		#Future Note: update candidate type to object_group_candidate for new rule
		#             which is added using new object group instead of individual ips.
		attr = 	{
			'source_candidate_type': sd_cand_types['sct'],
			'source_candidate': items_to_check[0],
			'destination_candidate_type': sd_cand_types['dct'],
			'destination_candidate': items_to_check[1], 
			'action': 'permit',
			'protocol': items_to_check[3],
			'port_type': port_type,
			'port': items_to_check[2],
			'remark': lastlineattr['remark'],
		}
		fwop.add_add_req_op(aclname, lastline, srObj, f, rw, attr)	
		lastline += 1
	return lastline
# ----------------------------------------------------------------------------------------
def add_new_individual_rule(acl, aclname, lastline, row, port_type, port, protocol, fwop, 
	srObj, f, rw, rule_desc, rule_desc_to_add, exact_candid_group_names):
	""" Individual Rule with ips """
	# lastlineattr = acl[lastline]
	lastline = int(lastline)
	if rule_desc_to_add:
		_myrule = f.newdesc(aclname, lastline, rule_desc)
		_rollbackrule = f.rollback_newdesc(aclname, lastline, rule_desc)
		fwop.add_output(srObj.customer, rw, AR, ARR, _myrule, _rollbackrule)
		lastline += 1
	sdp_attr_sets = get_set_names(row, port, exact_candid_group_names)
	sd_cand_types = candid_type_set(exact_candid_group_names)

	for items_to_check in combinations(*sdp_attr_sets, {protocol,}):
		#Future Note: update candidate type to object_group_candidate for new rule
		#             which is added using new object group instead of individual ips.
		attr = 	{
			'source_candidate_type': sd_cand_types['sct'],
			'source_candidate': items_to_check[0],
			'destination_candidate_type': sd_cand_types['dct'],
			'destination_candidate': items_to_check[1], 
			'action': 'permit',
			'protocol': items_to_check[3],
			'port_type': port_type,
			'port': items_to_check[2],
			'remark': rule_desc
		}
		fwop.add_add_req_op(aclname, lastline, srObj, f, rw, attr)
		lastline += 1
	return lastline

def get_set_names(row, port, exact_candid_group_names):
	"""--> attribute sets/names (source, destination, port) """
	src_set, dst_set, port_set = row.src_ip, row.dst_ip, port
	for k, v in exact_candid_group_names.items():
		if k == 'destination_candidate': dst_set = {v,}
		if k == 'source_candidate': src_set = {v,}
		if k == 'port': port_set = {v,}
	return (src_set, dst_set, port_set)

def candid_type_set(exact_candid_group_names):
	dic = {"sct": "host_candidate", "dct": "host_candidate"}
	if exact_candid_group_names.get("source_candidate"):
		dic["sct"] = "object-group_candidate"
	if exact_candid_group_names.get("destination_candidate"):
		dic["dct"] = "object-group_candidate"
	return dic

## ----------------------------------------------------------------------------------------
