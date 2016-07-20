#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR
cd ../..
echo "Printing ${2}"
./selphy/selphy --printer_ip $1 $2
rm $2
popd