meta:
  id: f_repeat_024
  endian: be
seq:
  - id: f0
    type: u4
  - id: f1
    type: u1
  - id: items
    type: u1
    repeat: expr
    repeat-expr: 6
