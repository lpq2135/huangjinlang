#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "OpenCC::OpenCC" for configuration "Release"
set_property(TARGET OpenCC::OpenCC APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(OpenCC::OpenCC PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "D:/a/OpenCC/OpenCC/build/lib.win-amd64-cpython-311/opencc/clib/lib/opencc.lib"
  )

list(APPEND _cmake_import_check_targets OpenCC::OpenCC )
list(APPEND _cmake_import_check_files_for_OpenCC::OpenCC "D:/a/OpenCC/OpenCC/build/lib.win-amd64-cpython-311/opencc/clib/lib/opencc.lib" )

# Import target "OpenCC::marisa" for configuration "Release"
set_property(TARGET OpenCC::marisa APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(OpenCC::marisa PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "D:/a/OpenCC/OpenCC/build/lib.win-amd64-cpython-311/opencc/clib/lib/marisa.lib"
  )

list(APPEND _cmake_import_check_targets OpenCC::marisa )
list(APPEND _cmake_import_check_files_for_OpenCC::marisa "D:/a/OpenCC/OpenCC/build/lib.win-amd64-cpython-311/opencc/clib/lib/marisa.lib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
