from lxml import etree
import re
import os
import sys

if len(sys.argv) != 2:
	print("must be 2 args")
	exit(0)

filepath = sys.argv[1]
print("html file: ", filepath)
wfile = open(os.path.basename(filepath) + "-extract.txt", "w", encoding="utf8")

with open(filepath, encoding="utf8") as file:
	html = etree.HTML(file.read())
	html_data = html.xpath('//tr')
	print(len(html_data))
	for trow in html_data:
		cells = trow.xpath('td/text()')
		if len(cells) not in [4,5]:
			print("err row: ", trow.text, "num: ", len(cells))
			continue
		
		accent = re.findall(r'美:(/.*?/)', cells[2])
		if len(accent) == 1:
			accent = accent[0]
		else:
			print("err accent: ", cells[2], "No:", cells[0])
			accent = cells[2]
		if len(cells) == 4:
			wfile.write(f'{cells[1]}|{accent}|{cells[3]}\n')
		elif len(cells) == 5:
			wfile.write(f'{cells[1]}|{accent}|{cells[4]}\n')
		else:
			print("err row: ", trow.text, "num: ", len(cells))
