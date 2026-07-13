meta:
  id: f_repeat_021
  endian: le
seq:
  - id: f0
    type: u2
  - id: f1
    type: u4
  - id: num_items
    type: u1
  - id: items
    type: u4
    repeat: expr
    repeat-expr: num_items
