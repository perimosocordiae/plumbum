class Plumbum::Compiler is HLL::Compiler;

INIT {
    Plumbum::Compiler.language('Plumbum');
    Plumbum::Compiler.parsegrammar(Plumbum::Grammar);
    Plumbum::Compiler.parseactions(Plumbum::Actions);
}
