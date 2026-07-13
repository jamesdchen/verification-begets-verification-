meta:
  id: f_repeat_022
  endian: be
seq:
  - id: f0
    type: u4
  - id: f1
    type: u1
  - id: items
    type: u4
    repeat: expr
    repeat-expr: 2
