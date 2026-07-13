meta:
  id: f_repeat_011
  endian: be
seq:
  - id: num_items
    type: u2
  - id: items
    type: u2
    repeat: expr
    repeat-expr: num_items
