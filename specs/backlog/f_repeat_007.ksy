meta:
  id: f_repeat_007
  endian: be
seq:
  - id: f0
    type: u1
  - id: f1
    type: u1
  - id: items
    type: u2
    repeat: expr
    repeat-expr: 3
