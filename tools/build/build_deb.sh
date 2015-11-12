#!/bin/bash
cd ../..

mv requirements.txt _requirements.txt
touch requirements.txt

echo ""
echo "Packaging .DEB now..."
echo ""
python3 setup.py --command-packages=stdeb.command sdist_dsc -i --with-python2=True --with-python3=True --dist-dir=deb_dist --extra-cfg-file=debian.cfg --ignore-install-requires 

echo ""
echo "Copying post install script..."
echo ""
#cp -Rv debian/* deb_dist/*/debian/
#chmod +x deb_dist/*/debian/*postinst

echo ""
echo "Rebuilding package with postinst script..."
echo ""
cd deb_dist/*/
dpkg-buildpackage -rfakeroot -uc -us -b
cd ../..

echo ""
echo ".DEB creation completed"
echo ""
[ -d build ] || mkdir build
mv `ls deb_dist/*.deb` ./build/
echo "   .deb moved into 'build' folder : "
ls build/*.deb
echo ""

cp _requirements.txt requirements.txt
rm _requirements.txt

cd tools/build/
source ./clean_deb.sh
