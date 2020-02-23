##STOP - Make sure you updated the version in the setup.py to match the version in github to be uploaded.
rm dist/*
python setup.py sdist
echo "RUN: twine upload dist/{VERSION}.tar.gz"