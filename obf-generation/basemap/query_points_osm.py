#!/usr/bin/python
import psycopg2
import sys
import pprint
import re

def num(s, df):
	if s is None:
		return df
	try:
		return int(s)
	except ValueError:
		try:
			return float(s)
		except ValueError:
			return df

def esc(s):
	return s.replace("\"", "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace("'","&apos;")

def process_points(cond, filename, array):
	f = open(filename,'w')
	conn_string = "host='127.0.0.1' dbname='gis' user='gisuser' password='gisuser' port='5432'"
	f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	f.write('<osm version="0.5">\n')
 
	conn = psycopg2.connect(conn_string)
	cursor = conn.cursor()
	shift = 3
	queryFields = ""
	names = ['name:ar',	'name:be',	'name:ca',	'name:cs',	'name:da',	'name:de',	'name:el',	
				    'name:es',	'name:fi',	'name:fr',	'name:he',	'name:hi',	'name:hr',	
				    'name:hu',	'name:it',	'name:ja',	'name:ko',	'name:lt',	'name:lv',	'name:nl',	
				    'name:pl',	'name:ro',	'name:ru',	'name:sk',	'name:sl',	'name:sv',	
				    'name:sw',	'name:zh']
	for tag in array:
		if tag == 'name:en':
			tag = 'tags->\'name:en\' as "name:en"'
		if tag == 'iata':
			tag = 'tags->\'iata\' as "iata"'
		if tag == 'icao':
			tag = 'tags->\'icao\' as "icao"'
		if tag == 'faa':
			tag = 'tags->\'faa\' as "faa"'
		if tag == 'natural':
			tag = '"natural"'
		if tag == 'seamark:type':
			tag = 'tags->\'seamark:type\' as "seamark:type"'
		if tag == 'abandoned':
			tag = 'tags->\'abandoned\' as "abandoned"'
		queryFields += ", " + tag

	for nm in names:
		array.append(nm)
		queryFields += ", tags->\'" + nm + "\' as \"" + nm + "\""
		
	sql = "select ST_AsText(ST_Transform(way,94326)), osm_id, population " + queryFields + \
	      " from planet_osm_point where " + cond + ";"
	      # "LIMIT 2"
	#print sql
	cursor.execute(sql)
 
	node_id =-1000
	parse = re.compile('(-?[\d|\.]+)\s(-?[\d|\.]+)')
	for row in cursor:
		node_id = row[1] #node_id - 1
		match = parse.search(row[0])
		xml = '\n<node id="%s" lat="%s" lon="%s">\n' % (node_id, match.groups()[1], match.groups()[0])
		base = shift
		while base - shift < len(array):
			if row[base] is not None:
				tagName = array[base - shift]
				value = esc(row[base])
				if tagName == "place" and value == "city" :
					pop = num(row[2], 0)
					if pop > 500000	:
						xml += '\t<tag k="%s" v="%s" />\n' % ("osmand_place_basemap", "city")
				# if tagName == 'name' and row[base+1] is not None and len(row[base+1]) > 0 :
					# value = '' # write name:en instead of name
				# if tagName == 'name:en' and len(value) > 0 :
					# tagName = 'name'
				

				if len(value) > 0 :
					xml += '\t<tag k="%s" v="%s" />\n' % (tagName, value)
			base = base + 1
		xml += '</node>'	
		f.write(xml)
	f.write('</osm>')

if __name__ == "__main__":
	process_points("place in ('sea','ocean','state', 'country') "
				   " or \"natural\" in ('peak', 'cave_entrance', 'rock', 'waterfall', 'cape', 'volcano', 'stream', 'strait', 'reef')"
				   " or tourism in ('alpine_hut') "
				   " or tags->'seamark:type' in ('light_major') "
				   " or tags->'seamark:type' in ('harbour') "
				   " or tags->'abandoned' in ('yes') "
				   " or aeroway in ('aerodrome', 'airport')", 'points.osm', 
				   ['name', 'name:en',
				    'ref', 'ele', 'place','natural', 'seamark:type', 'abandoned', 'aeroway', 'tourism', 'iata', 'icao', 'faa'])
	process_points("place in ('city','town') ", 'cities.osm', ['name', 'name:en', 'place', 'capital'])
