test:
	python3 -m unittest discover tests

assets/oxxa-api-v1.99.txt:
	# (tested with poppler-utils 0.62.0-2ubuntu2.12 pdftotext)
	pdftotext -eol unix -layout assets/oxxa-api-v1.99.pdf - | \
	  perl -pe 'BEGIN{undef $$/} s/\n\nVersie datum:[^\n]*\n\s+\d+\n//smg' | \
	  sed -e 's/ *\.\.\.\.\..* [0-9]*$$//;s/\f\([A-Z]\{3\}.*\)/\n## \1 ##/;s/\f/\n/g' \
	  >assets/oxxa-api-v1.99.txt
