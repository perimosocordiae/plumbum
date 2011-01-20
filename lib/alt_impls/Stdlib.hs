
module Stdlib (StrSeq(StrSeq),IntSeq(IntSeq),
    inc,sort,strip,Stdlib.head,
    shellexec,slurp) where

import qualified Data.String.Utils as DSU
import qualified Data.List as DL 
import System.Process
import System.IO

data StrSeq = StrSeq [String] deriving Show
data IntSeq = IntSeq [Int] deriving Show

class Pipeable ss where
  inc :: ss -> IntSeq
  sort, strip :: ss -> ss
  head :: ss -> Int -> ss

instance Pipeable StrSeq where
  inc (StrSeq s) = IntSeq $ map ((+1).(read::String->Int)) s
  sort (StrSeq s) = StrSeq $ DL.sort s
  head (StrSeq s) n = StrSeq $ take n s
  strip (StrSeq s) = StrSeq $ map DSU.strip s

instance Pipeable IntSeq where
  inc (IntSeq s) = IntSeq $ map (+1) s
  sort (IntSeq s) = IntSeq $ DL.sort s
  head (IntSeq s) n = IntSeq $ take n s
  strip (IntSeq _) = error "strip not defined for integer sequences"

-- "" means <> means read from stdin
slurp s = do 
  --TODO: bug, getContents closes the file
	file <- if s == "" then getContents else readFile s
	return $ StrSeq $ lines file

-- read from stdout of shell command
shellexec s = do
	(_,Just stdout,_,_) <- createProcess (shell s){ std_out = CreatePipe }
	file <- hGetContents stdout
	return $ StrSeq $ lines file

