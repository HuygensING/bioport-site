#!/bin/bash
# Adjust compiler.jar location according to your needs
COMPILER_PATH=/home/silvio/dojo-build/dojo-release-1.4.1-src/util/buildscripts/

java -jar $COMPILER_PATH/compiler.jar \
    --js_output_file lib-compiled.js\
    --js jquery.ready.js\
    --js jquery.flydom-3.1.1.js\
    --js autocomplete/jquery.ajaxQueue.js\
    --js autocomplete/jquery.bgiframe.min.js\
    --js autocomplete/jquery.dimensions.js\
    --compilation_level WHITESPACE_ONLY
#    --js autocomplete/thickbox-compressed.js\
