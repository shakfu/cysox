gcc -o eg-static -I./include -L./lib-static \
	-lsox 		\
	-lFLAC 		\
	-lao 		\
	-lsndfile 	\
	-lvorbis 	\
	-lvorbisenc	\
	-lvorbisfile \
	-lpng16   	\
	-lltdl 		\
	-lmad 		\
	-lmp3lame 	\
	-logg 		\
	-lopus 		\
	-lopusfile 	\
	-lz 		\
	-lopencore-amrnb \
	-lopencore-amrwb \
	-framework CoreAudio \
	example.c
