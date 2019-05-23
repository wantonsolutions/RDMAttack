#!/bin/bash
godir="go/src/github.com/wantonsolutions/RDMAttack/src"

go build
scp ./* ssgrant@b09-05:~/$godir
