#!/bin/bash
for i in {1..64}
do
   python justsaveIQdata.py
   echo "i = $i"
done
