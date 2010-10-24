#!/usr/bin/env runhaskell

-- WARNING: this does not do much other than some limited parsing
--          the Python version is what actually works

import Text.ParserCombinators.Parsec
import Data.String.Utils
import Data.List
import System.Process
import System.IO
import Control.Monad

data Program = Program {stmts :: [Expression], 
                        symtab :: [(String,Expression)]}
    deriving Show

type Expression = [Atom]

data Atom = LiteralAtom [String] | Identifier String
            | SlurpAtom String   | ShellAtom String
    deriving Show

-- MAIN

main = forever $ getLine >>= (run . stripLine) where
	stripLine = strip . (takeWhile (/='#'))
	forever a = a >> (forever a)

run line = case parse expr "(stdin)" line of
            Left err -> putStr "Error: " >> print err
            Right ast -> do
				output <- evaluate ast
				putStrLn $ show output

-- EVALUATION

evaluate :: Expression -> IO [String]
evaluate = foldM eval []

eval :: [String] -> Atom -> IO [String]
-- literally, whatever the atom holds
eval [] (LiteralAtom l) = return l

-- apply some function from the stdlib
eval lst (Identifier i) = case lookup i stdlib of
	Just fn -> return $ fn lst
	Nothing -> error $ "Invalid identifier: "++i

-- "" means <> means read from stdin
eval [] (SlurpAtom "") = do
	file <- getContents --TODO: bug, getContents closes the file
	return $ lines file

-- read from file
eval [] (SlurpAtom s) = do
	file <- readFile s
	return $ lines file

-- read from stdout of shell command
eval [] (ShellAtom s) = do
	(_,Just stdout,_,_) <- createProcess (shell s){ std_out = CreatePipe }
	file <- hGetContents stdout
	return $ lines file

-- TODO: may want to merge this back with above
eval lst (ShellAtom s) = error "Passing data to shell cmd not yet implemented"

-- catch-all for invalid args
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

-- STD LIBRARY
stdlib :: [(String, [String] -> [String])]
stdlib = [
	("inc", map (show.(+1).(read::String->Int))),
	("sort", sort),
	("head", take 10),
	("strip", map strip),
	("count", (\lst -> [show(length lst)]))
	]
