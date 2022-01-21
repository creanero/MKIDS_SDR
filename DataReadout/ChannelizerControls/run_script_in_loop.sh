#!/bin/bash
for i in {1..10}
do
   python pulse_triggering.py
   echo "i = $i"
done
