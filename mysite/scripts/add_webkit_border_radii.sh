find -name "*.css" -print0 | xargs -0 sed -i -e '/.*webkit.*/!s/-moz-b\([^;]*\);/-webkit-b\1; \0/g' -e 's/-webkit-border-radius-\(top\|bottom\)\(left\|right\)/-webkit-border-\1-\2-radius/g'
