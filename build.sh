#!/bin/bash

rm -R work
rm -R out
mkarchiso -v -w work -o out .
