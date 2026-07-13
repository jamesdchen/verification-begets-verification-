meta:
  id: e_lenprefix_008
  endian: le
seq:
  - id: f0
    type: u1
  - id: f1
    type: u8
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
