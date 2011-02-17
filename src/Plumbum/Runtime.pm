# language-specific runtime functions go here

sub pipe(*@args) {
	#pir::say(pir::join('', @args));
	for @args { pir::say("pipe: $_"); }
    1;
}

sub slurp($fname) {
	pir::say("Slurping: $fname"); 1;
}

sub shell($cmd) {
	pir::say("Shell exec'ing: $cmd"); 1;
}
