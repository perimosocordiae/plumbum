#!/usr/bin/env runhaskell

-- WARNING: this does not do much other than some limited parsing
--          the Python version is what actually works

import Text.ParserCombinators.Parsec
import Data.String.Utils

data Program = Program {stmts :: [Expression], 
                        symtab :: [(String,Expression)]}
    deriving Show

type Expression = [Atom]

data Atom = LiteralAtom [String] | Identifier String
            | SlurpAtom String   | ShellAtom String
    deriving Show

-- MAIN

main = do 
    stdin <- getContents
    mapM_ run (stripLines stdin)

stripLines = (map (strip . (takeWhile (/='#')))) . lines

run line = case parse expr "(stdin)" line of
            Left err -> putStr "Error: " >> print err
            Right ast -> (putStrLn . show . evaluate) ast

-- EVALUATION

evaluate :: Expression -> [String]
evaluate = foldl eval []

eval :: [String] -> Atom -> [String] --TODO (get other types, too)
eval [] (LiteralAtom l) = l
eval lst (Identifier i) = lst++[i] --TODO (need state monad for Program)
eval [] (SlurpAtom s) = [s] --TODO (going to be messy, using IO)
eval [] (ShellAtom s) = [s] --TODO (here too)
eval _ _ = error "Invalid pipe"

-- PARSING

expr = atom `sepBy` pipe where
    pipe = spaces >> (char '|') >> spaces

atom = listLiteral <|> identifier <|> slurpLiteral <|> shellLiteral <?> "atom"

listLiteral = do
    s <- quoted '[' ']'
    return $ LiteralAtom $ map strip (split "," s)

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
