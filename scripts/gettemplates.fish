gh repo list DB-Student-Repos -L 10000 --json name --json isTemplate | jq -r '.[] | select (.isTemplate == true) | .name' >templates
