meta:
  id: f_repeat_010
  endian: be
seq:
  - id: num_items
    type: u1
  - id: items
    type: u2
    repeat: expr
    repeat-expr: num_items
