#!/bin/bash
cd ../..
echo "Packaging Python .zip package."
echo ""
python3 setup.py sdist --formats=zip
