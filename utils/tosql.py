#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	A utility script to convert the Datuk dictionary corpus
	to import ready SQL

	Requires DatukParser.py

	Usage (tosql.py input_file output_file):
	~$ python tosql.py ../corpus/datuk.corpus ../corpus/datuk.sql

	License: GNU GPLv3

	Kailash Nadh, http://nadh.in
	May 2013
"""


import sys, codecs
from DatukParser import DatukParser

class DatukSQL:
	entries = None
	fp = None
	cache = {}

	# buffer limit for entries in a single insert statement
	insert_buffer = 1000

	# table schema
	schema = """
		# Generated by tosql.py - http://olam.in/corpus/datuk

		SET NAMES 'utf8';

		DROP TABLE IF EXISTS `word`;
		CREATE TABLE IF NOT EXISTS `word` (
		  `id` int(10) NOT NULL AUTO_INCREMENT,
		  `word` varchar(500) NOT NULL DEFAULT '',
		  `letter` varchar(20) NOT NULL DEFAULT '',
		  `root` varchar(500) NOT NULL,
		  `literal` varchar(500) NOT NULL,
		  PRIMARY KEY (`id`)
		) ENGINE=MyISAM DEFAULT CHARSET=utf8;

		DROP TABLE IF EXISTS `definition`;
		CREATE TABLE IF NOT EXISTS `definition` (
		  `id` int(10) NOT NULL AUTO_INCREMENT,
		  `definition` varchar(3000) NOT NULL,
		  PRIMARY KEY (`id`)
		) ENGINE=MyISAM DEFAULT CHARSET=utf8;

		DROP TABLE IF EXISTS `relation`;
		CREATE TABLE IF NOT EXISTS `relation` (
		  `id` int(10) NOT NULL AUTO_INCREMENT,
		  `id_word` int(10) NOT NULL DEFAULT '0',
		  `id_definition` int(10) NOT NULL DEFAULT '0',
		  `rtype` varchar(150) NOT NULL DEFAULT '-',
		  PRIMARY KEY (`id`),
		  UNIQUE KEY `id_rel` (`id_word`,`id_definition`,`rtype`)
		) ENGINE=MyISAM DEFAULT CHARSET=utf8;

	"""

	# SQL insert heads
	insert_heads = {
		"word": "letter, word, root, literal, id",
		"definition": "id, definition",
		"relation": "id_word, id_definition, rtype"
	}

	def __init__(self, infile, outfile):

		# get the corpus data
		print("Parsing corpus")
		try:
			parser = DatukParser(infile)
			self.entries = parser.get_all()
		except:
			print("Could not read input file")
			raise

		# ready the output file
		try:
			self.fp = codecs.open(outfile, encoding = 'utf-8', errors = 'ignore',  mode='w')
			self.fp.write(self.schema)
		except:
			print("Can't write to output file")
			raise

		for table in self.insert_heads:
			self.cache[table] = []

	def convert(self):
		print("Compiling")
		self._prepare()

		print("Writing")
		# write sql per table
		for table in self.cache:
			limit = len(self.cache[table]) / self.insert_buffer

			# write insert statements based on the insert buffer
			n = 0
			next = 0
			for n in range(0, limit):
				next = n*self.insert_buffer + self.insert_buffer
				self._flush(table, self.cache[table][n*self.insert_buffer : next])

			# flush the remaining ones
			self._flush(table, self.cache[table][next:])

		print("Done. Wrote " + \
				str(len(self.cache['word'])) + " words, " + \
				str(len(self.cache['definition']))) + " definitions, " + \
				str(len(self.cache['relation'])) + " relations"


	def _prepare(self):
		"""Prepare the data, words, definitions, their relations and ids"""

		# == write the words sql
		for entry in self.entries:
			self.cache['word'].append( "('" + "', '".join([self._escape(p) for p in entry[0:5] ]) + "')" )


		# == collect all unique definitions
		definitions = {}
		d = 1
		for entry in self.entries:
			for defn in entry.definitions:
				if defn.definition not in definitions:
					definitions[defn.definition] = d
					d+=1

		# == write the definitions
		for defn in definitions.keys():
			self.cache['definition'].append( "(" + str(definitions[defn]) + ", '" + self._escape(defn) +  "')" )


		# == compile word->definition relationships
		relations = []
		for entry in self.entries:
			for defn in entry.definitions:
				relations.append([entry.id, str(definitions[defn.definition]), "-" if not defn.type else self._escape(defn.type)])

		# == write relationships
		for rel in relations:
			self.cache['relation'].append( "('" + "', '".join(rel) + "')" )

	def _flush(self, table, rows):
		"""Write SQL chunks to file"""

		sql = "INSERT INTO " + table + " (" + self.insert_heads[table] + ") VALUES\n"
		sql += ",\n".join(rows) + ';'
		sql += "\n\n"

		self.fp.write(sql)
		pass

	def _escape(self, piece):
		"""MySQL escape"""

		return piece.replace("'", r"\'")

# ===

def main():
	if (len(sys.argv) != 3):
		print "Error: Need two arguments, input file and output file"
		quit()

	infile = sys.argv[1]
	outfile = sys.argv[2]

	tosql = DatukSQL(infile, outfile)
	tosql.convert()

if __name__ == "__main__":
	main()