meta:
  id: f_repeat_020
  endian: be
seq:
  - id: f0
    type: u4
  - id: f1
    type: u8
  - id: items
    type: u8
    repeat: expr
    repeat-expr: 4
