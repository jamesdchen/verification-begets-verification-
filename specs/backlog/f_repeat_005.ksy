meta:
  id: f_repeat_005
  endian: le
seq:
  - id: f0
    type: u2
  - id: num_items
    type: u1
  - id: items
    type: u8
    repeat: expr
    repeat-expr: num_items
