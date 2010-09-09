#!/usr/bin/python

"""
biblio.py - easy bibliography search tool

Vassilios Karakoidas (2008) - vassilios.karakoidas@gmail.com
"""

import os
import os.path
import sys
import re

from bibtex import bibparse

# Command-line Dispatcher
class CmdDispatcher:
	def __init__(self, args):
		self.__args = args
		self.__bibfiles = {}
		self.__repos = []
		
		# works only for posix based systems so far
		# check for .biblio-py
		self.__homedir = os.path.expanduser('~')
		self.__configdir = "%s/.biblio-py" % ( self.__homedir, )
		if not os.access(self.__configdir, os.F_OK):
			print "ERROR: directory %s does not exist!!! Creating basic configuration" % ( self.__configdir, )
			os.mkdir(self.__configdir)
			print "Created %s directory " % ( self.__configdir, )
			print "Use 'addpath' directive to add new .bib containing directories"
			os.exit(1)

		# search for repositories
		self.__repconf_file = "%s/repositories" % ( self.__configdir, )
		if not os.access(self.__repconf_file, os.F_OK):
			print "ERROR: cannot find repositories file, creating a default file"
			fp = open(self.__repconf_file, "w")
			fp.close()
		
		try:
			repconf = open(self.__repconf_file, "r")
			for line in repconf:
				self.__repos.append(line.strip())
			repconf.close()
		except IOError:
			print "ERROR: %s does not exist!" % ( self.__repconf_file, )
			print "Use 'addpath' directive to add new .bib containing directories"
			os.exit(1)

		# scan the directories / bibfiles
		files = []
		for r in self.__repos:
			rfiles = scan_dirs(r)
			files.extend(rfiles)
		for f in files:
			self.__bibfiles[f] = bibparse.parse_bib(f)

	def getBibfiles(self):
		return self.__bibfiles

	def search(self, keyword):
		results = []

		for (k, v) in self.__bibfiles.iteritems():
			for val in v:
				if val.search([keyword]):
					results.append(val)

		return results
		
	def doSearch(self):
		for (k, v) in self.__bibfiles.iteritems():
			for val in v:
				if val.search(self.__args):
					print val

	def doCount(self):
		total = 0				
		
		for k, v in self.__bibfiles.iteritems():
			print 'Processed %s ... found %d entries'% ( k, len(v) )
			total = total + len(v)
		
		print '\nTotal: %d entries in %d files' % ( total, len(self.__bibfiles.keys()) )
	
	def __getKey(self, key):
		for k, v in self.__bibfiles.iteritems():
			for val in v:
				if val.getKey(key):
					return val.export()
		
		return ""
	
	def doExport(self):
		for exp_key in self.__args:
			print self.__getKey(exp_key)
		
	def doExpfile(self):
		filename = self.__args[0]
		self.__args = []
		# TODO: add unicode support!
		fp = open(filename, "r")
		for line in fp:
			self.__args.append(line.strip())
		fp.close()
		self.doExport()
		
	def doTexmode(self):
		keys = scan_tex_files(self.__args)
		self.__args = keys
		self.doExport()
		
	def doAddpath(self):
		self.__repos.append(self.__args[0])
		
		try:
			repofile = open(self.__repconf_file, "w")
			for r in self.__repos:
				repofile.write("%s\n" % ( r,))
			repofile.close()
		except IOError:
			print "Cannot write %s" % ( self.__repconf_file, )

	def doKey(self):
		self.doExport()
		
	def doList(self):
		for r in self.__repos:
			status = "OK"			
			if not os.access(r, os.F_OK):
				status = "ERROR"
			print " %s - (%s)" % ( r, status )

	def doHelp(self):
		print """\nbibliography utility v0.55 (code name: sanity)

usage: biblio.py <directive> <arguments>

key                - Export a specific key
addpath            - Add a repository path
list               - List repository paths (also checks their validity)
search <keyword>   - search ALL bibtex tags for specific entries
count              - Count all bibtex entries and print statistics
export <keys...>   - Extracts the selected keys
expfile <file>     - Read the selected keys from a specified file and export the entries
texmode <files...> - Search a latex 
help               - Prints the online help"""

# scans the paths
def scan_dirs(path):
	res = []
	
	for root, dirs, files in os.walk(path):
		if '.svn' in dirs:
			dirs.remove('.svn')
		for d in dirs:
			fd = os.path.join(root, d)
			if os.path.islink(fd):
				res_two = scan_dirs(fd)
				res.extend(res_two)
		for f in files:
			if f.endswith('.bib'):
				res.append(os.path.join(root, f))

	return res
	
def scan_tex_files(files):
	keys = []
	
	for tf in files:
		tf_desc = open(tf, 'r')
		
		for line in tf_desc:
			mr_list = re.findall('cite{([^}]+)}', line.strip())
			if len(mr_list) > 0:
				for mr in mr_list:
					try:
						mr.index(',')
						for k in mr.split(','):
							try:
								keys.index(k.strip())							
							except (ValueError):
								keys.append(k.strip())
					except (ValueError):
						try:
							keys.index(mr.strip())
						except (ValueError):
							keys.append(mr.strip())
		
		tf_desc.close()
	
	return keys

# the program starts here
def main():
	if len(sys.argv) < 2:
		cdisp = CmdDispatcher(['biblio.py', 'help'])
		cdisp.doHelp()
		return
	starting_path = os.path.abspath(os.path.dirname(sys.argv[0]))
	# Set python's path to look for modules under our toplevel dir structure
	sys.path.append(starting_path)
	# initialise the dispatcher and execute
	cdisp = CmdDispatcher(sys.argv[2:])
	getattr(cdisp,"do" + sys.argv[1].title())()

# call the main function
if __name__ == '__main__':
	main()
