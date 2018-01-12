DATADIR:=microraiden/data

all: webui flake8

bandit:
	bandit -s B101 -r microraiden/

pylint:
	pylint microraiden/

ssl_cert:
	openssl req -x509 -newkey rsa:4096 -nodes -out $(DATADIR)/cert.pem -keyout $(DATADIR)/key.pem -days 365

flake8:
	flake8 microraiden/

clean:
	python setup.py clean --all

mrproper:
	rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info

webui:
	python setup.py compile_webui

docs:
	cd microraiden/webui/microraiden/ && npm run docs
