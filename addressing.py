
from general import *

incorrectinput = 'INCORRECT SUBNET OR SUBNET MASK DETECTED NULL RETURNED'
# ----------------------------------------------------------------------------
# Module Functions
# ----------------------------------------------------------------------------

def binsubnet(subnet):
	"""converts provided decimal format subnet to binary format and return 
	strings of binary.
	--> str

	:param subnet: IPv4 address
	:param type: str
	"""
	try:
		s = ''
		octs = subnet.split("/")[0].split(".")
		for o in octs:
			bo = str(bin(int(o)))[2:]
			lbo = len(bo)
			pzero = '0'*(8 - lbo)
			s = s + pzero + bo
		return s
	except:
		pass


def addressing(subnet):
	'''main function proiving ip-subnet object for various functions on it
	--> ipsubnet object

	:param: subnet: either ipv4 or ipv6 subnet with /mask
	:param type: str

	:param decmask: decimal mask notation only in case of IPv4 (optional)
	:param type: str
	'''
	v_obj = Validation(subnet)
	if v_obj.validated:
		version = v_obj.version
		if version == 4:
			return IPv4(v_obj.subnet)
		else:
			return None


def isSplittedRoute(line):
	"""	1: No single line,
		0 : Yes splitted line [line1]
		-1: Yes splitted line [line2]
	"""
	if found(line, ','):
		return 1 if len(line.split()) > 5 else -1
	else:
		return 0


def isSubset(pfx, supernet):
	if not isinstance(pfx, (str, IPv4)):
		raise Exception("INPUTERROR")
	if not isinstance(supernet, (str, IPv4)):
		raise Exception("INPUTERROR")
	if isinstance(supernet, str): supernet = addressing(supernet)
	if isinstance(pfx, str): pfx = addressing(pfx)
	if supernet.mask <= pfx.mask:
		supernet_bin = binsubnet(supernet.subnet)
		pfx_bin = binsubnet(pfx.subnet)
		if supernet_bin[0:supernet.mask] == pfx_bin[0:supernet.mask]:
			return True
	return False	


# private
# Concatenate strings s and pfx with conjuction
def _strconcate(s, pfx, conj=''):
	"""Concatenate strings s and pfx with conjuction
	--> str

	:param s: string
	:param type: str

	:param pfx: string to be added to original string s.
	:param type: str

	:param conj: conjuctor to be use while gluing the strings.
	:param type: str

	"""
	if s == '':	
		s = s + pfx
	else:
		s = s + conj + pfx
	return s

# ------------------------------------------------------------------------------
# Validation Class - doing subnet validation and version detection
# ------------------------------------------------------------------------------
class Validation(object):
	'''ip-subnet validation class
	:param subnet: ipv4 or ipv6 subnet with "/" mask
	:param type: str

	'''

	def __init__(self, subnet):
		'''ip-subnet validation class
		:param subnet: ipv4 or ipv6 subnet with "/" mask
		:param type: str

		'''
		self.mask = None
		self.subnet = subnet
		self.version = self.__function
		self.validated = False
		if self.version == 4:
			self.validated = self.check_v4_input
		# elif self.version == 6:
		# 	self.validated = self.check_v6_input
		else:
			raise Exception(f'Not a VALID Subnet {subnet}')

	@property
	def __function(self):
		# if found(self.subnet, ":"):
		# 	return 6
		if found(self.subnet, "."):
			return 4
		else:
			return 0

	@property
	def check_v4_input(self):
		'''Property to validate provided v4 subnet
		'''
		# ~~~~~~~~~ Mask Check ~~~~~~~~~
		try:
			self.mask = self.subnet.split("/")[1]
		except:
			self.mask = 32
			self.subnet = self.subnet + "/32"
		try:			
			self.mask = int(self.mask)
			if not all([self.mask>=0, self.mask<=32]):
				raise Exception(f"Invalid mask length {self.mask}")
		except:
			raise Exception(f"Incorrect Mask {self.mask}")

		# ~~~~~~~~~ Subnet Check ~~~~~~~~~
		try:
			octs = self.subnet.split("/")[0].split(".")
			if len(octs) != 4:
				raise Exception(f"Invalid Subnet Length {len(octs)}")
			for i in range(4):
				if not all([int(octs[i])>=0, int(octs[i])<=255 ]):
					raise Exception("Invalid Subnet Octet {i}")
			return True
		except:
			raise Exception("Unidentified Subnet")

