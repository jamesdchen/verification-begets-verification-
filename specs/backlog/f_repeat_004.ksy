meta:
  id: f_repeat_004
  endian: be
seq:
  - id: f0
    type: u4
  - id: num_items
    type: u2
  - id: items
    type: u4
    repeat: expr
    repeat-expr: num_items
