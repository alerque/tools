cat /tmp/OBS-${lang}*tex \
		| egrep 'start.*matter|goto' \
		| sed -e 's/goto/~goto~/g' \
		| tr '~' '\n' \
		| egrep 'matter|goto' \
		| awk 'BEGIN{tag="none"}
			{
				if (sub("^.*start","",$0) && sub("matter.*$","",$0)) {tag = $0 }
				if ($0 ~ goto) { count[tag]++ }
			}
			END { for (g in count) { printf "%s=%d\n", g, count[g]; } }' \
		| sort -ru \
		> /tmp/$$.tmp
echo $lang $(cat /tmp/$$.tmp)