# ------------------------------------------------------------------------------
# IPv4 Subnet (IPv4) class 
# ------------------------------------------------------------------------------
class IPv4:
	'''Defines IPv4 object and its various operations
	--> IPv4 object
	
	:param subnet: input ipv4 subnet string
	:param type: str
	'''

	# Initializer
	def __init__(self, subnet):
		'''Initialize IPv4 object

		:param subnet: input subnet string
		:param type: str
		'''
		self.subnet = subnet
		self.mask = int(self.subnet.split("/")[1])
		self.net = self.subnet.split("/")[0]		

	def __getitem__(self, n):
		'''get a specific ip, Range of IP(s) from Subnet'''
		try:
			return self.n_thIP(n, False)
		except:
			l = []
			for x in self.__subnetips(n.start, n.stop):
				l.append(x)
			return tuple(l)

	def __add__(self, n):
		'''add n-ip's to given subnet and return udpated subnet'''
		return self.n_thIP(n, False, "_")

	def __sub__(self, n):
		'''Deduct n-ip's from given subnet and return udpated subnet'''
		return self.n_thIP(-1*n, False, "_")

	def __truediv__(self, n):
		'''Devide provided subnet/super-net to n-number of smaller subnets'''
		return self.__sub_subnets(n)

	def __iter__(self):
		'''iterate over full subnet'''
		return self.__subnetips()

	# --------------------------------------------------------------------------
	# Private Properties
	# --------------------------------------------------------------------------

	# binary to decimal mask convert
	def __bin2decmask(self, binmask):
		return binmask.count('1')

	# binary mask return property
	@property
	def __binmask(self):
		try:
			pone ='1'*self.mask
			pzero = '0'*(32-self.mask)
			return pone+pzero
		except:
			pass

	# Inverse mask return property
	@property
	def __invmask(self):
		try:
			pone ='0'*self.mask
			pzero = '1'*(32-self.mask)
			return pone+pzero
		except:
			pass


	# --------------------------------------------------------------------------
	# Private Methods
	# --------------------------------------------------------------------------

	# binary to Decimal convert subnet method
	@staticmethod
	def __bin2dec(binnet):
		o = []
		for x in range(0, 32, 8):
			o.append(int(binnet[x:x+8], 2))
		return o

	# binary subnet return method
	@staticmethod
	def __binsubnet(subnet):
		return binsubnet(subnet)

	# adjust length of 4 octets
	@staticmethod
	def __set32bits(bins):
		lbo = len(str(bins))
		pzero = '0'*(34 - lbo)
		return pzero+bins[2:]

	# list to octet conversion
	@staticmethod
	def __lst2oct(lst):
		l = ''
		for x in lst:
			l = str(x) if l == '' else l +'.'+ str(x)
		return l

	# compare two binary for and operation
	def __both(self, binone, bintwo):
		b1 = int(binone.encode('ascii'), 2)
		b2 = int(bintwo.encode('ascii'), 2) 
		b1b2 = bin(b1 & b2)
		return self.__set32bits(b1b2)

	# compare two binary for or operation
	def __either(self, binone, bintwo):
		b1 = int(binone.encode('ascii'), 2)
		b2 = int(bintwo.encode('ascii'), 2) 
		b1b2 = bin(b1 | b2)
		return self.__set32bits(b1b2)

	# get n-number of subnets of given super-net
	def __sub_subnets(self, n):
		_iplst = []
		for i1, x1 in enumerate(range(32)):
			p = 2**x1
			if p >= n: break
		_nsm = self.mask + i1
		_nip = int(self.__binsubnet(self.NetworkIP()), 2)
		_bcip = int(self.__binsubnet(self.BroadcastIP()), 2)
		_iis = (_bcip - _nip + 1) // p
		for i2, x2 in enumerate(range(_nip, _bcip+1, _iis)):
			_iplst.append(self.n_thIP(i2*_iis)+ "/" + str(_nsm))
		return tuple(_iplst)

	# yields IP Address(es) of the provided subnet
	def __subnetips(self, begin=0, end=0):
		_nip = int(self.__binsubnet(self.NetworkIP()), 2)
		if end == 0:
			_bcip = int(self.__binsubnet(self.BroadcastIP()), 2)
		else:
			_bcip = _nip + (end-begin)
		for i2, x2 in enumerate(range(_nip, _bcip)):
			if begin>0:  i2 = i2+begin
			yield self.n_thIP(i2)

	# --------------------------------------------------------------------------
	# Available Methods & Public properties of class
	# --------------------------------------------------------------------------

	def NetworkIP(self, withMask=True):
		'''Network IP Address of subnet from provided IP/Subnet
		--> str

		:param withMask: output string with or w/o mask
		:param type: bool

		'''
		try:
			s = self.__binsubnet(self.subnet)
			bm = self.__binmask
			net = self.__lst2oct(self.__bin2dec(self.__both(s, bm )))
			if withMask :
				return net + "/" + str(self.mask)
			else:
				return net
		except:
			pass
	subnetZero = NetworkIP

	def BroadcastIP(self, withMask=False):
		'''Broadcast IP Address of subnet from provided IP/Subnet
		--> str

		:param withMask: output string with or w/o mask
		:param type: bool
		'''
		try:
			s = self.__binsubnet(self.subnet)
			im = self.__invmask
			bc = self.__lst2oct(self.__bin2dec(self.__either(s, im )))
			if withMask :
				return bc + "/" + str(self.mask)
			else:
				return bc
		except:
			pass

	def n_thIP(self, n=0, withMask=False, _=''):
		'''n-th IP Address of subnet from provided IP/Subnet
		--> str
		
		:param n: nth number ip address from provided subnet.
		:param type: int

		:param withMask: output string with or w/o mask
		:param type: bool
		'''
		s = self.__binsubnet(self.subnet)
		if _ == '':
			bm = self.__binmask
			addedbin = self.__set32bits(bin(int(self.__both(s, bm), 2)+n))
		else:
			addedbin = self.__set32bits(bin(int(s.encode('ascii'), 2 )+n))

		if any([addedbin > self.__binsubnet(self.BroadcastIP()), 
				addedbin < self.__binsubnet(self.NetworkIP())]) :
			raise Exception("Address Out of Range")
		else:
			ip = self.__lst2oct(self.__bin2dec(addedbin))
			if withMask :
				return ip + "/" + str(self.mask)
			else:
				return ip

	@property
	def decmask(self):
		'''--> Decimal Mask from provided IP/Subnet - int'''
		return self.mask
	decimalMask = decmask

	@property
	def binmask(self):
		'''--> Binary Mask from provided IP/Subnet - str'''
		return self.__lst2oct(self.__bin2dec(self.__binmask))

	@property
	def invmask(self):
		'''--> Inverse Mask from provided IP/Subnet - str'''
		return self.__lst2oct(self.__bin2dec(self.__invmask))

	def ipdecmask(self, n=0):
		'''IP with Decimal Mask for provided IP/Subnet,
		--> str
		
		:param n: nth number ip address from provided subnet.
		:param type: int
		'''
		try:
			return self[n] + "/" + str(self.mask)
		except:
			raise Exception(f'Invalid Input : detected')

	def ipbinmask(self, n=0):
		'''IP with Binary Mask for provided IP/Subnet,
		--> str
		
		:param n: nth number ip address from provided subnet.
		:param type: int
		'''
		try:
			return self[n] + " " + self.binmask
		except:
			raise Exception(f'Invalid Input : detected')

	def ipinvmask(self, n=0):
		'''IP with Inverse Mask for provided IP/Subnet,
		--> str
		
		:param n: nth number ip address from provided subnet.
		:param type: int
		'''
		try:
			return self[n] + " " + self.invmask
		except:
			raise Exception(f'Invalid Input : detected')

	@property
	def version(self):
		'''--> version number of IP Subnet - int'''
		return 4



