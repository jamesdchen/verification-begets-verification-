meta:
  id: e_lenprefix_010
  endian: be
seq:
  - id: f0
    type: u1
  - id: f1
    type: u1
  - id: len_data
    type: u2
  - id: data
    type: str
    size: len_data
    encoding: ASCII
