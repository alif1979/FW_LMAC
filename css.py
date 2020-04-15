
from general import *

# ----------------------------------------------------------------------------------------
# Style Maps
# ----------------------------------------------------------------------------------------
def h_font_bg_color_schema(shtName):
	h_font_color_schema_maps = {CHANGE_PROCEDURE: h_range_font_color_1_2, 
						FALLBACK_PROCEDURE: h_range_font_color_1_2, 
						SH_RUN: h_range_font_color_3_None}
	return h_font_color_schema_maps[shtName]

def v_bg_color_schema(shtName):
	v_bg_color_schema_maps = {CHANGE_PROCEDURE: h_range_bg_color_1_2, 
						FALLBACK_PROCEDURE: h_range_bg_color_1_2, 
						SH_RUN: h_range_bg_color_3}
	return v_bg_color_schema_maps[shtName]

# ----------------------------------------------------------------------------------------
# color styling
# ----------------------------------------------------------------------------------------
def h_range_font_color_1_2(val):
	"""-->Font Color Scheme1 - CHG/RBK tabs"""	
	color = 'black'
	if val[CONTENT].startswith("no "): color = 'red'
	if val[CONTENT].startswith("access-list"): color = 'blue'
	if found(val[CONTENT], "object"):
		color = 'red' if val[CONTENT].lstrip()[:3] == "no " else 'blue'
	return ['color: white','color: black','color: black','color: black',
			f'color: {color}', f'color: {color}']

def h_range_bg_color_3(val):
	"""-->Background color scheme1 - sh rn Tab"""
	colorpre, colorpost = 'white', 'white'
	pr = val["Pre"].strip()
	po = val["Post"].strip()
	if pr == po:
		pass
	elif not po:
		colorpost = 'yellow'
	elif not pr:
		colorpre = 'yellow'
	else:
		colorpre = 'yellow'
		colorpost = 'red'
	return [f'background-color: {colorpre}', f'background-color: {colorpost}', 
			f'background-color: white']

def h_range_bg_color_1_2(val):
	"""background color schema for columns in rows between _min/_max range"""
	c_scheme = {'a': '#cccccc', 'w': 'None', 'y': 'yellow', 'g': 'green'}
	color = []
	for i, v in enumerate(val):
		c = 'background-color: None'
		if i in (3,4,5):
			c = f'background-color: {c_scheme.get(val["."], None)}'
		color.append(c)
	return color

def h_range_font_color_3_None(val):
	"""background color schema for N/A Tabs """
	return [ f'color: black' for v in val]
# ----------------------------------------------------------------------------------------
