#!python
# ripe.py
# Real IP Extractor
# Builds table mapping real server IPs to CSM vservers/serverfarms

import re

# Path of csm config file
csmFile = '/Users/nlucent/Downloads/dpwsus01-msfc'

# Indicates a new configuration block
newblockStr = '!\n'

# determine where we are in the file
newBlock = True
inSfarm = False;
inVserver = False;

# serverfarm RE
re1='(\\s+)'	# White Space 1
re2='(serverfarm)'	# Word 1
re3='(\\s+)'	# White Space 2
re4='((?:[a-z][a-z0-9_-]*))'

sfarmRE = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)

#serverfarm with backup
re5='(\\s+)'
re6='(backup)'
re7='(\\s+)'
re8='((?:[a-z][a-z0-9_-]*))'
sfarmBackupRE = re.compile(re1+re2+re3+re4+re5+re6+re7+re8,re.IGNORECASE|re.DOTALL)

# reals RE
re1='(\\s+)'	# White Space 1
re2='(real)'	# Word 1
re3='(\\s+)'	# White Space 2
re4='((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))(?![\\d])'	# IPv4 IP Address

realRE = re.compile(re1+re2+re3+re4, re.IGNORECASE|re.DOTALL)

# vserver RE
re1='(\\s+)'	# White Space 1
re2='(vserver)'	# Word 1
re3='(\\s+)'	# White Space 2
re4='((?:[a-z][a-z0-9_-]*))'

vserverRE = re.compile(re1+re2+re3+re4, re.IGNORECASE|re.DOTALL)

# virtual RE
re1='(\\s+)'	# White Space 1
re2='(virtual)'	# Word 1
re3='(\\s+)'	# White Space 2
re4='((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))(?![\\d])'	# IPv4 IP Address

virtualRE = re.compile(re1+re2+re3+re4, re.IGNORECASE|re.DOTALL)

#virtual serverfarm
re1='(\\s+)'	# White Space 1
re2='(serverfarm)'	# Word 1
re3='(\\s+)'	# White Space 2
re4='((?:[a-z][a-z0-9_-]*))'

vsfRE = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)


sfarmData = {}
vserverData = {}
csmData = {}


f = open(csmFile, 'r')

# load file into memory since its rewritten throughout the day
config = f.readlines()
f.close()

# set newBlock = TRUE when newblockStr found
for line in config:
	
	# See if we are starting a new block
	if line == newblockStr:
		newBlock = True
		inSfarm = False
		inVserver = False
		continue
	else:
		newBlock = False

	# check for vserver
	v = vserverRE.search(line)
	if v:
		inVserver = True
		vserverGrp = v.group(4)							# grab vserver name
		vserverData[vserverGrp] = []					# empty entry
		continue
		
	if inVserver:
		# Need to pull both virtual, and serverfarm val
		vr = virtualRE.search(line)						# found virtual line in vserver block
		vrs = vsfRE.search(line)
		
		if vr:
			curVr = vr.group(4)
			vserverData[vserverGrp] = [curVr]				# vserverdata = { vservergrp: [virtualip] }
		if vrs:
			vsfarm = vrs.group(4)
			vserverData[vserverGrp].append(vsfarm)

	# Check for serverfarm
	s = sfarmRE.search(line)
	sb = sfarmBackupRE.search(line)
	if s and not inVserver:												# Found serverfarm line
		inSfarm = True
		farmName = s.group(4)							# grab farmname
		sfarmData[farmName] = []						# Create emtpy list
		continue										# next line
	
	if sb and not inVserver:
		inSfarm = True
		fname1 = sb.group(4)
		fname2 = sb.group(8)
		sfarmData[fname1] = []
		sfarmData[fname2] = []
		
	# Check if we are in serverfarm block
	if inSfarm and not inVserver:
		r = realRE.search(line)							# search for real line
		if r:											# found
			curReal = r.group(4)						# get IP of real
			sfarmData[farmName].append(curReal)			# append real to sfarm
			continue
		
for key in vserverData:
	curfarm = vserverData[key]
	if len(curfarm) == 2:
		ip,farmname = curfarm
		csmData[ip] = sfarmData.get(farmname)
			


#print vserverData
#print sfarmData

			
		

	

		
	
				
			
		
			
		
			
			
			
		
		