class Plumbum::Actions is HLL::Actions;

method TOP($/) {
    make PAST::Block.new( $<statementlist>.ast , :hll<plumbum>, :node($/) );
}

method statementlist($/) {
    my $past := PAST::Stmts.new( :node($/) );
    for $<statement> { $past.push( $_.ast ); }
    make $past;
}

method statement($/) {
	make ($<assignment> // $<p_expr>).ast;
}

method assignment($/){
	my $lhs := $<identifier>.ast;
	my $rhs := $<p_expr>.ast;
	$lhs.lvalue(1);
	make PAST::Op.new( $lhs, $rhs, :pasttype('bind'), :node($/));
}

method identifier($/){
	make PAST::Var.new(:name(~$/), :scope('package'), :node($/));
}

#TODO: consider rewriting as:
# p_expr = <atom> | '|' <p_expr>
#  and use the AST to accumulate things for us
method p_expr($/){
	my @pipe := ();
	for $<atom> { @pipe.unshift( $_.ast ); }
	#TODO: this causes trouble, as @pipe isn't an ast node
	make PAST::Op.new( @pipe, :node($/), :name('pipe'), :pasttype('call') );
}

method atom($/){
	make ($<slurp> // $<shell> // $<listliteral> // $<string> // $<fcall>).ast;
}

method slurp($/){ 
	my $contents := $<quote_EXPR>.ast;
	make PAST::Op.new( $contents, :pasttype('call'), :name('slurp'), :node($/));
}
method shell($/){
	my $contents := $<quote_EXPR>.ast;
	make PAST::Op.new( $contents, :pasttype('call'), :name('shell'), :node($/));
}
method listliteral($/){
	my @lst := ();
	for $<EXPR> { @lst.push( $_.ast ); }
	make PAST::Val.new(:node($/), :value(@lst));
}
method string($/){
	make $<quote>.ast;
}
method fcall($/){
	my $fn := $<identifier>.ast;
	my $past := PAST::Op.new( :pasttype('call'), :node($/), :name($fn) );
	for $<EXPR> { $past.push( $_.ast ); }
}

## terms

method term:sym<lhs>($/) { make $<lhs>.ast; }
method term:sym<integer>($/) {
	make PAST::Val.new(:value($<integer>.ast), :returns<Integer>);
}
method term:sym<quote>($/) {
	my $past := $<quote>.ast;
	$past.returns('String');
	make $past;
}

method quote:sym<'>($/) { make $<quote_EXPR>.ast; }
method quote:sym<">($/) { make $<quote_EXPR>.ast; }

method circumfix:sym<( )>($/) { make $<EXPR>.ast; }

