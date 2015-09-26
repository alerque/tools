#!/usr/bin/env bash
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
# Caleb Maclennan <caleb@alerque.com>
#
# > “One Ring to bring them all and in the darkness bind them…”
#
# Except we're working with light here, so that doesn't quite work. The idea is
# for this script to eventually obsolete all the piecemeal ones for exporting
# various resources in various formats and help avoid code duplication by
# handling arguments and setting up the various build environments.

# If anything at all throws an error and this script doesn't otherwise catch
# and handle it correctly that is a bug in this script and should be fixed.
set -e

# Usage instructions
help() {
	cat <<-END_OF_HELP
	Usage: $0 -r <resource> -f <format> -l <language> [optional_options]
	Required options:
	    -r <resource> Name of resource to export, e.g. \`-r obs\`
	    -f <format>   Output format, e.g. \`-f pdf\`
	    -l <language> Language to export, e.g. \`-l en\`
	Optional options:
        -o <dir>      Add output location for final exported format
	                	(defaults to current directory)
        -r <location> Send build report to an email address or directory
	                	(defaults to none)
	Debuging options:
	    -e            Stop to edit data files durring run using \$EDITOR
		-t            Specifiy the directory for temporary files
        -d            Show debug messages while running script
        -h            Show this help
	Notes:
	    All options that accept arguments may be specified more than once.
	END_OF_HELP
}

# Process command line options
while getopts r:f:l:o:r:hdet: opt; do
	case $opt in
        r) resources=("${resources[@]}" "$OPTARG") ;;
        f) formats=("${formats[@]}" "$OPTARG") ;;
        l) languages=("${languages[@]}" "$OPTARG") ;;
		o) OUTPUT_DIRS=$OPTARG ;;
		r) REPORT_LOCS=$OPTARG ;;
		t) TEMP_DIR=$OPTARG ;;
		e) EDIT=true ;;
        d) DEBUG=true ;;
		h) help && exit 0 ;;
		?) help >&2 && exit 1 ;;
	esac
done

# Setup working environment including default values for anything not specified
: ${TOOLS_DIR:=$(cd $(dirname "$0")/ && pwd)}
: ${DEBUG:=false}
: ${EDIT:=false}
: ${OUTPUT_DIRS[0]=$(pwd)}
: ${REPORT_LOCS[0]=}
# Create a temporary directory using the system default temp directory location
# in which we can stash any files we want in an isolated namespace. It is very
# important that this dir actually exist. The set -e option should always be
# used so that if the system doesn't let us create a temp directory we won't
# continue.
if [[ -z $TEMP_DIR ]]; then
    TEMP_DIR=$(mktemp -d -t "uW-export.XXXXXX")
    # If _not_ in DEBUG mode, _and_ we made our own temp directory, then
    # cleanup out temp files after every run. Running in DEBUG mode will skip
    # this so that the temp files can be inspected manually
    $DEBUG || trap 'popd > /dev/null; rm -rf "$TEMP_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $TEMP_DIR ]]; then
    mkdir -p "$TEMP_DIR"
fi

# Change to own own temp dir but note our current dir so we can get back to it
pushd $TEMP_DIR > /dev/null

: ${LOG_FILE:=$TEMP_DIR/export.log}

# Import common shell functions from our library
source $TOOLS_DIR/lib/shell_functions.sh

# Check for a minimum amount of information from arguments to continue
test ${#resources[@]} -ge 1 ||
	usage_error "At least one resource must be specified"
test ${#languages[@]} -ge 1 ||
	usage_error "At least one language must be specified"
test ${#formats[@]} -ge 1 ||
	usage_error "At least one output format must be specified"

# Main logic
start_logging

# Loop through all the work we have to do
for resource in "${resources[@]}"; do
	for language in "${languages[@]}"; do
		for format in "${formats[@]}"; do
			case $format in
				pdf)
					source $TOOLS_DIR/lib/tex_functions.sh
					case $resource in
						obs)
							setup_context
							check_tex_font_cache notosans
							check_tex_font_cache notonaskharabic
							check_tex_font_cache abyssicicasil
							;;
						*)
							fail "Unknown resource $resource"
					esac
					;;
				*)
					fail "Unknown format $format"
					;;
			esac
		done
	done
done
