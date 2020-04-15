
from general import *
from abc import ABC, abstractclassmethod
from addressing import binsubnet
# ----------------------------------------------------------------------------------------
class InitGroups(ABC):
	def __init__(self, hostname=None, confList=None, object_group_dict=None):
		self.dic = {}
		if hostname:
			self.hostname = hostname
			self.name = hostname
			self.get_groups(confList, object_group_dict)

	@abstractclassmethod
	def get_groups(self):
		pass

# ----------------------------------------------------------------------------------------
class DictMethods():
	def __str__(self):
		if len(self.dic.keys()) > 7:
			try: return f"['{self.name}'] --> with Keys:{tuple(self.dic.keys())[:7]} ...and more"
			except: return f"[O] --> with Keys:{tuple(self.dic.keys())[:7]} ...and more"
		else:
			try: return f"['{self.name}'] --> with Keys:{self.dic.keys()}"
			except: return f"[O] --> with Keys:{self.dic.keys()}"
	def __iter__(self):
		for k, v in self.dic.items():
			yield (k, v)
	def __getitem__(self, item):
		try:
			return self.dic[item]
		except KeyError:
			return None
	def __get__(self, key, item):
		try:
			return self[key][item]
		except KeyError:
			return None
	def __setitem__(self, item, value):
		self.dic[item] = value
	def __delitem__(self, srno):
		try:
			for k in sorted(self.dic.keys()):
				if k <= srno: continue
				self.dic[k-1] = self.dic[k]
			del(self.dic[k])
		except:
			raise KeyError
	def append(self, item, value):
		try:
			if not self.dic.get(item):
				self.dic[item] = []
			elif isinstance(self.dic[item], (str, int)):
				self.dic[item] = [self.dic[item],]
			self.dic[item].append(value)
		except:
			raise Exception

# ----------------------------------------------------------------------------------------
def network_type(spl, idx):
	'''check if spl index value is host, prefix or object-group 
	spl=splitted line, idx=index
	--> tuple with type identified, candidate ip/prefix/object-groupname
	'''
	_type = ''
	_candidate = ''
	if spl[idx] in ('host', 'object-group', 'object'):
		_type = spl[idx] + "_candidate"
		_candidate = spl[idx+1]
	elif spl[idx] in ('any', 'any4'):
		_type = 'prefix'+ "_candidate"
		try:
			_candidate = '0.0.0.0/0'
		except:
			lgmain.save(f"ERROR: caching network_type failed for acl: ,{spl}", CRITICAL)
			raise Exception
	else:
		_type = 'prefix'+ "_candidate"
		try:
			_candidate = spl[idx]+'/'+str(binsubnet(spl[idx+1]).count('1'))
		except:
			print(spl, idx)
			lgmain.save(f"ERROR: caching network_type failed for acl: ,{spl}", CRITICAL)
			raise Exception
	return (_type, _candidate)


def port_type(spl, idx):
	'''check if spl index value is eq, icmp, range etc... 
	spl=splitted line, idx=index
	--> tuple with type identified, candidate ports
	'''
	_type = ''
	_candidate = ''
	if spl[idx] in ('eq', 'object-group'):
		_type = spl[idx] + "_candidate"
		_candidate = spl[idx+1]
	elif spl[idx] in ICMP:
		_type = ''
		_candidate = spl[idx]
	elif spl[idx] == 'range':
		_type = spl[idx] + "_candidate"
		_candidate = spl[idx+1]+' '+spl[idx+2]		
	return (_type, _candidate)

# ----------------------------------------------------------------------------------------
