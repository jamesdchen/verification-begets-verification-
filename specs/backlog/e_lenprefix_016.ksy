meta:
  id: e_lenprefix_016
  endian: le
seq:
  - id: f0
    type: u4
  - id: f1
    type: u1
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
