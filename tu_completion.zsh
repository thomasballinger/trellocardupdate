autoload compinit
compinit

function tu_completion {
    local WORDS
    IFS=$'\n' # in array below, each line is an element
    read -c -A WORDS # Reads in current line into WORDS variable
    # Reply is a global we're supposed to dump "return values" in
    reply=($(tu --get-zsh-completion $WORDS "pref:$1" "suff:$2"));
    unset IFS # I hope this resets default behavior - maybe should be
              # grabbing the original and saving it instead?
}

compctl -UK tu_completion tu
