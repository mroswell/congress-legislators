#!/usr/bin/env python

# Add newly elected Members of Congress for the 113th Congress,
# and add new terms to Members of Congress that were reelected.

import csv
from collections import OrderedDict
from utils import load_data, save_data

senate_election_class = 1
at_large_districts = ['AK', 'AS', 'DC', 'DE', 'GU', 'MP', 'MT', 'ND', 'PR', 'SD', 'VI', 'VT', 'WY']

y = load_data("legislators-current.yaml")
y_historical = load_data("legislators-historical.yaml")

# Map GovTrack IDs to dicts. Track whether they are in the current or historical file.
by_id = { }
for m in y: by_id[m["id"]["govtrack"]] = (m, True)
for m in y_historical: by_id[m["id"]["govtrack"]] = (m, False)

# Sanity checking.
if False:
	w = csv.writer(open("house_senate_winners2.csv", "w"))
	w.writerow([f for f in ('state','seat','first','last','incumbent','party','middle','suffix','id','info')])
	for rec in csv.DictReader(open("house_senate_winners.csv")):
		rec["info"] = ""
		if rec["id"].strip() != "" and int(rec["id"]) in by_id:
			m = by_id[int(rec["id"])][0]
			if m["name"]["first"] != rec["first"]: rec["info"] += m["name"]["first"] + " "
			if m["name"]["last"] != rec["last"]: rec["info"] += m["name"]["last"] + " "
			if m["terms"][-1]["state"] != rec["state"]: rec["info"] += m["terms"][-1]["state"] + " "
			
			d = m["terms"][-1].get("district")
			d = { None: 0, 0: 1}.get(d, d)
			if str(d) != rec["seat"]: rec["info"] += str(m["terms"][-1].get("district", "X")) + " "
			
			if m["terms"][-1]["end"] != "2012-12-31": rec["info"] += m["terms"][-1]["end"] + " "
			
			if m["terms"][-1]["party"] != rec["party"]: rec["info"] += m["terms"][-1]["party"] + " "
			
		w.writerow([rec[f].encode("utf8") for f in ('state','seat','first','last','incumbent','party','middle','suffix','id','info')])
	
	raise ValueError()

# Process each election winner.
seen_members = set()
for rec in csv.DictReader(open("house_senate_winners.csv")):
	if rec["id"].strip() != "":
		# This is the reelection of someone that has already served in Congress.
		m, is_current = by_id[int(rec["id"])]
		seen_members.add(int(rec["id"]))

		if not is_current:
			# If this person is in the historical file, move them into the current file.
			if rec["incumbent"].strip() == "1": raise ValueError("Incumbent %d is in the historical file?!" % int(rec["id"]))
			y_historical.remove(m)
			y.append(m)
			
		else:
			# This person is in the current file. They must be continuing from a term that ends at the end.
			if m["terms"][-1]["end"] != '2012-12-31':
				raise ValueError("Most recent term doesn't end on December 31 of this year: %d" % int(rec["id"]))
			
	else:
		# This is a new individual. Create a new record for them.
		
		if rec["incumbent"].strip() == "1": raise ValueError("Incumbent does not have a govtrack ID?!")
		
		m = OrderedDict([
			("id", {}),
			("name", OrderedDict([
				("first", rec["first"]),
				("last", rec["last"]),
				])),
			("bio", {}),
			("terms", []),
		])
		for k in ('suffix', 'middle'):
			if rec[k].strip() != "":
				m["name"][k] = rec[k].strip()
			
		y.append(m)
			
	# Create a new term for this individual.
	
	term =  OrderedDict([
		("type", "sen" if int(rec["seat"]) == 0 else "rep"),
		("start", "2013-01-03"),
		("end", "2018-12-31" if int(rec["seat"]) == 0 else "2014-12-31"),
		("state", rec["state"]),
		("party", rec["party"]),
	])
	
	if int(rec["seat"]) == 0:
		term["class"] = senate_election_class
	else:
		d = int(rec["seat"])
		if rec["state"] in at_large_districts: d = 0 # it's coded in the file as 1, but we code as 0
		term["district"] = d
		
	# For incumbents, assume url, address, and similar fields are not changing.
	# Pull the forward from the individual's most recent term, which is always listed last.
	if len(m["terms"]) > 0:
		for field in ("url", "address", "phone", "fax", "contact_form", "office"):
			if field in m["terms"][-1]: term[field] = m["terms"][-1][field]

	# Append the new term.
	m["terms"].append(term)
	
# Move anyone else to the historical file.
for m in y:
	id = m.get('id', {}).get('govtrack')
	if id and id not in seen_members:
		y.remove(m)
		y_historical.append(m)

save_data(y, "legislators-current.yaml")
save_data(y_historical, "legislators-historical.yaml")