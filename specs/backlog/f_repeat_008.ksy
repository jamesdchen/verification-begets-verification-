meta:
  id: f_repeat_008
  endian: le
seq:
  - id: f0
    type: u8
  - id: items
    type: u1
    repeat: expr
    repeat-expr: 8
