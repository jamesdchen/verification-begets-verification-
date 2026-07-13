meta:
  id: f_repeat_006
  endian: le
seq:
  - id: f0
    type: u1
  - id: f1
    type: u8
  - id: items
    type: u4
    repeat: expr
    repeat-expr: 2
