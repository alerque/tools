#!/usr/bin/env bash
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  dboerschlein
#  Jesse Griffin <jesse@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>

is_child_process || echo "Please run this using export.sh" && exit 1

help() {
    echo "    -c       Override checking level (1, 2 or 3)"
    echo "    -m MAX   Set a maximum number of chapters to be typeset"
    echo "    -t TAG   Add a tag to the output filename"
    echo "    -v VER   Override the version field in the output"
}

# Process command line options
while getopts c:del:m:o:r:t:v:h opt; do
    case $opt in
        c) checking=$OPTARG;;
        m) max_chapters=$OPTARG;;
        t) tag=$OPTARG;;
        v) version=$OPTARG;;
    esac
done

# Setup variable defaults in case flags were not set
: ${checking=}
: ${max_chapters=0}
: ${tag=}
: ${version=}

## PROCESS LANGUAGES AND BUILD PDFS ##


for lang in "${langs[@]}"; do
    # Get the version for this language (if not forced from an option flag)
    LANGVER=${version:-$("$BASEDIR"/uw/get_ver.py $lang)}

    # Pick a filename based on all the parts we have
    BASENAME="obs-${lang}-v${LANGVER/./_}${tag:+-$tag}"

    # Run python (export.py) to generate the .tex file from template .tex files
    ./obs/export.py -l $lang -m $max_chapters -f tex ${checking:+-c $checking} -o "$BASENAME.tex"

    # If requested, stop to manually edit the finished ConTeXt file before typesetting
    $edit && $EDITOR "$BASENAME.tex"

    # Run ConTeXt (context) to generate stories from .tex file output by python
    $DEBUG && trackers="afm.loading,fonts.missing,fonts.warnings,fonts.names,fonts.specifications,fonts.scaling,system.dump"
    context --paranoid --batchmode ${trackers:+--trackers=$trackers} "$BASENAME.tex"

    # Send to requested output location(s)
    for dir in "${outputs[@]}"; do
        install -Dm 0644 "${BASENAME}.pdf" "$(eval echo $dir)/${BASENAME}.pdf"
    done

    # This reporting bit could probably use a rewrite but since I'm not clear on what
    # the use case is I'm only fixing the file paths and letting it run as-is...
    # (originally from export_all_DBP.sh)
    if [[ -n "$REPORTS_LOCS" ]]; then
        (
            if [[ -s "$BASENAME-report.txt" ]]; then
                formatA="%-10s%-30s%s\n"
                formatD="%-10s%-10s%-10s%-10s%s\n"
                printf "$formatA" "language" "link-counts-each-matter-part  possibly-rogue-links-in-JSON-files"
                printf "$formatA" "--------" "----------------------------  --------------------------------------------------------"
            fi
            egrep 'start.*matter|goto' $BASENAME.tex |
                sed -e 's/goto/~goto~/g' |
                tr '~' '\n' |
                egrep 'matter|\.com|goto' |
                tee part |
                egrep 'matter|goto' |
                awk 'BEGIN{tag="none"}
                    {
                        if (sub("^.*start","",$0) && sub("matter.*$","",$0)) {tag = $0 }
                        if ($0 ~ goto) { count[tag]++ }
                    }
                    END { for (g in count) { printf "%s=%d\n", g, count[g]; } }' |
                sort -ru > tmp
            sed -e 's/[^ ]*https*:[^ ]*]//' part |
                tr ' ()' '\n' |
                egrep 'http|\.com' > bad
            printf "$formatD" "$lang" $(cat tmp) "$(echo $(cat bad))"
        ) > "$TOOLS_DIR/$BASENAME-report.txt" || : # Don't worry about exiting if report items failed
    fi
done

## SEND REPORTS ##

if [[ -n "$REPORTS_LOCS" ]]; then
    report_package="$TOOLS_DIR/OBS-build-report-$(date +%s)${tag:+-$tag}.zip"
    zip -9yrj "$report_package" "$TOOLS_DIR"
    for target in "${REPORTS_LOCS[@]}"; do
        if [[ -d "$target" ]]; then
            install -m 0644 "$report_package" "$target/"
        elif [[ "$target" =~ @ ]]; then
            mailx -s "OBS build report ${tag:+($tag)}" -a "$report_package" "$target" < $LOG
        fi
    done
fi
