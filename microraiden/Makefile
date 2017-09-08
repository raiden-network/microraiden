DATADIR:=microraiden/data

bandit:
	bandit -s B101 -r microraiden/

pylint:
	pylint microraiden/

ssl_cert:
	openssl req -x509 -newkey rsa:4096 -nodes -out $(DATADIR)/cert.pem -keyout $(DATADIR)/key.pem -days 365

flake8:
	flake8 microraiden/
