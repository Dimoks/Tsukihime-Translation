#!/bin/bash
for File in *.JPG; do
	basename="${File%.*}.png"
	lowername="${basename,,}"
	echo Processing: "$File"
	magick "$File" -colorspace RGB -resize 16.69%% -colorspace sRGB "../allpac_textures/$lowername"
done
