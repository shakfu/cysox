
INCLUDE_DIR=./include
LIB_DIR=./lib

function update_sox() {
	SOX_DIR=`brew --prefix sox`
	SOX_INCLUDE_DIR=${SOX_DIR}/include
	SOX_LIB_DIR=${SOX_DIR}/lib
	cp ${SOX_INCLUDE_DIR}/sox.h ${INCLUDE_DIR}
	cp ${SOX_LIB_DIR}/libsox.a ${LIB_DIR}
}

# --- dependencies

function update_lib() {
	DEP_DIR=`brew --prefix $1`
	DEP_INCLUDE_DIR=${DEP_DIR}/include
	DEP_LIB_DIR=${DEP_DIR}/lib
	cp -rf ${DEP_INCLUDE_DIR}/* ${INCLUDE_DIR}
	cp -f ${DEP_LIB_DIR}/*.a ${LIB_DIR}
}

update_lib sox
update_lib flac
update_lib lame
update_lib mpg123
update_lib libogg
update_lib libsndfile
update_lib opus
update_lib opusfile
update_lib libvorbis
update_lib libpng
update_lib mad





# /opt/homebrew/opt/sox/lib/libsox.3.dylib (compatibility version 4.0.0, current version 4.0.0)

# /opt/homebrew/opt/flac/lib/libFLAC.14.dylib (compatibility version 15.0.0, current version 15.0.0)
# /opt/homebrew/opt/lame/lib/libmp3lame.0.dylib (compatibility version 1.0.0, current version 1.0.0)
# /opt/homebrew/opt/libogg/lib/libogg.0.dylib (compatibility version 0.0.0, current version 0.8.5)
# /opt/homebrew/opt/libpng/lib/libpng16.16.dylib (compatibility version 64.0.0, current version 64.0.0)
# /opt/homebrew/opt/libsndfile/lib/libsndfile.1.dylib (compatibility version 2.0.0, current version 2.37.0)
# /opt/homebrew/opt/libvorbis/lib/libvorbis.0.dylib (compatibility version 5.0.0, current version 5.9.0)
# /opt/homebrew/opt/libvorbis/lib/libvorbisenc.2.dylib (compatibility version 3.0.0, current version 3.12.0)
# /opt/homebrew/opt/libvorbis/lib/libvorbisfile.3.dylib (compatibility version 7.0.0, current version 7.8.0)
# /opt/homebrew/opt/mad/lib/libmad.0.dylib (compatibility version 3.0.0, current version 3.1.0)
# /opt/homebrew/opt/opusfile/lib/libopusfile.0.dylib (compatibility version 5.0.0, current version 5.5.0)

# /usr/lib/libz.1.dylib (compatibility version 1.0.0, current version 1.2.12)
# /System/Library/Frameworks/CoreAudio.framework/Versions/A/CoreAudio (compatibility version 1.0.0, current version 1.0.0)
# /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1351.0.0)