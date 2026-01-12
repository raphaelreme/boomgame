set -e

uv run pyinstaller BOOM.spec

BOOM_VERSION=$(uv run boom_version)

PACKAGE_NAME=boom_$BOOM_VERSION-1_all

mkdir -p $PACKAGE_NAME/usr/local/bin
mkdir -p $PACKAGE_NAME/usr/share/applications
mkdir -p $PACKAGE_NAME/DEBIAN

cp dist/BOOM $PACKAGE_NAME/usr/local/bin
cp -r boom/usr/share/BOOM $PACKAGE_NAME/usr/share

sed "s/<version>/$BOOM_VERSION/g" boom/DEBIAN/control.template >> $PACKAGE_NAME/DEBIAN/control
sed "s/<version>/$BOOM_VERSION/g" boom/usr/share/applications/BOOM.desktop.template >> $PACKAGE_NAME/usr/share/applications/BOOM.desktop

dpkg-deb --build --root-owner-group $PACKAGE_NAME


