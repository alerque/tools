#!/usr/bin/env bash
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
# Caleb Maclennan <caleb@alerque.com>

function fail() {
	echo "Error: $@"
	exit 1
}

function usage_error() {
	echo "Usage error: $@"
	help
	exit 1
}

function start_logging() {
	# If running in DEBUG mode, output information about every command run
	$DEBUG && set -x

    # If a reporting location is specified, capture and log out own stdout
	[[ -n "$REPORTS_LOCS" ]] && exec 2>&1 > $LOG_FILE
}

function is_child_process() {
	true
}
