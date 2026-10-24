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

# Generate onset.c from onset.pyx using Cython
add_custom_command(
    OUTPUT onset.c
    COMMAND Python::Interpreter -m cython
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/onset.pyx"
        --output-file onset.c
    DEPENDS
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/onset.pyx"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/cysox/kissfft.pxd"
    COMMENT "Generating onset.c from onset.pyx"
)

# Create the extension module (named _sox internally to avoid conflict with libsox)
python_add_library(_sox MODULE sox.c WITH_SOABI)

# Build KissFFT as a static library (used by onset module for O(n log n) FFT)
add_library(kissfft STATIC
    "${CMAKE_CURRENT_SOURCE_DIR}/vendor/kissfft/kiss_fft.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/vendor/kissfft/kiss_fftr.c"
)
target_include_directories(kissfft PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/vendor/kissfft")
# Use double precision to match onset.pyx's double buffers
target_compile_definitions(kissfft PUBLIC kiss_fft_scalar=double)
set_target_properties(kissfft PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Create the onset module (uses KissFFT for spectral analysis)
python_add_library(onset MODULE onset.c WITH_SOABI)
target_include_directories(onset PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/vendor/kissfft")
target_compile_definitions(onset PRIVATE kiss_fft_scalar=double)
target_link_libraries(onset PRIVATE kissfft)

# Set the output name to "sox" (the actual module name users import)
set_target_properties(_sox PROPERTIES OUTPUT_NAME "sox")

# Include directories
target_include_directories(_sox PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")

# Platform-specific configuration
if(IS_MACOS OR IS_LINUX)
    # scripts/build-libsox.sh installs a static libsox and its sox.pc into
    # lib/. Prefer it over a system libsox. It is static-only, so it needs the
    # Libs.private flags.
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/lib/pkgconfig/sox.pc")
        set(ENV{PKG_CONFIG_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/lib/pkgconfig:$ENV{PKG_CONFIG_PATH}")
        set(STATIC ON)
    endif()

    set(SOX_FOUND FALSE)
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(SOX QUIET sox)
    endif()

    if(SOX_FOUND AND STATIC)
        message(STATUS "Linking libsox statically via pkg-config: ${SOX_STATIC_LDFLAGS}")
        target_include_directories(_sox PRIVATE ${SOX_STATIC_INCLUDE_DIRS})
        target_link_libraries(_sox PRIVATE ${SOX_STATIC_LDFLAGS})
    elseif(SOX_FOUND)
        message(STATUS "Found sox via pkg-config")
        target_include_directories(_sox PRIVATE ${SOX_INCLUDE_DIRS})
        target_link_directories(_sox PRIVATE ${SOX_LIBRARY_DIRS})
        target_link_libraries(_sox PRIVATE ${SOX_LIBRARIES})
    elseif(IS_LINUX)
        # Fallback: use find_path and find_library
        message(STATUS "pkg-config failed, using fallback method")

        find_path(SOX_INCLUDE_DIR sox.h
            PATHS /usr/include /usr/local/include
            NO_DEFAULT_PATH
        )
        if(NOT SOX_INCLUDE_DIR)
            find_path(SOX_INCLUDE_DIR sox.h)
        endif()

        find_library(SOX_LIBRARY NAMES sox
            PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu
            NO_DEFAULT_PATH
        )
        if(NOT SOX_LIBRARY)
            find_library(SOX_LIBRARY NAMES sox)
        endif()

        if(SOX_INCLUDE_DIR AND SOX_LIBRARY)
            message(STATUS "Found sox: ${SOX_LIBRARY}")
            message(STATUS "Found sox.h: ${SOX_INCLUDE_DIR}")
            target_include_directories(_sox PRIVATE ${SOX_INCLUDE_DIR})
            target_link_libraries(_sox PRIVATE ${SOX_LIBRARY})
        else()
            message(FATAL_ERROR "Could not find libsox. Please install libsox-dev.")
        endif()
    else()
        message(FATAL_ERROR "Could not find libsox. Run scripts/setup.sh.")
    endif()

    if(DEBUG)
        target_compile_options(_sox PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(_sox PRIVATE -fsanitize=address)
        if(IS_MACOS)
            target_compile_definitions(_sox PRIVATE DEBUG DEBUG_EFFECTS_CHAIN=1)
        endif()
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

# Install the extension modules
install(TARGETS _sox onset DESTINATION cysox)
