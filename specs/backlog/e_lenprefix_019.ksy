meta:
  id: e_lenprefix_019
  endian: le
seq:
  - id: f0
    type: u1
  - id: f1
    type: u2
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
