DATADIR:=raiden_mps/data

bandit:
	bandit -s B101 -r raiden_mps/

pylint:
	pylint raiden_mps/

ssl_cert:
	openssl req -x509 -newkey rsa:4096 -nodes -out $(DATADIR)/cert.pem -keyout $(DATADIR)/key.pem -days 365
