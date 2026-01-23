cmake_minimum_required(VERSION 3.15...3.30)
project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES C)

# Find Python
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

# Platform detection
if(APPLE)
    set(IS_MACOS TRUE)
elseif(UNIX AND NOT APPLE)
    set(IS_LINUX TRUE)
elseif(WIN32)
    set(IS_WINDOWS TRUE)
endif()

# Debug mode
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(DEBUG TRUE)
else()
    set(DEBUG FALSE)
endif()

# Static linking option (defaults to ON for macOS, OFF for others)
option(STATIC "Use static linking" $<IF:$<BOOL:${IS_MACOS}>,ON,OFF>)
if(IS_MACOS AND NOT DEFINED STATIC)
    set(STATIC ON)
endif()
if(DEFINED ENV{STATIC} AND "$ENV{STATIC}" STREQUAL "1")
    set(STATIC ON)
endif()

# Generate sox.c from sox.pyx using Cython
add_custom_command(
    OUTPUT sox.c
    COMMAND Python::Interpreter -m cython
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/sox.pyx"
        --output-file sox.c
    DEPENDS
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/sox.pyx"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/sox.pxd"
    COMMENT "Generating sox.c from sox.pyx"
)

# Create the extension module (named _sox internally to avoid conflict with libsox)
python_add_library(_sox MODULE sox.c WITH_SOABI)

# Set the output name to "sox" (the actual module name users import)
set_target_properties(_sox PROPERTIES OUTPUT_NAME "sox")

# Include directories
target_include_directories(_sox PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")

# Platform-specific configuration
if(IS_MACOS)
    # macOS configuration
    set(LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/lib")

    if(STATIC)
        # Static linking using imported libraries to avoid target name conflicts
        # Create imported static library for libsox (named libsox_static to avoid conflict)
        add_library(libsox_static STATIC IMPORTED)
        set_target_properties(libsox_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libsox.a")

        add_library(libsndfile_static STATIC IMPORTED)
        set_target_properties(libsndfile_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libsndfile.a")

        add_library(libflac_static STATIC IMPORTED)
        set_target_properties(libflac_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libFLAC.a")

        add_library(libopus_static STATIC IMPORTED)
        set_target_properties(libopus_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libopus.a")

        add_library(libopusfile_static STATIC IMPORTED)
        set_target_properties(libopusfile_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libopusfile.a")

        add_library(libmp3lame_static STATIC IMPORTED)
        set_target_properties(libmp3lame_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libmp3lame.a")

        add_library(libmad_static STATIC IMPORTED)
        set_target_properties(libmad_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libmad.a")

        add_library(libmpg123_static STATIC IMPORTED)
        set_target_properties(libmpg123_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libmpg123.a")

        add_library(libvorbis_static STATIC IMPORTED)
        set_target_properties(libvorbis_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libvorbis.a")

        add_library(libvorbisfile_static STATIC IMPORTED)
        set_target_properties(libvorbisfile_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libvorbisfile.a")

        add_library(libvorbisenc_static STATIC IMPORTED)
        set_target_properties(libvorbisenc_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libvorbisenc.a")

        add_library(libogg_static STATIC IMPORTED)
        set_target_properties(libogg_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libogg.a")

        add_library(libpng16_static STATIC IMPORTED)
        set_target_properties(libpng16_static PROPERTIES IMPORTED_LOCATION "${LIB_DIR}/libpng16.a")

        # Link in dependency order
        target_link_libraries(_sox PRIVATE
            libsox_static
            libsndfile_static
            libflac_static
            libopus_static
            libopusfile_static
            libmp3lame_static
            libmad_static
            libmpg123_static
            libvorbis_static
            libvorbisfile_static
            libvorbisenc_static
            libogg_static
            libpng16_static
        )
    else()
        # Dynamic linking
        target_link_directories(_sox PRIVATE "${LIB_DIR}")
        target_link_libraries(_sox PRIVATE
            -lsox -lsndfile -lFLAC -lopus -lmp3lame
            -lvorbis -lvorbisfile -lvorbisenc -lpng16
        )
    endif()

    # Always need zlib and CoreAudio framework
    target_link_libraries(_sox PRIVATE -lz)
    target_link_libraries(_sox PRIVATE "-framework CoreAudio")

    if(DEBUG)
        target_compile_options(_sox PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(_sox PRIVATE -fsanitize=address)
        target_compile_definitions(_sox PRIVATE DEBUG DEBUG_EFFECTS_CHAIN=1)
    endif()

elseif(IS_LINUX)
    # Linux configuration - use pkg-config
    find_package(PkgConfig)
    if(PkgConfig_FOUND)
        pkg_check_modules(SOX sox)
        if(SOX_FOUND)
            target_include_directories(_sox PRIVATE ${SOX_INCLUDE_DIRS})
            target_link_directories(_sox PRIVATE ${SOX_LIBRARY_DIRS})
            target_link_libraries(_sox PRIVATE ${SOX_LIBRARIES})
        endif()
    endif()

    if(NOT SOX_FOUND)
        # Fallback if pkg-config fails
        target_include_directories(_sox PRIVATE
            /usr/include
            /usr/local/include
        )
        target_link_directories(_sox PRIVATE
            /usr/lib
            /usr/local/lib
            /usr/lib/x86_64-linux-gnu
            /usr/lib/aarch64-linux-gnu
        )
        target_link_libraries(_sox PRIVATE
            sox sndfile FLAC opus mp3lame
            vorbis vorbisfile vorbisenc png z
        )
    endif()

    if(DEBUG)
        target_compile_options(_sox PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(_sox PRIVATE -fsanitize=address)
    endif()

elseif(IS_WINDOWS)
    # Windows configuration
    if(DEFINED ENV{SOX_INCLUDE_DIR})
        target_include_directories(_sox PRIVATE $ENV{SOX_INCLUDE_DIR})
    endif()
    if(DEFINED ENV{SOX_LIB_DIR})
        target_link_directories(_sox PRIVATE $ENV{SOX_LIB_DIR})
    endif()
    target_link_libraries(_sox PRIVATE sox)
endif()

# Install the extension module
install(TARGETS _sox DESTINATION cysox)
