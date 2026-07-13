meta:
  id: f_repeat_019
  endian: le
seq:
  - id: f0
    type: u1
  - id: f1
    type: u8
  - id: num_items
    type: u1
  - id: items
    type: u1
    repeat: expr
    repeat-expr: num_items