# ------------------------------------------------------------------------------
# Routes Class
# ------------------------------------------------------------------------------
class Routes(object):
	''' Routing Table
	--> Routes object with all routes in dictionary

	:param hostname: device hostname
	:param type: str

	:param route_list: output of cisco sh route command in list format
	:param type: list

	:param route_file: feed text file of sh route output directly instead
	:param type: io/text file

	Properties
	----------
	routes: dictionary of route: routename

	See also
	---------
	get_prefix_desc: --> Prefix Description / str
	inTable --> checks is provided prefix in routes / bool
	outerPrefix --> outer prefix / str
	'''
	# object initializer
	def __init__(self, hostname, route_list=None, route_file=None):
		if route_file != None: route_list = text_to_List(route_file)
		self.__parse(route_list, hostname)

	def __getitem__(self, key):
		return self.routes[key]

	def __iter__(self):
		for k, v in self.routes.items():
			yield (k, v)

	@property
	def reversed_table(self):
		for k, v in reversed(self.routes.items()):
			yield (k, v)

	@property
	def routes(self):
		"""--> routes with its name"""
		return self._op_items

	def get_prefix_desc(self, prefix):
		'''Returns prefix description if available or returns for default route
		--> str

		:param prefix: ip prefix to search in output
		:param type: str
		'''
		pfxlst = []
		if isinstance(prefix, str):
			x = self.__check_in_table(addressing(prefix))[1]
			try:
				pfxlst.append(self[x])
				return pfxlst[0]
			except:
				print("prefixesNotinAnySubnet: Error")
				return None
		elif isinstance(prefix, IPv4):
			x = self.__check_in_table(prefix.subnet)
			pfxlst.append(self[x])
		elif isinstance(prefix, (list, tuple, set)):
			for p in prefix:
				px = self.get_prefix_desc(p)
				if px:
					pfxlst.append(px)
		else:
			raise Exception("INPUTERROR")
		if len(set(pfxlst)) == 1:
			return pfxlst[0]
		else:
			print("prefixesNotinSamesubnet: Error")

	def inTable(self, prefix):
		'''check if prefix is in routes table, return for Def.Route otherwise
		--> bool
		'''
		return self.__check_in_table(prefix)[0]

	def outerPrefix(self, prefix):
		'''check and return parent subnet of prefix in routes table, Def.Route else
		--> str
		'''
		return self.__check_in_table(prefix)[1]

	######################### LOCAL FUNCTIONS #########################

	# Helper for inTable and outerPrefix
	def __check_in_table(self, prefix):
		if not isinstance(prefix, (str, IPv4)):
			raise Exception("INPUTERROR")
		for k, v in self.reversed_table:
			if k == '0.0.0.0/0': continue
			if isSubset(prefix, k):
				return (True, k)
				break
		return (False, '0.0.0.0/0')

	# set routes in dictionary/ parser
	def __parse(self, route_list, hostname):
		headers = (
		"L - local", "C - connected", "S - static", "R - RIP", "M - mobile", "B - BGP",
		"D - EIGRP", "EX - EIGRP external", "O - OSPF", "IA - OSPF inter area", 
		"N1 - OSPF NSSA external type 1", "N2 - OSPF NSSA external type 2",
		"E1 - OSPF external type 1", "E2 - OSPF external type 2", "V - VPN",
		"i - IS-IS", "su - IS-IS summary", "L1 - IS-IS level-1", "L2 - IS-IS level-2",
		"ia - IS-IS inter area", "* - candidate default", "U - per-user static route",
		"o - ODR", "P - periodic downloaded static route", "+ - replicated route",
		"Gateway of last resort"
		)
		op_items = OrderedDict()
		for line in route_list:
			if blank_line(line): continue
			if hostname_line(line, hostname): continue
			if find_any(line, headers): continue
			if isSplittedRoute(line) == 0:
				spl = line.strip()
				continue
			if isSplittedRoute(line) == -1:
				line = spl + ' ' + line
			spl = line.split(",")
			if line.find('0.0.0.0 0.0.0.0') > -1:
				op_items['0.0.0.0/0'] = replace_dual_and_split(spl[1])[-1].strip()
				continue
			route = replace_dual_and_split(spl[0])[1]
			try:
				routeMask = binsubnet(replace_dual_and_split(spl[0])[2]).count('1')
			except:
				print(spl)
			routeDesc = replace_dual_and_split(spl[-1])[-1]
			op_items[route + '/' + str(routeMask)] = routeDesc.strip()
		self._op_items = op_items

