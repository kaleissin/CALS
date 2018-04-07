SHELL := /bin/sh

PROJECT := CALS

SETTINGS_PATH := cals.site.settings
LOCALPATH := ./src
WSGI_PATH := $(LOCALPATH)/cals/site/
PYTHONPATH := $(LOCALPATH)/
SETTINGS := production
DJANGO_SETTINGS_MODULE = $(SETTINGS_PATH).$(SETTINGS)
DJANGO_POSTFIX := --settings=$(DJANGO_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
LOCAL_SETTINGS := local
DJANGO_LOCAL_SETTINGS_MODULE = $(SETTINGS_PATH).$(LOCAL_SETTINGS)
DJANGO_LOCAL_POSTFIX := --settings=$(DJANGO_LOCAL_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
TEST_SETTINGS := test
DJANGO_TEST_SETTINGS_MODULE = $(SETTINGS_PATH).$(TEST_SETTINGS)
DJANGO_POSTFIX := --settings=$(DJANGO_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
DJANGO_TEST_POSTFIX := --settings=$(DJANGO_TEST_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
PYTHON_BIN := $(VIRTUAL_ENV)/bin

.PHONY: clean showenv coverage test bootstrap pip virtualenv sdist virtual_env_set

.DEFAULT: virtual_env_set
	$(PYTHON_BIN)/django-admin.py $@ $(DJANGO_LOCAL_POSTFIX)

showenv:
	@echo 'Environment:'
	@echo '-----------------------'
	@$(PYTHON_BIN)/python3 -c "import sys; print 'sys.path:', sys.path"
	@echo 'PYTHONPATH:' $(PYTHONPATH)
	@echo 'PROJECT:' $(PROJECT)
	@echo 'DJANGO_SETTINGS_MODULE:' $(DJANGO_SETTINGS_MODULE)
	@echo 'DJANGO_LOCAL_SETTINGS_MODULE:' $(DJANGO_LOCAL_SETTINGS_MODULE)
	@echo 'DJANGO_TEST_SETTINGS_MODULE:' $(DJANGO_TEST_SETTINGS_MODULE)

showenv.all: showenv showenv.virtualenv showenv.site

showenv.virtualenv: virtual_env_set
	PATH := $(VIRTUAL_ENV)/bin:$(PATH)
	export $(PATH)
	@echo 'VIRTUAL_ENV:' $(VIRTUAL_ENV)
	@echo 'PATH:' $(PATH)

showenv.site: site_set
	@echo 'SITE:' $(SITE)

djangohelp: virtual_env_set
	$(PYTHON_BIN)/django-admin.py help $(DJANGO_POSTFIX)

collectstatic: virtual_env_set
	-mkdir -p .$(LOCALPATH)/static
	$(PYTHON_BIN)/django-admin.py collectstatic -c --noinput $(DJANGO_POSTFIX)

cmd: virtual_env_set
	$(PYTHON_BIN)/django-admin.py $(CMD) $(DJANGO_POSTFIX)

localcmd: virtual_env_set
	$(PYTHON_BIN)/django-admin.py $(CMD) $(DJANGO_LOCAL_POSTFIX)

refresh:
	touch $(WSGI_PATH)*wsgi.py

rsync:
	rsync -avz --checksum --exclude-from .gitignore --exclude-from .rsyncignore . ${REMOTE_URI}

compare:
	rsync -avz --checksum --dry-run --exclude-from .gitignore --exclude-from .rsyncignore . ${REMOTE_URI}

clean:
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -name "*.pyc" -print0 | xargs -0 rm -rf
	find . -name "*.bak" -print0 | xargs -0 rm -rf
	find . -name ".*.sw[p-z]" -print0 | xargs -0 rm -f
	find . -name "*~" -print0 | xargs -0 rm -f
	rm -rf htmlcov
	rm -rf .coverage
	rm -f archive-*.tgz

test: clean
	$(PYTHON_BIN)/django-admin.py test $(APP) $(DJANGO_TEST_POSTFIX)

coverage: clean virtual_env_set
	-$(PYTHON_BIN)/coverage run $(PYTHON_BIN)/django-admin.py test $(APP) $(DJANGO_TEST_POSTFIX)
	$(PYTHON_BIN)/coverage html --include="$(LOCALPATH)/*" --omit="*/admin.py,*/test*"

predeploy: test

register: virtual_env_set
	python3 setup.py register

sdist: virtual_env_set
	python3 setup.py sdist

upload: sdist virtual_env_set
	python3 setup.py upload
	make clean

bootstrap: virtualenv pip virtual_env_set

pip: requirements/$(SETTINGS).txt virtual_env_set
	pip install -r requirements/$(SETTINGS).txt

virtualenv:
	virtualenv --no-site-packages $(VIRTUAL_ENV)
	echo $(VIRTUAL_ENV)

batchbadge:
	PYTHONWARNINGS=ignore $(PYTHON_BIN)/django-admin.py batchbadge -v 0 $(DJANGO_POSTFIX)

batchbadge-verbose:
	$(PYTHON_BIN)/django-admin.py batchbadge $(DJANGO_POSTFIX)

tar:
	tar --posix -c -a -f archive-`date -u "+%Y%m%d%H%M%SZ"`.tgz  --exclude '__pycache__' --exclude 'archive-*' --exclude '*~' *

all: collectstatic refresh

