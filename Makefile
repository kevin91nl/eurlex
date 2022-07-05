compile:
	-rm -rf dist
	python setup.py sdist bdist_wheel
upload_test:
	python3 -m twine upload --repository testpypi dist/* --skip-existing
upload_prod:
	python3 -m twine upload dist/* --skip-existing
install_test:
	python -m pip install --upgrade --index-url https://test.pypi.org/simple/ --no-deps eurlex
install_prod:
	python -m pip install --upgrade --no-deps eurlex
deploy_test: compile upload_test install_test
deploy_prod: compile upload_prod install_prod
deploy: compile upload_test upload_prod install_prod