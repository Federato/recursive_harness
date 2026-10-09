"""Which fields a rating's chosen inputs could have reached (DEVIATIONS-PLAN.md, P3 / T4).

Off unless a caller sets `Interpreter.taint = Taint()` before `run` -- every ordinary rating leaves it `None`
and pays one attribute test per node. With it on, the interpreter reports to it:

  * `hit()` -- a tainted source was read: a node already marked, a lookup on a table a carrier overrode, or a
    carrier's group LCM substituted into a product;
  * `wrote(node)` -- a value was written; the node is marked if anything tainted was read while that value was
    being computed (the dynamic extent of the write's expression), or earlier in the same rule call after a
    tainted read (control dependence: a test on a tainted value decides what the rest of the rule writes);
  * `enter_rule()` / `leave_rule()` around each rule call; a rule that read anything tainted taints the
    expression that called it.

It over-approximates on purpose: "could have reached" may include a field whose value did not change. T4 asks
the converse -- every field that DID change must be in `nodes` -- so an over-approximation can only make T4
easier to pass for a field that also changed for a reason outside the carrier's inputs, never hide a change
with no tainted input at all.
"""
from __future__ import annotations


class Taint:
    def __init__(self):
        self.nodes: set[int] = set()
        self.stack: list[bool] = [False]
        self.rules: list[bool] = [False]
        self.sources = 0

    def mark(self, node) -> None:
        """An input the carrier wrote before the rules ran."""
        self.nodes.add(id(node))

    def around(self, fn, el, frame):
        self.stack.append(False)
        try:
            return fn(el, frame)
        finally:
            f = self.stack.pop()
            if f:
                self.stack[-1] = True

    def hit(self) -> None:
        self.sources += 1
        self.stack[-1] = True
        self.rules[-1] = True

    def read(self, node) -> None:
        if node is not None and id(node) in self.nodes:
            self.hit()

    def wrote(self, node) -> None:
        if self.stack[-1] or self.rules[-1]:
            self.nodes.add(id(node))
        else:
            self.nodes.discard(id(node))

    def enter_rule(self) -> None:
        self.rules.append(False)

    def leave_rule(self) -> None:
        if self.rules.pop():
            self.stack[-1] = True
