meta:
  id: e_lenprefix_001
  endian: be
seq:
  - id: f0
    type: u1
  - id: f1
    type: u4
  - id: len_data
    type: u1
  - id: data
    type: str
    size: len_data
    encoding: ASCII
