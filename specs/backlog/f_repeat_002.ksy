meta:
  id: f_repeat_002
  endian: be
seq:
  - id: f0
    type: u8
  - id: num_items
    type: u2
  - id: items
    type: u1
    repeat: expr
    repeat-expr: num_items
