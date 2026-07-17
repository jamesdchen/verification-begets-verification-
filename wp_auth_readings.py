"""WP-AUTH: session-inline MathReadings for the 11 promoted sources (41-51),
the 51-source authoring continuation.  Mirrors the flagship authoring reference
(scratchpad/inline_readings.py) helper-builder style EXACTLY: one reading per
source, authored by the orchestrating session (UNMETERED -- cost columns VOID),
reused identically by both arms (the F5.2 same-inputs discipline).

Quotes are LITERAL source substrings (the groundedness gate; parse_math_reading
checks every demand/presupposition quote occurs verbatim, whitespace/case
normalized, and every choice quotes nothing).

The four EXISTENTIAL sources (41-44) carry GENUINE ``binder:"exists"`` quantifier
statements and certify (or honestly refuse) via the merged bounded-shadow ∃
channel (math_eval.exists_shadow_shape / exists_instances).  Their compiled
binder prefix is ``∀* ∃*`` (all forall quantifier statements sort BEFORE the
exists ones by id: "qf" < "qx"); hypotheses reference OUTER objects only.

Bound-edge behavior at B=8, authored HONESTLY (never distort the reading to
force a green):
  * 41  a=bq+r, 0<=r<b : q,r stay in [-8,8] for in-box a,b>0  -> CERTIFIES.
  * 42  ax+by=gcd(a,b) : reduced Bezout coeffs |x|,|y|<=4      -> CERTIFIES.
  * 43  n<m            : at n=B=8 NO in-box m>8 exists         -> HONEST REFUSAL
                         (the conservative bound-edge policy over-refuses a
                         truly-true UNBOUNDED statement -- the SAFE direction,
                         never a false green; §11.6).  Recorded as a refusal.
  * 44  b=a*q (a|b)    : q=b/a in [-8,8] for in-box a!=0        -> CERTIFIES.

51_goldbach is the manifest-declared non-transcribable (operator:prime, sharing
38's miss): the honest inline author declines -> None, exactly as 38/39/40."""


# -------------------------------------------------------- helper builders (mirror)
def _amb(carrier="Int"):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}

def _obj(i, name, quote, force="presupposition", typ="Int"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}

def _q(sid, objects, quote, binder="forall"):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": binder, "objects": objects}}

def _hyp(i, pred, quote, force="demand"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}

def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}

def r(name): return {"ref": name}
def lit(n): return {"lit": n}
def op(o, *args): return {"op": o, "args": list(args)}

def dvd(a, b): return op("dvd", a, b)
def eq(a, b): return op("=", a, b)
def ne(a, b): return op("!=", a, b)
def le(a, b): return op("<=", a, b)
def lt(a, b): return op("<", a, b)
def add(a, b): return op("+", a, b)
def mul(a, b): return op("*", a, b)
def sub(a, b): return op("-", a, b)
def mod(a, b): return op("mod", a, b)
def even(a): return op("even", a)
def AND(a, b): return op("and", a, b)

a, b, c, d, g, m, n, q, x, y = (r("a"), r("b"), r("c"), r("d"), r("g"),
                                r("m"), r("n"), r("q"), r("x"), r("y"))
rr = r("r")

READINGS = {}

# ============================================================ existential (41-44)
# 41: DIVISION ALGORITHM.  ∀ a,b (b>0) ∃ q,r : a = b*q + r  ∧  0<=r  ∧  r<b.
# Every in-box outer world has an in-box witness (q=a div b, r=a mod b), so the
# bounded shadow genuinely holds -> CERTIFIES.
READINGS["41_division_algorithm"] = {"theorem": "division_algorithm",
                                     "statements": [
    _amb("Int"),
    _obj("oa", "a", "a and b are integers"),
    _obj("ob", "b", "a and b are integers"),
    _obj("oq", "q", "integers q and r"),
    _obj("orr", "r", "integers q and r"),
    _q("qf", ["a", "b"], "a and b are integers", binder="forall"),
    _hyp("h1", lt(lit(0), b), "b greater than 0", force="presupposition"),
    _q("qx", ["q", "r"], "There exist integers q and r", binder="exists"),
    _con(AND(AND(eq(a, add(mul(b, q), rr)), le(lit(0), rr)), lt(rr, b)),
         "a equals b times q plus r and 0 is less than or equal to r and r "
         "is less than b")]}

# 42: BEZOUT IDENTITY.  ∀ a,b ∃ x,y : a*x + b*y = gcd(a,b).  The reduced Bezout
# coefficients stay in-box (|x|<=|b|/2, |y|<=|a|/2) -> CERTIFIES.
READINGS["42_bezout_identity"] = {"theorem": "bezout_identity",
                                  "statements": [
    _amb("Int"),
    _obj("oa", "a", "a and b are integers"),
    _obj("ob", "b", "a and b are integers"),
    _obj("ox", "x", "integers x and y"),
    _obj("oy", "y", "integers x and y"),
    _q("qf", ["a", "b"], "a and b are integers", binder="forall"),
    _q("qx", ["x", "y"], "There exist integers x and y", binder="exists"),
    _con(eq(add(mul(a, x), mul(b, y)), op("gcd", a, b)),
         "a times x plus b times y equals the greatest common divisor of a "
         "and b")]}

