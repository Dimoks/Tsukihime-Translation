#!/bin/bash
for File in *.png; do
	echo Processing: "$File"
	magick "$File" -set colorspace sRGB "$File"
done
