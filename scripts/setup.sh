
INCLUDE_DIR=./include
LIB_DIR=./lib

function update_lib() {
	DEP_DIR=`brew --prefix $1`
	DEP_INCLUDE_DIR=${DEP_DIR}/include
	DEP_LIB_DIR=${DEP_DIR}/lib
	cp -rf ${DEP_INCLUDE_DIR}/* ${INCLUDE_DIR}
	cp -af ${DEP_LIB_DIR}/*.a ${LIB_DIR}
	cp -af ${DEP_LIB_DIR}/*.dylib ${LIB_DIR}
}


mkdir -p lib include

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

rm -f \
	lib/libpng.a \
	lib/libsyn123.a \
	lib/libout123.a \
	lib/libFLAC++.a \
	lib/libopusurl.a
