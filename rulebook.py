
from general import *
from abc import ABC, abstractproperty
from acg import Obj
# ----------------------------------------------------------------------------------------
def rulebook_sequence(service_request_type, customer):
	"""-->request type object"""
	if service_request_type.lower() == 'del':
		srObj = DelRequestRuleBook(service_request_type, customer)
	elif service_request_type.lower() == 'add':
		srObj = AddRequestRuleBook(service_request_type, customer)
	else:
		lgmain.save(f"Wrong Input, {service_request_type}", WARN)
		srObj = None
	return srObj

# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
class RuleBook(ABC):
	"""RuleBook defining various operations and sequence to be check in order"""

	def __init__(self, service_request_type, customer):
		self.sr = service_request_type.lower()
		self.customer = customer
		self.merged_matched_acl_lines = {
			'source_candidate': [],
			'destination_candidate': [], 
			'port': [] ,
			'protocol': [],
		}
		self.merged_sub_matched_lines = {
			'source_candidate': [],
			'destination_candidate': [], 
			'port': [] ,
			'protocol': [],
		}
		self.merged_super_matched_lines = {
			'source_candidate': [],
			'destination_candidate': [], 
			'port': [] ,
			'protocol': [],
		}


	@abstractproperty
	def sequence(self):
		pass

	@property
	def exact_match_acl_lines(self):
		"""-->set of exactly matched acl lines"""
		u = None
		newmal = {'protocol':set(), 'port':set(), "source_candidate":set(), "destination_candidate": set()}
		for k, allv in self.merged_matched_acl_lines.items():
			for v in allv:
				if v.get("exist") and v.get("exact"):
					newmal[k].add(v["acl_line_number"])
		for k, v in newmal.items():
			if u is None: u = v
			u.intersection_update(v)
		self.exact_matched_acl_lines = u
		return u		

	@property
	def super_match_acl_lines(self):
		"""-->set of partial/super matched acl lines"""
		u = set()
		newmal = {'protocol':[], 'port':[], "source_candidate":[], "destination_candidate": []}
		newmalgp = {'protocol':[], 'port':[], "source_candidate":[], "destination_candidate": []}
		finalmalgp = {'protocol':[], 'port':[], "source_candidate":[], "destination_candidate": []}
		for k, allv in self.merged_super_matched_lines.items():
			for v in allv:
				if v.get("exist") and v.get("supersetgroup_"+k):
					newmal[k].append(v["acl_line_number"])
					newmalgp[k].append(v["supersetgroup_"+k])
				elif v.get("exist") and v.get("exact"):
					newmal[k].append(v["acl_line_number"])
					newmalgp[k].append("exact")

		for k, v in newmalgp.items():
			for i, item in enumerate(v):
				if not item or item is None:
					newmal[k][i] = ""
		
		u1 = None
		for k, v in newmal.items():
			if u1 is None: u1 = set(v)
			u1.union(v)

		for i in u1:
			try:
				if (
					i in newmal['source_candidate'] and
					i in newmal['destination_candidate'] and
					i in newmal['port'] and
					i in newmal['protocol']
					):
					s = newmalgp['source_candidate'][newmal['source_candidate'].index(i)]
					d = newmalgp['destination_candidate'][newmal['destination_candidate'].index(i)]
					pt= newmalgp['port'][newmal['port'].index(i)]
					pr= newmalgp['protocol'][newmal['protocol'].index(i)]
					if 'exact' == s and 'exact' == d and 'exact' == pt and 'exact' == pr:
						continue
					finalmalgp['source_candidate'].append({i:s})
					finalmalgp['destination_candidate'].append({i:d})
					finalmalgp['port'].append({i:pt})
					finalmalgp['protocol'].append({i:pr})
			except:
				continue
		self.super_matched_acl_lines = finalmalgp
		return u

	@property
	def sub_match_acl_lines(self):
		"""sub matched acl lines filtering"""
		u = set()
		for k, allv in self.merged_sub_matched_lines.items():
			self.merged_sub_matched_lines[k] = remove_duplicate(allv)


	def merge_exact_lines(self, matchedlines):
		"""Merge Matched lines with merged matched acl lines"""
		for k, allv in matchedlines.items():
			self.merged_matched_acl_lines[k].extend(allv)

	def merge_super_matched_lines(self, matchedlines):
		"""Merge Matched lines with merged super matched acl lines"""
		for k, allv in matchedlines.items():
			self.merged_super_matched_lines[k].extend(allv)

	def merge_sub_matched_lines(self, matchedlines):
		"""Merge Matched lines with sub merged matched acl lines"""
		for k, allv in matchedlines.items():
			if not allv in self.merged_sub_matched_lines[k]:
				self.merged_sub_matched_lines[k].extend(allv)

# ----------------------------------------------------------------------------------------
class DelRequestRuleBook(RuleBook):
	"""DELETE REQUEST RULES"""
	def merge(self, matchedlines):
		"""sequence of merger"""
		self.merge_exact_lines(matchedlines)
		self.merge_super_matched_lines(matchedlines)
	
	@property
	def sequence(self):
		"""sequence of operation"""
		self.exact_match_acl_lines
		self.super_match_acl_lines


# ----------------------------------------------------------------------------------------
class AddRequestRuleBook(RuleBook):
	"""ADD REQUEST RULES"""
	def merge(self, matchedlines):
		"""sequence of merger"""
		self.merge_exact_lines(matchedlines)
		self.merge_sub_matched_lines(matchedlines)

	@property
	def sequence(self):
		"""sequence of operation"""
		self.exact_match_acl_lines
		self.sub_match_acl_lines

# ----------------------------------------------------------------------------------------
def remove_duplicate(lst):
	'''Remove duplicate values from list'''
	ll = []
	for x in lst:
		if x not in ll:
			ll.append(x)	
	return ll
# ----------------------------------------------------------------------------------------
	