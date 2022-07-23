#!/usr/bin/bash

# sample video:
# https://www.youtube.com/watch?v=bQQR8XMFj3g

# clean up
mkdir -p tmp_out
rm -f tmp_out/*.png
rm -f tmp_out/cropped_*.png

# decode video
ffmpeg -i $1  -vf "select=not(mod(n\,100))" -vsync 0 tmp_out/%03d.png

# crop images
for f in tmp_out/*.png; do
	echo $f;
	fbase=$(basename $f);
	convert $f -crop +0+390 tmp_out/cropped_$fbase
done

# merge together
convert tmp_out/cropped_*.png -append tmp_out/final.png
