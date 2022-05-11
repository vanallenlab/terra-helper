#!/bin/bash

HANDLE=$1

# WARNING: OBJECT REMOVAL CANNOT BE UNDONE
# Deletes all files listed in the passed HANDLE
# The passed file should be a simple text file, listing one file on google cloud per row

cat "$HANDLE" | gsutil -m rm -I
