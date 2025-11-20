#!/bin/bash
[ ! -d "thumb" ] && mkdir "thumb"
for File in *.png; do
	echo Processing: "$File"
	magick "$File" -resize 16.69% "thumb/$File"
done
