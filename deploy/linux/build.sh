set -e

uv run pyinstaller BOOM.spec

PACKAGE_NAME=boom_$(boom_version)-1_all

mkdir -p $PACKAGE_NAME/usr/local/bin
mkdir -p $PACKAGE_NAME/usr/share/applications
mkdir -p $PACKAGE_NAME/DEBIAN

cp dist/BOOM $PACKAGE_NAME/usr/local/bin
cp -r boom/usr/share/BOOM $PACKAGE_NAME/usr/share

sed "s/<version>/$(boom_version)/g" boom/DEBIAN/control.template >> $PACKAGE_NAME/DEBIAN/control
sed "s/<version>/$(boom_version)/g" boom/usr/share/applications/BOOM.desktop.template >> $PACKAGE_NAME/usr/share/applications/BOOM.desktop

dpkg-deb --build --root-owner-group $PACKAGE_NAME


