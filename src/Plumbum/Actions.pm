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
	#my $stmt := $<assignment> ?? $<assignment> !! $<p_expr>;
	#make $stmt.ast;
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

method p_expr($/){
	my $past := PAST::Op.new( :node($/), :name('pipe'), :pasttype('call') );
	for $<atom> { $past.unshift( $_.ast ); }
	make $past;
}

method atom($/){
	make ($<slurp> // $<shell> // $<fcall>).ast;
}

#TODO: all these three
method slurp($/){ }
method shell($/){ }
method fcall($/){ }

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

