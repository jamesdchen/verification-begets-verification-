"""Incumbent, hand-written, black-box order-lifecycle service.

This is *untrusted third-party code* -- someone's existing stateful service.
The protocol-lift loop (buildloop.lstar) treats it strictly as a black box:
it may only construct it (which resets it to a fresh state) and call
``call(tool, args)``; it never reads the source's control flow.  All state
lives in instance attributes -- there are NO module globals and NO files, so
constructing a fresh ``Incumbent`` is a total reset, which is exactly what the
membership oracle relies on to make each query independent.

Frozen incumbent interface (shared by P2/P3):

    class Incumbent:
        def __init__(self): ...                 # reset to a fresh state
        def call(self, tool: str, args: dict) -> jsonable: ...

Observable contract (the thing L* is meant to recover):

    normal lifecycle   init --login--> authed --pay(>=100)--> paid
                       --ship--> shipped --close--> closed

    * login succeeds only from ``init``;
    * pay succeeds only from ``authed`` and only when amount >= 100
      (a small payment is always refused -- this is the arg abstraction the
      learner declares: pay_big vs pay_small);
    * ship succeeds only from ``paid``; close only from ``shipped``;
    * every other (state, tool) pair is refused with "reject" and leaves the
      state unchanged.

Hidden trapdoor (the honesty tooth): there is a state ``void`` that is NOT on
the advertised lifecycle and is reachable ONLY by the long sequence

    login, pay(>=100), ship, close, refund, refund

i.e. two refunds *after* a fully-closed order.  In ``void`` the service is
degenerate -- it accepts EVERY tool with "ok" (a latent god-mode / audit
bypass).  Because ``void`` sits six transitions deep and is Myhill-Nerode
distinguishable from ``closed`` only by a length>=2 suffix, a learner whose
equivalence oracle explores too shallow a depth (small state bound n) will
collapse ``closed``, ``refund_pending`` and ``void`` into one state and MISS
it entirely; only a deeper bound reaches it.
"""


class Incumbent:
    # amount at or above which a payment is honoured
    PAY_THRESHOLD = 100

    def __init__(self):
        # ALL state is here; a fresh instance is a clean reset.
        self.state = "init"

    def call(self, tool, args):
        args = args or {}
        st = self.state

        # --- the degenerate hidden state: accepts anything -----------------
        if st == "void":
            return "ok"

        if tool == "login":
            if st == "init":
                self.state = "authed"
                return "ok"
            return "reject"

        if tool == "pay":
            amount = args.get("amount", 0)
            if st == "authed" and isinstance(amount, int) \
                    and amount >= self.PAY_THRESHOLD:
                self.state = "paid"
                return "ok"
            return "reject"

        if tool == "ship":
            if st == "paid":
                self.state = "shipped"
                return "ok"
            return "reject"

        if tool == "close":
            if st == "shipped":
                self.state = "closed"
                return "ok"
            return "reject"

        if tool == "refund":
            # A single refund on a closed order opens a refund window; a
            # SECOND refund in that window trips the latent void state.
            if st == "closed":
                self.state = "refund_pending"
                return "ok"
            if st == "refund_pending":
                self.state = "void"
                return "ok"
            return "reject"

        # unknown tool -> the driver would normally map an exception to
        # "__error__"; we surface it explicitly so the output alphabet is
        # well defined even off the declared abstraction.
        return "__error__"
