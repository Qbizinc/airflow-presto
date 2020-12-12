#!/usr/bin/env bash -e

# Assumes 1 link.
for link in $(python -m markdown_link_extractor ../README.md)
do
    echo $link
    curl -f $link > /dev/null
done

exit $?
