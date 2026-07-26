# round 2 consumption receipt

`p7-parallel-tower-r2` (the `evalTmN` case) rode the lane and returned:

    candidates=1  passed=1  failed=0  not-run=0
    [PASSED] p7-parallel-tower-r2
      declares=evalTmP_powp, evalTmNP_powp, substTmP_powp
      gate_ok, elaborated, replayed (lean4checker), no sorryAx

Two of the five walker cases the class measurement names are now prototyped
and machine-checked over the parallel tower: `evalTm` + `substTm` (r1) and
`evalTmN` (r2).  Still unmet: `substTm_evalTm`, `check`.

The prototype remains a PROPOSAL.  `tools/FgReflect.lean` is untouched, and
adopting `TmP` is an attended purchase decision under the ordinary bill
discipline -- "it elaborated in the batch ride" is a reason to keep
authoring and never a done-predicate.
