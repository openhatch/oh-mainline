#!/bin/sh
set -x
set -e

PREFIX="."
while [ ! -d "$PREFIX/mysite" ]; do
    PREFIX="../$PREFIX"
done

cd "$PREFIX"
cp -f mysite/config-files/schema.xml parts/download_solr/example/solr/conf/schema.xml
cd parts/download_solr/example
java -jar start.jar
