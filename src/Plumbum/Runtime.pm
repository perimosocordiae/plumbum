# language-specific runtime functions go here

sub pipe(*@args) {
    pir::say(pir::join('', @args));
    1;
}
