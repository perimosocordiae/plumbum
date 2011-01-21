
import Text.ParserCombinators.Parsec
import Data.String.Utils

main = do
  input <- getContents
  putStrLn $ compile $ strip $ takeWhile (/='#') input

compile src = case parse expr "(stdin)" src of
               Left err -> error $ show err
               Right ast -> toHaskell ast

preamble = unlines ["import Stdlib","main = do{"]
coda = "}"

toHaskell atoms = preamble ++ (join "\n;" hlines) ++ coda where
  hlines = reverse $ lines $ join " $ " $ map a2hs $ reverse atoms

data Atom = LiteralAtom String | Identifier String
            | SlurpAtom String | ShellAtom String
    deriving Show

a2hs :: Atom -> String
a2hs (LiteralAtom l) = "IntSeq " ++ l
a2hs (SlurpAtom s) = "slurped\nslurped <- slurp " ++ (show s)
a2hs (ShellAtom s) = "shelled\nshelled <- shellexec " ++ (show s)
a2hs (Identifier i) = i

-- PARSING

expr = atom `sepBy` pipe where
    pipe = spaces >> (char '|') >> spaces

atom = listLiteral <|> identifier <|> slurpLiteral <|> shellLiteral <?> "atom"

listLiteral = do
    s <- quoted '[' ']'
    return $ LiteralAtom $ '[' : s ++ "]"

quoted open close = do
    (char open)
    s <- manyTill anyChar (char close)
    return s

slurpLiteral = do
    s <- quoted '<' '>'
    return $ SlurpAtom s

shellLiteral = do
    s <- quoted '`' '`'
    return $ ShellAtom s

identifier = do
    s <- many1 letter
    return $ Identifier s