# 43: LARGER INTEGER EXISTS.  ∀ n ∃ m : n < m.  The natural faithful reading is
# bound-edge-REFUTING at n=B=8 (no in-box m>8): the shadow is CONSERVATIVE and
# over-refuses this truly-true UNBOUNDED statement.  Authored honestly -- an
# HONEST REFUSAL, recorded, never distorted into a green.
READINGS["43_larger_integer_exists"] = {"theorem": "larger_integer_exists",
                                        "statements": [
    _amb("Int"),
    _obj("on", "n", "every integer n", force="demand"),
    _obj("om", "m", "an integer m"),
    _q("qf", ["n"], "For every integer n", binder="forall"),
    _q("qx", ["m"], "there exists an integer m", binder="exists"),
    _con(lt(n, m), "n is less than m")]}

# 44: DIVIDES WITNESS.  ∀ a,b (a!=0, a|b) ∃ q : b = a*q.  q=b/a in [-8,8] for
# in-box a!=0 dividing b -> CERTIFIES.
READINGS["44_divides_witness"] = {"theorem": "divides_witness",
                                  "statements": [
    _amb("Int"),
    _obj("oa", "a", "a and b are integers"),
    _obj("ob", "b", "a and b are integers"),
    _obj("oq", "q", "an integer q"),
    _q("qf", ["a", "b"], "a and b are integers", binder="forall"),
    _hyp("h1", ne(a, lit(0)), "a not equal to 0", force="presupposition"),
    _hyp("h2", dvd(a, b), "a divides b"),
    _q("qx", ["q"], "there exists an integer q", binder="exists"),
    _con(eq(b, mul(a, q)), "b equals a times q")]}

# ============================================================ forall path (45-50)
READINGS["45_cong_transitive"] = {"theorem": "cong_transitive", "statements": [
    _amb("Int"),
    _obj("om", "m", "m is a positive integer"),
    _obj("oa", "a", "a is congruent"),
    _obj("ob", "b", "congruent to b modulo m"),
    _obj("oc", "c", "congruent to c modulo m"),
    _q("q", ["m", "a", "b", "c"], "a is congruent to b modulo m"),
    _hyp("h0", lt(lit(0), m), "positive integer", force="presupposition"),
    _hyp("h1", eq(mod(a, m), mod(b, m)), "a is congruent to b modulo m"),
    _hyp("h2", eq(mod(b, m), mod(c, m)), "b is congruent to c modulo m"),
    _con(eq(mod(a, m), mod(c, m)), "a is congruent to c modulo m")]}

READINGS["46_cong_add_const"] = {"theorem": "cong_add_const", "statements": [
    _amb("Int"),
    _obj("om", "m", "m is a positive integer"),
    _obj("oa", "a", "a is congruent"),
    _obj("ob", "b", "congruent to b modulo m"),
    _obj("oc", "c", "a plus c"),
    _q("q", ["m", "a", "b", "c"], "a is congruent to b modulo m"),
    _hyp("h0", lt(lit(0), m), "positive integer", force="presupposition"),
    _hyp("h1", eq(mod(a, m), mod(b, m)), "a is congruent to b modulo m"),
    _con(eq(mod(add(a, c), m), mod(add(b, c), m)),
         "a plus c is congruent to b plus c modulo m")]}

READINGS["47_cong_scalar_mul"] = {"theorem": "cong_scalar_mul", "statements": [
    _amb("Int"),
    _obj("om", "m", "m is a positive integer"),
    _obj("oa", "a", "a is congruent"),
    _obj("ob", "b", "congruent to b modulo m"),
    _obj("oc", "c", "a times c"),
    _q("q", ["m", "a", "b", "c"], "a is congruent to b modulo m"),
    _hyp("h0", lt(lit(0), m), "positive integer", force="presupposition"),
    _hyp("h1", eq(mod(a, m), mod(b, m)), "a is congruent to b modulo m"),
    _con(eq(mod(mul(a, c), m), mod(mul(b, c), m)),
         "a times c is congruent to b times c modulo m")]}

READINGS["48_db_sum"] = {"theorem": "db_sum", "statements": [
    _amb("Int"),
    _obj("oa", "a", "a, b, and g are integers"),
    _obj("ob", "b", "a, b, and g are integers"),
    _obj("og", "g", "a, b, and g are integers"),
    _q("q", ["a", "b", "g"], "a, b, and g are integers"),
    _hyp("h1", dvd(g, a), "g divides both a and b"),
    _hyp("h2", dvd(g, b), "g divides both a and b"),
    _con(dvd(g, add(a, b)), "g divides the sum a plus b")]}

READINGS["49_cd_combo_diff"] = {"theorem": "cd_combo_diff", "statements": [
    _amb("Int"),
    _obj("oa", "a", "a, b, d, x, and y are integers"),
    _obj("ob", "b", "a, b, d, x, and y are integers"),
    _obj("od", "d", "a, b, d, x, and y are integers"),
    _obj("ox", "x", "a, b, d, x, and y are integers"),
    _obj("oy", "y", "a, b, d, x, and y are integers"),
    _q("q", ["a", "b", "d", "x", "y"], "a, b, d, x, and y are integers"),
    _hyp("h1", dvd(d, a), "d divides a"),
    _hyp("h2", dvd(d, b), "d divides b"),
    _con(dvd(d, sub(mul(a, x), mul(b, y))),
         "d divides the difference of a times x and b times y")]}

READINGS["50_even_times_even"] = {"theorem": "even_times_even", "statements": [
    _amb("Int"),
    _obj("oa", "a", "two even integers"),
    _obj("ob", "b", "two even integers"),
    _q("q", ["a", "b"], "two even integers"),
    _hyp("h1", even(a), "two even integers", force="presupposition"),
    _hyp("h2", even(b), "two even integers", force="presupposition"),
    _con(even(mul(a, b)), "The product of two even integers is even")]}

# 51: manifest-declared non-transcribable (operator:prime, sharing 38's miss).
READINGS["51_goldbach"] = None
