for REP in (gh repo list 23W-INCO --json name | jq -r ".[]|.name")
    gh repo sync 23W-INCO/$REP
end
