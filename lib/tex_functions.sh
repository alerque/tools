#!/usr/bin/env bash
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
# Caleb Maclennan <caleb@alerque.com>

function rebuild_tex_font_cache() {
	export OSFONTDIR="/usr/share/fonts/google-noto;/usr/share/fonts/noto-fonts/hinted;/usr/local/share/fonts;/usr/share/fonts;~/.local/share/fonts"
	mtxrun --script fonts --reload
	context --generate
}

function check_tex_font_cache() {
	mtxrun --script fonts --list --all |
		grep -q $1
}

function tex_has_font() {
	check_tex_font_cache $1 ||
		rebuild_tex_font_cache && check_tex_font_cache $1 ||
		fail "Requested font $1 not found on system"
}

function setup_context() {
	if ! command -v context >/dev/null; then
		test -d "$TOOLS_DIR/tex" || install_context
		source "$TOOLS_DIR/tex/setuptex"
	fi
	# The ConTeXt templates expect to find a few building blocks in the main
	# repo, but we're going to be working in a temp space, so once we are there
	# link back to the obs tools so these snippets can be found.
	ln -sf "$TOOLS_DIR/obs"
}

function install_context() {
	pushd $TOOLS_DIR
    sh <(curl -s -L http://minimals.contextgarden.net/setup/first-setup.sh)
	popd
}
